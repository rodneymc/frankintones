#!/usr/bin/env python3

from sys import argv
from time import sleep
from config import Config, eprint
import json
import threading
from midi_task import Midi_Task

if __name__ == "__main__":

    # Init the config    
    if len(argv) > 1:
        config = Config(argv[1])
    else:
        config = Config.get_default_config()

    Config.set_print_config(config)

    plotter = None
    stop_main_idle_loop = False

    Plotter = None
    if config.plotting:
        try:
            from plotter import Plotter
        except ImportError:
            eprint("Unable to import Plot - is Matplotlib installed?")
    
    if Plotter:
        plotter = Plotter(config.plotting)

    midi_task = Midi_Task(config)

    # Wrapper thread for the midi task
    def midi_task_wrapper():
        global stop_main_idle_loop
        try:
            midi_task.run()
        finally:
            # If the midi task returns or throws, stop the main thread
            if plotter:
                plotter.stop()
            else:
                stop_main_idle_loop = True
    
    #Start the Midi task
    midi_thread = threading.Thread(target = midi_task_wrapper)
    midi_thread.start()

    try:
        if plotter != None:
            plotter.run()    # Run the gui stuff in the main thread
        else:
            while stop_main_idle_loop == False:
                sleep(1)
    except KeyboardInterrupt:
        print("Bye")
    finally:
        midi_task.stop()
        midi_thread.join()
