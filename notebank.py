from config import eprint
from pygame import midi
from note import Note

class Chord:
    def __init__(self, notelist):
        note_data = []
        for note in notelist:
            note_data.append(note.get_data(1))



class Notebank:
    def __init__(self, config, tuning):
        # Some temporary testing of making chords


        # Start from Midi note number zero so we can just
        # have a simple array.

        self.notelist = []

        for midi_key in range(config.octaves * 12):
            note_name = midi.midi_to_ansi_note(midi_key)
            self.notelist.append(Note(note_name, config, tuning))

    def note_on(self, midi_key):
        eprint("Note on %d" %midi_key)

    def note_off(self, midi_key):
        eprint("Note off %d" %midi_key)
