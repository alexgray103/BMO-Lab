## tkinter used for widgets that make up GUI framework
from tkinter import *
import numpy as np #https://scipy-lectures.org/intro/numpy/operations.html
from tkinter import messagebox

from tkinter.filedialog import askopenfilename
import tkinter.font as font

#import all dependancies
from settings import Settings as _Settings
from ESS_functions import *
from settings_window import settings_window
from keyboard import *

# create new files and folders
import os

#used for serial comm with arduino
import serial
from time import sleep
import time
 
#saving data to csv
import pandas as pd
import csv

### matplotlib used for plotting data to a canvas 
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
import matplotlib.pyplot as plt


################ global variables ###########################
spec_folder_path = '/home/pi/Desktop/Spectrometer'
spec_folder_settings = '/home/pi/Desktop/Spectrometer/settings'
settings_file = '/home/pi/Desktop/Spectrometer/settings/settings.csv'
acquire_file = '/home/pi/Desktop/Spectrometer/settings/acquire_file.csv'
wavelength = range(0,288)
global filename




####################################################################


# create folder to hold all settings and data
if not os.path.exists(spec_folder_path):
        os.makedirs(spec_folder_path)
                
if not os.path.exists(spec_folder_settings):
        os.makedirs(spec_folder_settings)
# create acquire pseudo file if not already within spectrometer folder

try:
    #acquire file holds a temporary data array
    open_acquire_file = open(acquire_file, 'x')
except:
    open_acquire_file = open(acquire_file, 'a')
    
    
