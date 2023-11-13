from math import sin, pi
import sounddevice as sd
import numpy


class Note:

    SAMPLERATE = 44100

    def __init__(self, notename):
        self.freq = 440
        
    def makecycle(self):
        onecycle = []
        angfreq = self.freq*2*pi
        period = 1 / self.freq
        ang_per_sample = angfreq / Note.SAMPLERATE
        samples = int(Note.SAMPLERATE * period)

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
        print("Data is length %d" %(len(data)))
        sd.play(data, Note.SAMPLERATE)
        sd.wait()

