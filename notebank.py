from config import eprint
from pygame import midi
import numpy as np
from note import Note
from time import time, sleep
import sounddevice as sd


class Notebank:
    def __init__(self, config, tuning):
        self.config = config
        self.current_note_mask = 0
        self.current_chord = None
        self.out_stream = None
        self.start_idx = 0

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
        

    def audio_callback(self, outdata, frames, time, status):
        if status:
            eprint(status)
        t = (self.start_idx + np.arange(frames)) / self.config.sample_rate
        #print (t)
        t = t.reshape(-1, 1)
        done_first = False

        for note_num in range(len(self.notelist)):
            if (1 << note_num) & self.current_note_mask != 0: 
                for sinewave in self.notelist[note_num].get_sinewave_attributes():
                    if not done_first:
                        outdata[:] = sinewave.amp * np.sin(t*sinewave.freq + sinewave.phase)
                        done_first = True
                    else:
                        outdata[:] += sinewave.amp * np.sin(t*sinewave.freq + sinewave.phase)
        self.start_idx += frames

    def note_on(self, midi_key):
        note = self.notelist[midi_key]
        eprint("Note on %d %s %dHz" %(midi_key, note.name, note.freq))
        
        self.current_note_mask |= (1 << midi_key)
        if self.out_stream == None:
            self.out_stream = sd.OutputStream(blocksize=int(self.config.sample_rate/100), 
                        device = 5,
                        channels = 1,
                        callback = self.audio_callback,
                        samplerate=self.config.sample_rate)
            self.out_stream.start()

    def note_off(self, midi_key):
        eprint("Note off %d" %midi_key)
        self.current_note_mask &= ~ (1 << midi_key)
        if self.current_note_mask == 0:
            ## TODO don't stop abruptly
            self.out_stream.stop()
            self.out_stream.close()
            self.out_stream = None
        

    def stop(self):
        if self.current_chord:
            self.current_chord.stop()
        self.current_chord = None
        self.current_note_mask = 0
