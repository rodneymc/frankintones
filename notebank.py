from config import eprint
from pygame import midi
import numpy as np
from note import Note
from time import time, sleep
import sounddevice as sd
import threading

try:
    from plotter import Plotter
except: # probably matpotlib not installed
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
        self.plot_request_pending = False
        # End variables protected by sine_lists_mutex
        self.sine_lists_mutex = threading.Lock()
        if Plotter:
            self.plotting = config.plotting
            if self.plotting:
                self.plotter = Plotter.get_plotter()
        else:
            self.plotting = False

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

        # Now add the existing active waves that are not being added or removed this
        # time around.
        for sinewave_list in self.active_sinewaves.values():
            for sinewave in sinewave_list:
                outdata[:] += sinewave.amp * np.sin(t*sinewave.freq + sinewave.phase)


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

                        # Calculate the samples between zero crossover, based on the
                        # angular freq. Note we use pi not 2pi because two crosssovers.
                        # Then add the initial phase offset. This gives the number of samples
                        # to the first zero crossover
                        samples_between_zeros = int (self.config.sample_rate / sw.freq * np.pi) 
                        half_phase_offset_samples = int (self.config.sample_rate * sw.phase/sw.freq/2)

                        samples_since_last_zero = self.start_idx % samples_between_zeros
                        next_zero_relative = samples_between_zeros + half_phase_offset_samples - samples_since_last_zero

                        if next_zero_relative < frames:
                            # It's going to occur in this frame
                            active_sw_list_for_note.append(sw)
                            sw_moved_to_active_list.append(sw)
                
                for sw in sw_moved_to_active_list:
                    sw_list.remove(sw)

                for note_num, sw_list in self.sinewaves_pending_stop.items():
                    ## TODO timing
                    if self.active_sinewaves.get(note_num):
                        self.active_sinewaves.pop(note_num)

            if self.plot_request_pending:
                self.plotter.post_plot()
                self.plot_request_pending = False

        self.start_idx += frames

    def note_on(self, midi_key):
        note = self.notelist[midi_key]
        eprint("Note on %d %s %dHz" %(midi_key, note.name, note.freq))

        self.request_plot()

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
        eprint("Note off %d" %midi_key)
        with self.sine_lists_mutex:
            self.sinewaves_pending_stop[midi_key] = self.active_sinewaves.get(midi_key)
            # Cancel any sinewaves from this note that have been queued to start already
            if self.sinewaves_pending_start.get(midi_key):
                self.sinewaves_pending_start.pop(midi_key)

    def request_plot(self):

        if self.plotting:
            self.plot_request_pending = True

        return
        ###TODO obsolete code below

        # Iterate the list of active plots and remove those that
        # are actually finished with

        if (self.plotting):
            with self.sine_lists_mutex:
                for p in self.plots_active[::-1]:
                    if p.finished(): # user has closed the window
                        self.plots_active.remove(p)
                if len(self.plots_active) < self.plotting:
                    self.plot_request_pending = True


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
