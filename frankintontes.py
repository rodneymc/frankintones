#!/usr/bin/env python3

from sys import argv
from note import Note
from config import Config
import json

def main(args):
    config = Config("config/default.json")
    Config.set_print_config(config)    
    scale = ["C1", "D1", "E1", "F1", "G1", "A2", "B2", "C2", "D2", "E2", "F2", "G2", "A3", "B3", "C3"]

    # Play using the default
    play_scale(scale, config)

    # Play using frankintones
    play_scale(scale, Config("config/frankintones.json"))

def play_scale(scale, config):
    scaleData = []
    for noteName in scale:
        n = Note(noteName, config)
        scaleData += n.get_data(1)
    Note.play_buffer(scaleData)

if __name__ == "__main__":
    main(argv)
