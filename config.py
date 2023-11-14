import json, os
from sys import stderr, stdout
from shutil import copyfile

global print_config
SANDBOX="config/sandbox.json"
DEFAULT="config/default.json"

class Config:
    def __init__(self, fname=SANDBOX):

        # Use the sandbox config if none is specified. If the file
        # doesn't yet exist (it is in .gitignore) then create it from
        # the default.json template.

        if (fname == SANDBOX):
            if not os.path.exists(SANDBOX):
                copyfile(DEFAULT, SANDBOX)

        jobj = json.load(open(fname))

        self.reffreq = Config.get_value(jobj, "reffreq", 440)
        self.refinterval = Config.get_value(jobj, "refinterval", 2)
        self.refdivisor = Config.get_value(jobj, "refdivisor", 12)
        self.refnote = Config.get_value(jobj, "refnote", "A2")
        self.harmonics = Config.get_value(jobj, "harmonics", [0.5])

        if (jobj.get("debug_stderr") == False):
            self.dbg = stdout
        else:
            self.dbg = stderr

    def get_value(jobj, key, default):
        res = jobj.get(key)
        if res == None: res = default
        return res
    
    ## Allow setting of global print_config
    def set_print_config(c):
        global print_config
        print_config = c   

def eprint(*args, **kwargs):
    print(*args, file=print_config.dbg, **kwargs)