class Main_GUI:
    def __init__(self, master):
        global settings_file
        root = master
        root.title("ESS System Interface")
        full_screen = False
        #read in settings of the monitor plugged in and create window to that size
        self.w, self.h = root.winfo_screenwidth(), root.winfo_screenheight(),
        self.screensize = str(self.w) + 'x' + str(self.h)
        if full_screen == True:
            root.attributes('-fullscreen', True) # fullscreen on touchscreen
        else:
            root.geometry(self.screensize) # actual size of RPi touchscreen
            root.geometry('800x480')
            #root.geometry('800x480')
        root.configure(bg= "sky blue")
        root.minsize(800,480) # min size the window can be dragged to

        root.tk.call('wm','iconphoto', root._w, PhotoImage(file = "/home/pi/Desktop/BMO_Lab/ESS_png"))
        
        # parameters for buttons and frames
        #create all the buttons onto to the main window
        button_width = 10
        button_big_height = 4
        button_small_height = 3
        sticky_to = 'nsew' # allows all buttons to resize
         
        # setup Serial port- 
         ## Graphing Frame and fake plot
        self.graph_frame = Frame(root, background = "white")
        self.graph_frame.grid(row = 1, column = 1, columnspan = 6, rowspan = 5, padx = 1, pady = 3, sticky = sticky_to)
        
        #initalize figure
        self.fig = plt.figure()
        #initalize canvas for plotting
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)  # A tk.DrawingArea.
        # create toolbar for canvas
        toolbar = NavigationToolbar2Tk(self.canvas, self.graph_frame)
        toolbar.update()
        self.canvas.get_tk_widget().pack(fill = BOTH, expand = True)
        
        # create function object for calling functions
        settings_func = _Settings(settings_file)
        
        try:
            settings_func.create_settings()
        except:
            pass
        
        (self.settings, self.wavelength) = settings_func.settings_read()
        
        df = []
        func = functions(root, self.canvas, self.fig, df)
        
        
        # allow buttons and frames to resize with the resizing of the root window
        root.grid_columnconfigure((0,1,2,3,4,5,6),weight = 1)
        root.grid_rowconfigure((0,1,2,3,4,5,6),weight = 1)
        
        
        # with all their corresponding functions (command)
        self.quit_button = Button(root, text = "Quit", fg = 'Red', command = root.destroy, width = button_width, height = button_big_height)
        self.quit_button.grid(row = 0, column = 6, padx = 1, sticky = sticky_to)
        
        self.help_button = Button(root, text = "Help", fg = 'black', command = root.destroy, width = button_width, height = button_big_height)
        self.help_button.grid(row = 0, column = 5, sticky = sticky_to)
        
        self.settings_button = Button(root, text = "Settings", fg = 'black', command = lambda: self.window_popup(root), width = button_width, height = button_big_height)
        self.settings_button.grid(row = 0, column = 4, padx = (8,1), sticky = sticky_to)
        
        self.save_spectra_button = Button(root, text = "Save as Spectra", wraplength = 80, fg = 'black', command = func.plot_selected, width = button_width, height = button_big_height, state = DISABLED)
        self.save_spectra_button.grid(row = 0, column = 3, padx = (1,8), sticky = sticky_to)
        
        self.save_reference_button = Button(root, text = "Save as Reference", wraplength = 80, fg = 'black', command = func.plot_selected, width = button_width, height = button_big_height, state = DISABLED)
        self.save_reference_button.grid(row = 0, column = 2, padx = (10,0), sticky = sticky_to)
        
        self.open_new_button = Button(root, text = "New Experiment", wraplength = 80, fg = 'black', command = func.open_new_experiment, width = button_width, height = button_big_height)
        self.open_new_button.grid(row = 0, column = 1, padx = (0,5), sticky = sticky_to)
        
        self.open_experiment_button = Button(root, text = "Open Experiment", wraplength = 80, fg = 'black', command = func.OpenFile, width = button_width, height = button_big_height)
        self.open_experiment_button.grid(row = 0, column = 0, sticky = sticky_to)
        
        self.acquire_button = Button(root, text = "Acquire", wraplength = 80, fg = 'black',
                                     command = lambda: func.acquire(save = False), width = button_width, height = button_big_height)
        self.acquire_button.grid(row = 1, column = 0, pady = (3,1), sticky = sticky_to)
        
        self.acquire_save_button = Button(root, text = "Acquire and Save", fg = 'black', wraplength = 80, command = func.plot_selected, width = button_width, height = button_big_height, state = DISABLED)
        self.acquire_save_button.grid(row = 2, column = 0, pady = (0,1), sticky = sticky_to)
        
        self.autorange_button = Button(root, text = "Auto-Range", fg = 'black', wraplength = 80, command = func.plot_selected, width = button_width, height = button_big_height)
        self.autorange_button.grid(row = 3, column = 0, pady = (0,5), sticky = sticky_to)
        
        self.open_loop_button = Button(root, text = "Open Loop", fg = 'black',state = DISABLED, command = func.plot_selected, width = button_width, height = button_big_height)
        self.open_loop_button.grid(row = 4, column = 0, pady = (5,1), sticky = sticky_to)
        
        self.sequence_button = Button(root, text = "Sequence", fg = 'black', wraplength = 80, command = func.plot_selected, width = button_width, height = button_big_height)
        self.sequence_button.grid(row = 5, column = 0, sticky = sticky_to)
        
        self.scan_button = Button(root, text = "Sequence and Save", fg = 'black', wraplength = 80, command = func.plot_selected, width = button_width, height = button_big_height)
        self.scan_button.grid(row = 6, column = 0, sticky = sticky_to)
        
        self.water_pump_button = Button(root, text = "Scan", fg = 'black', wraplength = 80, command = func.plot_selected, width = button_width, height = button_small_height)
        self.water_pump_button.grid(row = 6, column = 1, padx = 1, sticky = sticky_to)
        
        self.ratio_view_button = Button(root, text = "Ratio View", fg = 'black', wraplength = 80, command = func.plot_selected, width = button_width, height = button_small_height, state = DISABLED)
        self.ratio_view_button.grid(row = 6, column = 2, padx = 1, sticky = sticky_to)
        
        self.autoscale_button = Button(root, text = "Autoscale", fg = 'black', wraplength = 80, command = func.plot_selected, width = button_width, height = button_small_height)
        self.autoscale_button.grid(row = 6, column = 3, padx = 1, sticky = sticky_to)
        
        self.plot_selected_button = Button(root, text = "Plot Selected", fg = 'black', wraplength = 80, command = func.plot_selected, state = DISABLED, width = button_width, height = button_small_height)
        self.plot_selected_button.grid(row = 6, column = 4, padx = 1, sticky = sticky_to)
        
        self.clear_button = Button(root, text = "Clear", fg = 'black', wraplength = 80, command = func.plot_selected, width = button_width, height = button_small_height)
        self.clear_button.grid(row = 6, column = 5, padx = 1, sticky = sticky_to)
        
        self.add_remove_button = Button(root, text = "Add/Remove Plots", fg = 'black', wraplength = 85, state = DISABLED, command = func.plot_selected, width = button_width, height = button_small_height)
        self.add_remove_button.grid(row = 6, column = 6, padx = 5, pady = 1, sticky = sticky_to)
        
    def window_popup(self, master):
        self.popup_window = Toplevel(master)
        self.sett_popup = settings_window(self.popup_window, master)
    
        
        
def main():
    root = Tk()
    app = Main_GUI(root)
    root.mainloop()
    
if __name__ == '__main__':
    main()