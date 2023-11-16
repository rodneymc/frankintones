import json, os
from sys import stderr, stdout
from shutil import copyfile

global print_config
TEMPLATE="config/config.template.json"
DEFAULT="config/config.json"

class Config:

    class Tuning():
        def __init__(self, jobj):
            self.reffreq = Config.get_value(jobj, "reffreq", 440)
            self.refinterval = Config.get_value(jobj, "refinterval", 2)
            self.refdivisor = Config.get_value(jobj, "refdivisor", 12)
            self.refnote = Config.get_value(jobj, "refnote", "A4")
            self.harmonics = Config.get_value(jobj, "harmonics", [0.5])

    def __init__(self, fname=DEFAULT):

        # Use the sandbox config if none is specified. If the file
        # doesn't yet exist (it is in .gitignore) then create it from
        # the default.json template.

        if (fname == DEFAULT):
            if not os.path.exists(DEFAULT):
                copyfile(TEMPLATE, DEFAULT)

        jfile = open(fname)
        jobj = json.load(jfile)
        jfile.close()

        if (jobj.get("debug_stderr") == False):
            self.dbg = stdout
        else:
            self.dbg = stderr

        self.sample_rate = Config.get_value(jobj, "sample_rate", 48000)
        self.lowpass = Config.get_value(jobj, "low_pass", True)
        self.mididev = Config.get_value(jobj, "mididev", None)
        self.sleeptime = Config.get_value(jobj, "sleeptime", 0.001)
        self.magickey = Config.get_value(jobj, "magickey", "A0")
        self.octaves = Config.get_value(jobj, "octaves", None)

        tunings = {}
        tunings_obj = jobj.get("tunings")
        if tunings_obj == None: raise ValueError("No tunings in config")

        for tname in tunings_obj.keys():
            tunings[tname] = Config.Tuning(tunings_obj[tname])
        self.tunings = tunings

    def get_value(jobj, key, default):
        res = jobj.get(key)
        if res == None: res = default

        if res == None:
            raise ValueError("%s has no config value or internal default" % key)
        return res
    
    ## Allow setting of global print_config
    def set_print_config(c):
        global print_config
        print_config = c

    default_config = None

    def get_default_config():
        if Config.default_config == None:
            Config.default_config = Config()
        return Config.default_config
    
    def get_tuning(self, name):
        return self.tunings[name]
    
    # Get a tuning by its number, we just roll over once we've
    # got to the end
    def get_tuning_by_number(self, number):
        tuning_names = list(self.tunings.keys())
        number %= len(tuning_names)
        name = tuning_names[number]
        return name, self.tunings[name]

def eprint(*args, **kwargs):
    print(*args, file=print_config.dbg, **kwargs)
