from math import sin, pi
import sounddevice as sd
import numpy, re
from config import eprint

class Note:

    SAMPLERATE = 48000
    NOTES = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]

    # Note number is relative to the reference note. Eg if ref note is C2
    # and the required note is B2 then the note number is -1

    def __init__(self, name, config):
        self.config = config
        number = Note.name_to_number(name, config.refnote)
        self.freq = config.reffreq * config.refinterval ** (number / config.refdivisor)
        self.name = name
        
    def name_to_number(name, refnote):
        return Note.name_to_number_abs(name) - Note.name_to_number_abs(refnote)
    
    def name_to_number_abs(name):
        namesplit = re.findall("[A-G]#*|[0-9]", name)
        return int(namesplit[1]) * 12 + Note.NOTES.index(namesplit[0])

    def get_data(self, duration):
        duration_samples = duration*Note.SAMPLERATE
        result = []
        angfreq = self.freq*2*pi
        period = 1 / self.freq
        ang_per_sample = angfreq / Note.SAMPLERATE
        samples_per_cycle = Note.SAMPLERATE * period
        
        # Round the duration to a whole number of cycles
        duration_samples = round(round(duration_samples / samples_per_cycle) * samples_per_cycle)

        for i in range(duration_samples):
            h_count = 1
            sample_value = 0
            for h in self.config.harmonics:
                sample_value += h * sin(ang_per_sample * i * h_count) 
            result.append(sample_value)
        return result

    def play(self, duration):
        data = numpy.array(self.get_data(duration))
        sd.play(data, Note.SAMPLERATE)
        sd.wait()

    def play_buffer(buffer):
        data = numpy.array(buffer)
        sd.play(data, Note.SAMPLERATE)
        sd.wait()
