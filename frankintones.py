#!/usr/bin/env python3

from sys import argv
from time import sleep
from note import Note
from notebank import Notebank
from config import Config, eprint
import json
from pygame import midi
import sounddevice as sd
import threading

stop = False

def non_gui_main(args):
    midi.init()
    eprint(sd.query_devices())
    midi_in = midi.Input(config.mididev)
    sleeptime = config.sleeptime
    tuning_number = 0
    magic_key = Note.name_to_number_midi(config.magickey)
    eprint("Magic key is %d %s %s" %(magic_key, config.magickey, midi.midi_to_ansi_note(magic_key)))
    initialized_tunings = {}

    while not stop:
        tuning_name, tuning = config.get_tuning_by_number(tuning_number)
        tuning_number += 1
        notebank = initialized_tunings.get(tuning_name)
        if notebank == None:
            eprint("Initialise with tuning %s" %tuning_name)
            notebank = Notebank(config, tuning)
            initialized_tunings[tuning_name] = notebank
        else:
            eprint("Switched to tuning %s" %tuning_name)
        
        switch_tuning = False # until next switch

        while not switch_tuning and not stop:
            if not midi_in.poll():
                # As neither poll nor read block..
                sleep(sleeptime)
            else:
                for e in midi_in.read(100):
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
    
   

def main_old(args):
    config = Config.get_default_config()
    Config.set_print_config(config)    
    scale = ["C3", "D3", "E3", "F3", "G3", "A4", "B4", "C4", "D4", "E4", "F4", "G4", "A5", "B5", "C5"]

    # Play using the default
    play_scale(scale, config, "Standard")

    # Play using frankintones
    play_scale(scale, config, "Frankintones")

def play_scale(scale, config, tuningName):
    tuning = config.get_tuning(tuningName)
    scaleData = []
    for noteName in scale:
        n = Note(noteName, config, tuning)
        scaleData += n.get_data(1)
    Note.play_buffer(scaleData, config)

if __name__ == "__main__":

    # Init the config    
    if len(argv) > 1:
        config = Config(argv[1])
    else:
        config = Config.get_default_config()

    Config.set_print_config(config)

    p = None

    if config.plotting:
        try:
            from plotter import Plotter
        except:
            eprint("Unable to import Plot - is Matplotlib installed?")
    
        if Plotter:
            p = Plotter(config.plotting)

    # Launch the stuff that doesn't write to the screen in a different thread
 
    t = threading.Thread(target = non_gui_main, args = argv)
    t.start()

    try:
        if p != None:
            p.run()    # Run the gui stuff in the main thread
        else:
            t.join() # TODO this is inconsistent
    except KeyboardInterrupt:
        print("Bye")
    finally:
        stop = True
        t.join()
