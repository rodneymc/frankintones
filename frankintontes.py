#!/usr/bin/env python3

from sys import argv
from note import Note
from config import Config
import json

def main(args):
    config = Config("config/default.json")
    Config.set_print_config(config)    
    print("Hello")
    scale = ["C1", "D1", "E1", "F1", "G1", "A2", "B2", "C2", "D2", "E2", "F2", "G2", "A3", "B3", "C3"]
    for noteName in scale:
        n = Note(noteName, config)
        n.play(1)

    config = Config("config/frankintones.json")
    for noteName in scale:
        n = Note(noteName, config)
        n.play(1)

if __name__ == "__main__":
    main(argv)
