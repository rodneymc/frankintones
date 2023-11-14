import json
from sys import stderr, stdout


global print_config

class Config:
    def __init__(self):
        jobj = json.load(open("config.json"))

        self.reffreq = Config.get_value(jobj, "reffreq", 440)
        self.refinterval = Config.get_value(jobj, "refinterval", 2)
        self.refdivisor = Config.get_value(jobj, "refdivisor", 12)
        self.refnote = Config.get_value(jobj, "refnote", "A2")

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
