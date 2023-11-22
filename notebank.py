from config import eprint
from pygame import midi
import numpy
from note import Note
from time import time
import sounddevice as sd

PRE_PREPARED_TIME = 10 # seconds

class Chord:
    def __init__(self, notelist, sample_rate):

        self.sample_rate = sample_rate
        samples = sample_rate * PRE_PREPARED_TIME

        if len (notelist) == 1:
            self.buffer = numpy.array(notelist[0].get_prepared_data())

        note_data = notelist[0].get_prepared_data().copy()

        for note in notelist[1:]:
            note_data = numpy.add(note.get_prepared_data(), note_data)

        self.buffer = note_data

    def play(self):
        sd.play(self.buffer, self.sample_rate)

    def stop(self):
        sd.stop()

class Notebank:
    def __init__(self, config, tuning):
        self.config = config
        self.current_notes = 0
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
            n.pre_prepare(PRE_PREPARED_TIME, trim=False)
            self.notelist.append(n)
        
        eprint("Initialise chord....")
        start = time()
        chord = self.chord_from_namelist(["C4", "D#4", "G4", "B4"])
        chord.play()
        eprint("Took %f" %(time()-start))
        
    def chord_from_namelist(self, namelist):
        notes = []
        for name in namelist:
            notes.append(self.notelist[Note.name_to_number_midi(name)])
        return Chord(notes, self.config.sample_rate)
    

    def note_on(self, midi_key):
        note = self.notelist[midi_key]
        eprint("Note on %d %s %dHz" %(midi_key, note.name, note.freq))
        # For test purposes for now just construct a monophonic chord
        self.current_chord = Chord([self.notelist[midi_key]], self.config.sample_rate)
        self.current_chord.play()

    def note_off(self, midi_key):
        eprint("Note off %d" %midi_key)
        # For now just stop playing the current chord.
        if (self.current_chord != None):
            self.current_chord.stop