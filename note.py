from math import sin, pi
import sounddevice as sd
import re
import numpy as np
from config import eprint
from time import time

class Sinewave:
    def __init__(self, amp, freq, phase):
        self.amp = amp
        self.freq = freq
        self.phase = phase

class Note:

    SAMPLERATE = 48000
    NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    # Note number is relative to the reference note. Eg if ref note is C2
    # and the required note is B2 then the note number is -1

    def __init__(self, name, config, tuning):
        self.config = config
        number = Note.name_to_number_abs(name) - Note.name_to_number_abs(tuning.refnote)
        self.freq = tuning.reffreq * tuning.refinterval ** (number / tuning.refdivisor)
        self.angular_freq = self.freq * 2 * pi
        self.name = name
        self.harmonics = tuning.harmonics #List of amplitude of harmonics starting at fundamental
        self.phases = tuning.phases #List of phase angles in radians
 
        # Pre-computed attributes of the individual sinewaves
        self.sinewaves = []
        for phase in self.phases:
            harmonic_number = 1
            for harmonic_amplitude in self.harmonics:
                self.sinewaves.append(Sinewave(harmonic_amplitude, self.angular_freq*harmonic_number, phase))
                harmonic_number += 1


    # Get the integer absolute note number. This is now synchronized to use the same
    # scheme as MIDI numbering, which starts at C1. C is the first note in the octave
    # the first octave is 1.
        
    def name_to_number_abs(name):
        namesplit = re.findall("[A-G]#*|[0-9]", name)
        return (int(namesplit[1]) + 1) * 12 + Note.NOTES.index(namesplit[0])

    #See above    
    def name_to_number_midi(name):
        return Note.name_to_number_abs(name)

    def get_sinewave_attributes(self):
        return self.sinewaves
