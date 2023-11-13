#!/usr/bin/env python3

from sys import argv
from note import Note

def main(args):
    print("Hello")
    n = Note("C2")
    n.makecycle()
    n.play(10)

if __name__ == "__main__":
    main(argv)

