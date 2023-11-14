from math import sin, pi
import sounddevice as sd
import numpy, re
from config import eprint

class Note:

    SAMPLERATE = 44100
    NOTES = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]

    # Note number is relative to the reference note. Eg if ref note is C2
    # and the required note is B2 then the note number is -1

    def __init__(self, name, config):
        self.config = config
        number = Note.name_to_number(name, config.refnote)
        self.freq = config.reffreq * config.refinterval ** (number / config.refdivisor)
        self.name = name
        self.makecycle()
        
    def name_to_number(name, refnote):
        return Note.name_to_number_abs(name) - Note.name_to_number_abs(refnote)
    
    def name_to_number_abs(name):
        namesplit = re.findall("[A-G]#*|[0-9]", name)
        return int(namesplit[1]) * 12 + Note.NOTES.index(namesplit[0])

    def makecycle(self):
        onecycle = []
        angfreq = self.freq*2*pi
        period = 1 / self.freq
        ang_per_sample = angfreq / Note.SAMPLERATE
        samples = int(Note.SAMPLERATE * period)
        eprint("%s %d Hz" %(self.name, self.freq))

        for i in range(samples):
            onecycle.append(sin(ang_per_sample * i) + .5*sin(ang_per_sample * i * 3)+ .3*sin(ang_per_sample *i * 5))
        self.onecycle = onecycle

    def get_data(self, duration):
        duration_samples = duration*Note.SAMPLERATE
        result = []
        while len(result) < duration_samples:
            result+=self.onecycle
        return result

    def play(self, duration):
        data = numpy.array(self.get_data(duration))
        #eprint("Data is length %d" %(len(data)))
        sd.play(data, Note.SAMPLERATE)
        sd.wait()

