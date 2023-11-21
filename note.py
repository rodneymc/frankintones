from math import sin, pi
import sounddevice as sd
import numpy, re
from config import eprint

class Note:

    SAMPLERATE = 48000
    NOTES = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]

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

    def get_data(self, duration, as_radians = False):
        duration_samples = duration*Note.SAMPLERATE
        result = []
        angfreq = self.freq*2*pi
        period = 1 / self.freq
        ang_per_sample = angfreq / Note.SAMPLERATE
        samples_per_cycle = Note.SAMPLERATE * period
        
        # Round the duration to a whole number of cycles
        duration_samples = round(round(duration_samples / samples_per_cycle) * samples_per_cycle)

        if (as_radians):
            for i in range(duration_samples):
                result.append((ang_per_sample *i)%(2*pi))

        else:
            for i in range(duration_samples):
                h_count = 1
                sample_value = 0
                for h in self.harmonics:
                    if self.config.lowpass:
                        # Skip any harmonics that would exceed the Nyquist limit
                        if self.freq * h_count > self.config.sample_rate / 2:
                            break

                    sample_value += h * sin(ang_per_sample * i * h_count) 
                result.append(sample_value)
        return result

    def play(self, duration):
        data = numpy.array(self.get_data(duration))
        sd.play(data, self.config.sample_rate)
        sd.wait()

    def play_buffer(buffer, config):
        data = numpy.array(buffer)
        sd.play(data, config.sample_rate)
        sd.wait()
