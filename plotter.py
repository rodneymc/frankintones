import threading
import matplotlib.pyplot as plt
import numpy as np

# Since the work done by this class must be in the main thread,
# let it be a singleton. plt is also a singleton

class Plotter:
    singleton = None

    def get_plotter():
        if Plotter.singleton == None:
            raise Exception("Plotter object has not been constructed")
        return Plotter.singleton
        
    def __init__(self, max_plots):
        if Plotter.singleton != None:
            raise Exception("Can only construct one Plotter")
        self.condition = threading.Condition()
        # Keep track of how many open windows there are
        self.max_plots = max_plots
        self.figure_count = 0
        self.figure_count_lock = threading.Lock()

        self.stop_flag = False
        self.posted_data = None
        plt.ion()

        Plotter.singleton = self

    def post_plot(self):
        with self.figure_count_lock:
            if self.figure_count >= self.max_plots:
                return
            self.figure_count += 1

        with self.condition:
            self.posted_data = True # TODO
            self.condition.notify()
    
    def run(self):
        while not self.stop_flag:

            data_to_process = None

            with self.condition:
                self.condition.wait(.1)
                data_to_process = self.posted_data
                self.posted_data = None

            plt.pause(.1) ## Allow for Matplotlib events

            if self.stop_flag:
                break

            if data_to_process:
                print("New figure")
                fig, ax = plt.subplots(figsize=(5, 2.7), layout='constrained')
                fig.canvas.mpl_connect('close_event', self.on_close)
                x = np.linspace(0, 2, 100)  # Sample data.
                ax.plot(x, x**2, label='quadratic')
                plt.draw()

    def stop(self):
        self.stop_flag = True

        with self.condition:
            self.condition.notify()

    ## Matplotlib event handlers
    def on_close(self, event):
        with self.figure_count_lock:
            self.figure_count -= 1
        # Seemingly due to a bug in TK or Matplotlib we have to close all of the windows
        # and start again.
        plt.close()
