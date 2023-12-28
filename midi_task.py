from pygame import midi
import sounddevice as sd
from config import Config, eprint
from notebank import Notebank
from note import Note
from time import sleep

class Midi_Task:
    def __init__(self, config):
        midi.init()
        eprint(sd.query_devices())
        self.midi_in = midi.Input(config.mididev)
        self.stopping = False
        self.config = config

    def run(self):

        sleeptime = self.config.sleeptime
        tuning_number = 0
        magic_key = Note.name_to_number_midi(self.config.magickey)

        while not self.stopping:
            tuning_name, tuning = self.config.get_tuning_by_number(tuning_number)
            tuning_number += 1
            eprint("Initialise with tuning %s" %tuning_name)
            notebank = Notebank(self.config, tuning)
            
            switch_tuning = False # until next switch

            while not switch_tuning and not self.stopping:
                if not self.midi_in.poll():
                    # As neither poll nor read block..
                    sleep(sleeptime)
                else:
                    for e in self.midi_in.read(100):
                        msg = e[0]
                        # The top half of the first byte is the command, the bottom byte is the channel
                        # TODO we just are accepting all channels right now.
                        cmd = msg[0] & 0xf0
                        key = msg[1]

                        if cmd == 128:
                            notebank.note_off(key)
                        elif cmd == 144:
                            # Note on, unless it's the magic key
                            if key == magic_key:
                                switch_tuning = True # To the next tuning
                                notebank.stop()
                                break # Don't process any more messages until we have new notebank
                            else:
                                notebank.note_on(key)

    def stop(self):
        self.stopping = True
