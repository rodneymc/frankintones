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
        self.harmonics = tuning.harmonics
        self.phases = tuning.phases #List of phase angles in radians
        self.wavetable = None    #Pre-prepared long-duration of tone
 
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

    # Generates wavetable data for a given duration
    # Inputs:
    #  duration - Length of wavetable in seconds
    #  trim - whether to adjust the length to an exact number of samples
    #         see also comments in the code around if trim:
    #  phase - phase offset in radians. If None, then all the phases
    #          listed in self.phases will be superimposed.
    def get_data(self, duration, trim=True, phase=None):

        # Interprete phase==None as all the phases
        if phase == None:
            phases = self.phases
        else:
            # A sepcific phase was requested
            phases = [phase]

        #eprint("Get data %s %dHz" %(self.name, self.freq))
        duration_samples = duration*Note.SAMPLERATE
        angfreq = self.freq*2*pi
        period = 1 / self.freq
        ang_per_sample = angfreq / Note.SAMPLERATE
        samples_per_cycle = Note.SAMPLERATE * period
        
        # Round the duration to a whole number of cycles. This reduces repition noise, ie
        # a pop or click when the wavetable loops round. However it has two problems,
        # 1) for a wavetable containing combined phases there is no common zero-crossover point
        # to round to
        # 2) Different note's wavetables will be trimmed to different lengths. 
        if trim:
            duration_samples_pretrim = duration_samples
            duration_samples = round(round(duration_samples / samples_per_cycle) * samples_per_cycle)
            # Note that there is still an error. For a short wavetable, this manifests as distortion,
            # for a longer wavetable this is a pop or a click (much reduced compared to not trimming).
            # The longer the wavetable is relative to the period of the note, the smaller the error is.
            #eprint("Zero crossover error %f vs %f" %(sin(ang_per_sample*duration_samples), sin(duration_samples_pretrim*duration_samples)))

        result = np.zeros(duration_samples, dtype='float64')

        for h in self.harmonics:
            h_count = 1
            if h == 0:
                continue
            if self.config.lowpass:
                # Skip any harmonics that would exceed the Nyquist limit
                if self.freq * h_count > self.config.sample_rate / 2:
                    break

            for phase in phases:
                harmonic_rads_per_sample = ang_per_sample * h_count
                final_angle = harmonic_rads_per_sample * duration_samples + phase
                these_harmonics_angles = np.linspace(phase, final_angle, duration_samples)
                these_harmonics_values = h * np.sin(these_harmonics_angles)
                result = np.add(result, these_harmonics_values)

                h_count += 1
        #eprint("Get data took %f" %(time()-start))
        return result

    # Iterate over the phase list yeilding a wavetable for each one.
    # This uses get_data which generates data each time.
    # duration - seconds
    # trim - see get_data()
    def get_phases(self, duration, trim):
        for phase in self.phases:
            yield self.get_data(duration, trim, phase)

    # Prepare a wavetable of a specific duration with all the phases.
    # This is used typically for a long duration wavetable and may become
    # redundant if sufficient real-time performance can be acheived.
    def pre_prepare(self, duration, trim=True):
        self.wavetable = self.get_data(duration, trim)

    # Get the pre-prepared wavetable - pre_prepared must have previously been called.
    def get_prepared_data(self):
        if self.wavetable == None:
            raise UserWarning("Attempting to use wavetable uninitialized")
        return self.wavetable

    # Blocking function which simply generates a wavetable for a given duration
    # and plays it. Returns when the note has finished playing.
    def play(self, duration):
        data = self.get_data(duration)
        sd.play(data, self.config.sample_rate)
        sd.wait()

    def get_sinewave_attributes(self):
        return self.sinewaves
