from math import sin, pi
import sounddevice as sd
import re
import numpy as np
from config import eprint
from time import time

class Note:

    SAMPLERATE = 48000
    NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    # Note number is relative to the reference note. Eg if ref note is C2
    # and the required note is B2 then the note number is -1

    def __init__(self, name, config, tuning):
        self.config = config
        number = Note.name_to_number_abs(name) - Note.name_to_number_abs(tuning.refnote)
        self.freq = tuning.reffreq * tuning.refinterval ** (number / tuning.refdivisor)
        self.name = name
        self.harmonics = tuning.harmonics
            
    def name_to_number_abs(name):
        namesplit = re.findall("[A-G]#*|[0-9]", name)
        return int(namesplit[1]) * 12 + Note.NOTES.index(namesplit[0])
    
    def name_to_number_midi(name):
        return Note.name_to_number_abs(name) + 12

    def get_data(self, duration, as_radians = False, trim=True):
        #eprint("Get data %s %dHz" %(self.name, self.freq))
        duration_samples = duration*Note.SAMPLERATE
        angfreq = self.freq*2*pi
        period = 1 / self.freq
        ang_per_sample = angfreq / Note.SAMPLERATE
        samples_per_cycle = Note.SAMPLERATE * period
        
        # Round the duration to a whole number of cycles
        if trim:
            duration_samples = round(round(duration_samples / samples_per_cycle) * samples_per_cycle)

        result = np.zeros(duration_samples, dtype='float32')

        if (as_radians):
            for i in range(duration_samples):
                result.append((ang_per_sample *i)%(2*pi))

        else:

            for h in self.harmonics:
                h_count = 1
                if h == 0:
                    continue
                if self.config.lowpass:
                    # Skip any harmonics that would exceed the Nyquist limit
                    if self.freq * h_count > self.config.sample_rate / 2:
                        break

                harmonic_rads_per_sample = ang_per_sample * h_count
                final_angle = harmonic_rads_per_sample * duration_samples
                these_harmonics_angles = np.linspace(0, final_angle, duration_samples)
                these_harmonics_values = h * np.sin(these_harmonics_angles)
                result = np.add(result, these_harmonics_values)

                h_count += 1
        return result

    def pre_prepare(self, duration, trim=True):
        self.wavetable = self.get_data(duration, False, trim)

    def get_prepared_data(self):
        return self.wavetable

    def play(self, duration):
        data = self.get_data(duration)
        sd.play(data, self.config.sample_rate)
        sd.wait()

    def play_buffer(buffer, config):
        data = np.array(buffer)
        sd.play(data, config.sample_rate)
        sd.wait()
