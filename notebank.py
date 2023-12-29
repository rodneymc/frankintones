from config import eprint
from pygame import midi
import numpy as np
from note import Note
from time import time, sleep
import sounddevice as sd
import threading

try:
    from plotter import Plotter, Plot_Request
except ImportError: # probably matpotlib not installed
    Plotter = None

class Notebank:
    def __init__(self, config, tuning):
        self.config = config
        self.out_stream = None
        self.start_idx = 0
        # Begin variables protected by sine_lists_mutex
        self.active_sinewaves = {}
        self.sinewaves_pending_start = {}
        self.sinewaves_pending_stop = {}
        # End variables protected by sine_lists_mutex
        self.sine_lists_mutex = threading.Lock()

        if Plotter:
            self.plotting = config.plotting
            if self.plotting:
                self.plotter = Plotter.get_plotter()
        else:
            self.plotting = False

        self.plot_request_pending = None
        self.plot_request_mutex = threading.Lock()

        # Start from Midi note number zero so we can just
        # have a simple array.

        self.notelist = []

        for midi_key in range(120): # should cover the whole range
            note_name = midi.midi_to_ansi_note(midi_key)
            n = Note(note_name, config, tuning)
            # So that all the pre-prepared notes are the same number of samples,
            # do not trim. This makes constructing chords easier. The trim is
            # useless for polyphonics anyway as the different notes in the chord
            # would have to be trimmed to different lengths anyhow.
            #n.pre_prepare(PRE_PREPARED_TIME, trim=False)
            self.notelist.append(n)
        

    def audio_callback(self, outdata, frames, time, status):
        if status:
            eprint(status)
        t = (self.start_idx + np.arange(frames)) / self.config.sample_rate
        #print (t)
        t = t.reshape(-1, 1)

        outdata[:] = np.zeros((frames, 1))

        with self.plot_request_mutex:
            if self.plot_request_pending:
                plot_request_pending = Plot_Request(self.plot_request_pending, self.start_idx, self.start_idx+frames)
                self.plot_request_pending = None
            else:
                plot_request_pending = None


        # Now add the existing active waves that are not being added or removed this
        # time around.
        for sinewave_list in self.active_sinewaves.values():
            for sinewave in sinewave_list:
                sw_data = sinewave.get_data(t)
                outdata[:] += sw_data

                if plot_request_pending:
                    plot_request_pending.add_individual(sinewave, sw_data, 0, frames)


        # TODO this is an outline framework for allowing the sinewaves to
        # be switched on and off separately. At present it actuall just does
        # them all at the same time.
        with self.sine_lists_mutex:
            for note_num, sw_list in self.sinewaves_pending_start.items():
                # Transfer the sinewaves that can be started this frame sequence
                # to the active list.
                # Start by seeing if there is already a lookup for this note in 
                # the active list.
                active_sw_list_for_note = self.active_sinewaves.get(note_num)
                if active_sw_list_for_note == None:
                    self.active_sinewaves[note_num] = active_sw_list_for_note = []
                
                sw_moved_to_active_list = []
                for sw in sw_list[::-1]: # iterate backwards for efficient removal
                    if sw not in active_sw_list_for_note:

                        # Where in the cycle will this waveform be at the beginning
                        # of the buffer?

                        buf_begin_angle = (t[0]*sw.freq + sw.phase_relative_to_fundamental) %np.pi

                        # Number of radians until next zero crossover
                        rad_to_zero = np.pi - buf_begin_angle

                        samples_to_zero = rad_to_zero * self.config.sample_rate / sw.freq
                        next_zero_relative = int(samples_to_zero)

                        if next_zero_relative < frames:
                            # It's going to occur in this frame
                            active_sw_list_for_note.append(sw)
                            sw_moved_to_active_list.append(sw)

                            # Generate the data for this sinewave
                            sw_data = sw.get_data(t)
                            # Overwrite up until the zero crossover with zeros
                            sw_data[0:next_zero_relative] = 0
                            outdata[:]+= sw_data
                            if plot_request_pending:
                                plot_request_pending.add_individual(sw, sw_data, 0, frames)
                
                for sw in sw_moved_to_active_list:
                    sw_list.remove(sw)

                for note_num, sw_list in self.sinewaves_pending_stop.items():
                    ## TODO timing
                    if self.active_sinewaves.get(note_num):
                        self.active_sinewaves.pop(note_num)

            if plot_request_pending:
                self.plotter.post_plot(plot_request_pending)

        self.start_idx += frames

    def note_on(self, midi_key):
        note = self.notelist[midi_key]

        self.request_plot("%s ON" % note.name)

        with self.sine_lists_mutex:

            # Remove this note from the stop queue.
            if self.sinewaves_pending_stop.get(midi_key):
                self.sinewaves_pending_stop.pop(midi_key)

            # Check for any sinewaves for this note that are still playing,
            # we won't be adding those.

            already_playing = self.active_sinewaves.get(midi_key)

            # Add all the sinewaves for that note to the start queue, unless
            # they happen to be playing already.
            new_sw_list = []
            for sw in self.notelist[midi_key].get_sinewave_attributes():
                if already_playing and sw in already_playing:
                    continue
                new_sw_list.append(sw)
            self.sinewaves_pending_start[midi_key] = new_sw_list

        if self.out_stream == None:
            self.out_stream = sd.OutputStream(blocksize=int(self.config.sample_rate/100), 
                        device = 5,
                        channels = 1,
                        callback = self.audio_callback,
                        samplerate=self.config.sample_rate)
            self.out_stream.start()

    def note_off(self, midi_key):
        note = self.notelist[midi_key]
        self.request_plot("%s OFF" %note.name)
        with self.sine_lists_mutex:
            self.sinewaves_pending_stop[midi_key] = self.active_sinewaves.get(midi_key)
            # Cancel any sinewaves from this note that have been queued to start already
            if self.sinewaves_pending_start.get(midi_key):
                self.sinewaves_pending_start.pop(midi_key)

    def request_plot(self, name):

        if self.plotting:
            self.plot_request_pending = name

    def stop(self):
        if self.out_stream:
            self.out_stream.stop()
            self.out_stream.close()
        self.out_stream = None
        self.current_note_mask = 0
        self.note_on_plotter = None
        self.note_off_plotter = None


    def __del__(self):
        self.stop()
