#!/usr/bin/env python3

from sys import argv
from note import Note
from config import Config
import json

def main(args):
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
    main(argv)
