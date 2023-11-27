from config import eprint
from pygame import midi
import numpy
from note import Note
from time import time, sleep
import sounddevice as sd

PRE_PREPARED_TIME = 1 # seconds

class Chord:
    def __init__(self, notelist, sample_rate):

        self.sample_rate = sample_rate
        samples = sample_rate * PRE_PREPARED_TIME
        self.buffer = numpy.zeros(samples)

        for note in notelist:
            self.add_note(note)


    def add_note(self, note):
        for phase_data in note.get_phases(PRE_PREPARED_TIME, False):
            self.buffer += phase_data

    def remove_note(self, note):
        for phase_data in note.get_phases(PRE_PREPARED_TIME, False):
            self.buffer -= phase_data

    def play(self):
        sd.play(self.buffer, self.sample_rate, loop=True)   

    def stop(self):
        sd.stop()

class Notebank:
    def __init__(self, config, tuning):
        self.config = config
        self.current_note_mask = 0
        self.current_chord = None

        # Start from Midi note number zero so we can just
        # have a simple array.

        self.notelist = []

        for midi_key in range(config.octaves * 12):
            note_name = midi.midi_to_ansi_note(midi_key)
            n = Note(note_name, config, tuning)
            # So that all the pre-prepared notes are the same number of samples,
            # do not trim. This makes constructing chords easier. The trim is
            # useless for polyphonics anyway as the different notes in the chord
            # would have to be trimmed to different lengths anyhow.
            #n.pre_prepare(PRE_PREPARED_TIME, trim=False)
            self.notelist.append(n)
        
        eprint("Initialise chord....")
        start = time()
#        chord = self.chord_from_namelist(["C4", "D#4", "G4", "B4"])
#        chord = self.chord_from_namelist(["C3", "E3", "G3"])
        chord = self.chord_from_namelist(["G3"])
        chord.play()
        for n in ["A#3", "D4", "F4", "G4"]:
            sleep(1.5)
            chord.add_note(self.notelist[Note.name_to_number_midi(n)])
        sleep(1.5)
        chord.stop()

        eprint("Took %f" %(time()-start))
        
    def chord_from_namelist(self, namelist):
        notes = []
        for name in namelist:
            notes.append(self.notelist[Note.name_to_number_midi(name)])
        return Chord(notes, self.config.sample_rate)
    

    def note_on(self, midi_key):
        note = self.notelist[midi_key]
        eprint("Note on %d %s %dHz" %(midi_key, note.name, note.freq))
        self.current_note_mask |= (1 << midi_key)
        if self.current_chord == None:
            self.current_chord = Chord([self.notelist[midi_key]], self.config.sample_rate)
            self.current_chord.play()
        else:
            self.current_chord.add_note(self.notelist[midi_key])

    def note_off(self, midi_key):
        eprint("Note off %d" %midi_key)
        self.current_note_mask &= ~ (1 << midi_key)
        
        if (self.current_chord != None):
            if (self.current_note_mask == 0):
                self.current_chord.stop()
                self.current_chord = None
            else:
                self.current_chord.remove_note(self.notelist[midi_key])

    def stop(self):
        if self.current_chord:
            self.current_chord.stop()
        self.current_chord = None
        self.current_note_mask = 0
