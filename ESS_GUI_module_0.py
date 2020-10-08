## tkinter used for widgets that make up GUI framework
from tkinter import *
import numpy as np #https://scipy-lectures.org/intro/numpy/operations.html
from tkinter import messagebox
import threading
import tkinter.font as tkFont
import random

#import all dependancies
from settings import Settings as _Settings
from ESS_functions import *
from keyboard import *
#from settings_window import settings_popup_window
import settings_window

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
# open up a serial to allow for reading in of module attachment

class Module_0:
    def __init__(self, master):
        global settings_file
        self.root = master
        self.root.title("ESS System Interface")
        full_screen = True
        if full_screen:
            self.root.attributes('-fullscreen', True) # fullscreen on touchscreen
        else:
            self.root.geometry('800x480') # actual size of RPi touchscreen
        #self.root.attributes('-fullscreen',True)
        self.root.configure(bg= "sky blue")
        self.root.minsize(800,480) # min size the window can be dragged to
    
        self.root.tk.call('wm','iconphoto', self.root._w, PhotoImage(file = "/home/pi/Desktop/BMO_Lab/ESS_png"))
        
        self.open_loop_stop = None # control open Loop button
        # parameters for buttons and frames
        #create all the buttons onto to the main window
        button_width = 8
        button_big_height = 4
        button_small_height = 3
        sticky_to = 'nsew' # allows all buttons to resize
        
        # battery check functions
        self.percent = 0 # battery percent variable
        self.battery_message = StringVar()
        self.battery_message.set(" %")
        battery_font = tkFont.Font(family = "Lucida Grande", size = 16)
        label_font = tkFont.Font(family = "Lucida Grande", size = 12)
        
        module_message = 'Module 0: Base ESS'
        # setup Serial port- 
         ## Graphing Frame and fake plot
        self.graph_frame = Frame(self.root, background = "white")
        self.graph_frame.grid(row = 1, column = 1, columnspan = 7, rowspan = 5, padx = 1, pady = 3, sticky = sticky_to)
        
        #initalize figure
        self.fig = plt.figure()
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('ADC Counts')
        plt.xlim(300,900)
        plt.ylim(0,66500)
        plt.subplots_adjust(bottom =0.14, right = 0.95, top = 0.96)
        
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
        
        #(self.settings, self.wavelength) = settings_func.settings_read()
        self.func = functions(self.root, self.canvas, self.fig)
        #self.func.home()
        
        
        # allow buttons and frames to resize with the resizing of the root window
        self.root.grid_columnconfigure((0,1,2,3,4,5,6,7),weight = 1)
        self.root.grid_rowconfigure((0,1,2,3,4,5,6),weight = 1)
        
        
        # with all their corresponding functions (command)
        self.quit_button = Button(self.root, text = "Quit", fg = 'Red', command = self.quit_button, width = button_width, height = button_big_height)
        self.quit_button.grid(row = 0, column = 6, padx = 1, sticky = sticky_to)
        
        self.help_button = Button(self.root, text = "Help", fg = 'black', command = self.func.plot_selected, width = button_width, height = button_big_height)
        self.help_button.grid(row = 0, column = 5, sticky = sticky_to)
        
        self.settings_button = Button(self.root, text = "Settings", fg = 'black', command = lambda: self.window_popup(self.root), width = button_width, height = button_big_height)
        self.settings_button.grid(row = 0, column = 4, padx = (1,1), sticky = sticky_to)
        
        self.save_spectra_button = Button(self.root, text = "Save as Spectra", wraplength = 80, fg = 'black', command = self.func.save_spectra, width = button_width, height = button_big_height, state = NORMAL)
        self.save_spectra_button.grid(row = 0, column = 3, padx = (1,1), sticky = sticky_to)
        
        self.save_reference_button = Button(self.root, text = "Save as Reference", wraplength = 80, fg = 'black', command = self.func.save_reference, width = button_width, height = button_big_height, state = NORMAL)
        self.save_reference_button.grid(row = 0, column = 2, padx = (1,0), sticky = sticky_to)
        
        self.open_new_button = Button(self.root, text = "New Experiment", wraplength = 80, fg = 'black', command = self.func.open_new_experiment, width = button_width, height = button_big_height)
        self.open_new_button.grid(row = 0, column = 1, padx = (0,1), sticky = sticky_to)
        
        self.open_experiment_button = Button(self.root, text = "Open Experiment", wraplength = 80, fg = 'black', command = self.func.OpenFile, width = button_width, height = button_big_height)
        self.open_experiment_button.grid(row = 0, column = 0, sticky = sticky_to)
        
        self.acquire_button = Button(self.root, text = "Acquire", wraplength = 80, fg = 'black',
                                     command = lambda: self.func.acquire(save = False), width = button_width, height = button_big_height)
        self.acquire_button.grid(row = 1, column = 0, pady = (3,1), sticky = sticky_to)
        
        self.acquire_save_button = Button(self.root, text = "Acquire and Save", fg = 'black', wraplength = 80,
                                          command = lambda: self.func.acquire(save = True)
                                          , width = button_width, height = button_big_height, state = NORMAL)
        self.acquire_save_button.grid(row = 2, column = 0, pady = (0,1), sticky = sticky_to)
        
        self.autorange_button = Button(self.root, text = "Auto-Range", fg = 'black', wraplength = 80,
                                       command = self.func.autorange,width = button_width,
                                       height = button_big_height)
        self.autorange_button.grid(row = 3, column = 0, pady = (0,5), sticky = sticky_to)
        
        self.open_loop_button = Button(self.root, text = "Open Loop", fg = 'black',state = NORMAL, command = self.open_loop, width = button_width, height = button_big_height)
        self.open_loop_button.grid(row = 4, column = 0, pady = (5,1), sticky = sticky_to)
        
        self.sequence_button = Button(self.root, text = "Sequence", fg = 'black', wraplength = 80, command = lambda: self.func.sequence(save = False), width = button_width, height = button_big_height)
        self.sequence_button.grid(row = 5, column = 0, sticky = sticky_to)
        
        self.sequence_save_button = Button(self.root, text = "Sequence and Save", fg = 'black', wraplength = 80, command = lambda: self.func.sequence(save =True), width = button_width, height = button_big_height)
        self.sequence_save_button.grid(row = 6, column = 0, sticky = sticky_to)
        
        #self.scan_button = Button(self.root, text = "Scan", fg = 'black', wraplength = 80, command = lambda: self.func.scan(save = True), width = button_width, height = button_small_height)
        #self.scan_button.grid(row = 6, column = 1, padx = 1, sticky = sticky_to)
        
        self.ratio_view_button = Button(self.root, text = "Ratio View", fg = 'black', wraplength = 80, command = self.ratio_view_toggle, width = button_width, height = button_small_height, state = NORMAL)
        self.ratio_view_button.grid(row = 6, column = 1, padx = 1, sticky = sticky_to)
        
        self.autoscale_button = Button(self.root, text = "Autoscale", fg = 'black', wraplength = 80, command = self.autoscale_toggle, width = button_width, height = button_small_height)
        self.autoscale_button.grid(row = 6, column = 2, padx = 1, sticky = sticky_to)
        
        self.plot_selected_button = Button(self.root, text = "Plot Selected", fg = 'black', wraplength = 80, command = self.func.plot_selected, state = NORMAL, width = button_width, height = button_small_height)
        self.plot_selected_button.grid(row = 6, column = 3, padx = 1, sticky = sticky_to)
        
        self.clear_button = Button(self.root, text = "Clear", fg = 'black', wraplength = 80, command = self.func.clear, width = button_width, height = button_small_height)
        self.clear_button.grid(row = 6, column = 4, padx = 1, sticky = sticky_to)
        
        self.add_remove_button = Button(self.root, text = "Add/Remove Plots", fg = 'black', wraplength = 85, state = NORMAL, command = self.func.add_remove_func, width = button_width, height = button_small_height)
        self.add_remove_button.grid(row = 6, column = 5, padx = 5, pady = 1, sticky = sticky_to)
        
        module_label = Label(self.root, bg = 'sky blue', text = module_message, wraplength = 80, font = label_font)
        module_label.grid(row = 6, column = 6, padx = 5, pady = 1, columnspan = 2, sticky = sticky_to)
        
        #battery_label = Label(self.root, bg = 'sky blue', textvariable = self.battery_message)
        #battery_label.grid(row = 6, column = 6, padx = 5, pady = 1, columnspan = 2, sticky = 'nsew')
        
        #self.battery_frame.grid_rowconfigure((0,1,2,3),weight = 1)
        #self.battery_frame.grid_columnconfigure((0),weight = 1)
        
        self.battery_frame = Frame(self.root, bg = 'sky blue')
        self.battery_frame.grid(row = 0, column = 7, padx = (0,1), pady = 1, sticky = 'nsew')
        
        
        self.battery_label_1 = Label(self.battery_frame, bg = "green", width = 1)
        self.battery_label_1.pack(fill = BOTH)
        
        self.battery_label_2 = Label(self.battery_frame, textvariable = self.battery_message, bg = "green", width = 1)
        self.battery_label_2.pack(fill = BOTH)
        
        self.battery_label_3 = Label(self.battery_frame, bg = "green", width = 1)
        self.battery_label_3.pack(fill = BOTH)
        
        self.battery_label_4 = Button(self.battery_frame, bg = "green", width = 1)
        self.battery_label_4.pack(fill = BOTH)
        
        
        # show module connected
        #messagebox.showinfo('Module #','Module 0: Base ESS System connected (No attachments)')
        
        
        def battery_percent_check():
            self.percent = self.func.battery_check()
            battery_message_temp = str(self.percent) + " %"
            #self.battery_message.set(battery_message_temp)
            self.percent = 97
            self.percent = random.randint(1,100)
            print(self.percent)
            
            #change battery status
            
            if int(self.percent) >=75:
                print('> 75')
                self.battery_message.set(">80 %")
                self.battery_label_1.configure(bg = 'green')
                self.battery_label_2.configure(bg = 'green')
                self.battery_label_3.configure(bg = 'green')
                self.battery_label_4.configure(bg = 'green')
            elif int(self.percent) <75 and self.percent > 50:
                self.battery_message.set("75 %")
                self.battery_label_2.configure(bg = 'green')
                self.battery_label_1.configure(bg = 'red')
                self.battery_label_3.configure(bg = 'green')
                self.battery_label_4.configure(bg = 'green')
                print('50-75')
            elif int(self.percent) <50 and self.percent >25:
                self.battery_message.set("50 %")
                self.battery_label_1.configure(bg = 'red')
                self.battery_label_2.configure(bg = 'red')
                self.battery_label_3.configure(bg = 'green')
                self.battery_label_4.configure(bg = 'green')
                print('25-50')
            else:
                self.battery_message.set("<25 %")
                self.battery_label_1.configure(bg = 'red')
                self.battery_label_2.configure(bg = 'red')
                self.battery_label_3.configure(bg = 'red')
                self.battery_label_4.configure(bg = 'yellow')
                print('0-25')
            
            self.root.update_idletasks()
            #threading.Timer(5,battery_percent_check).start()
            try:
                self.root.after(10000, battery_percent_check)
            except:
                pass
            
        battery_percent_check()
        
   # allows for popup of settings window
    def window_popup(self, master):
        self.popup_window = Toplevel(master)
        self.sett_popup = settings_window.settings_popup_window(self.popup_window, master)
    
    # send values to change visualization of data in functions class
    def autoscale_toggle(self):
        if self.autoscale_button['relief'] == SUNKEN:
            self.autoscale_button.config(bg = 'light grey', relief = RAISED)
        else:
            self.autoscale_button.config(bg = 'gold', relief = SUNKEN)
        self.func.autoscale()
                        
    def ratio_view_toggle(self):
        if  self.ratio_view_button['relief'] == SUNKEN:
            self.ratio_view_button.config(bg = 'light grey', relief = RAISED)
        else:
            self.ratio_view_button.config(bg = 'gold', relief = SUNKEN)
        self.func.ratio_view()
        
    # handle the button appearance and handles openloop functionality
    def open_loop_state(self):
        if self.open_loop_stop is not None:
            self.open_loop_button.config(command = self.open_loop,
                                         relief = RAISED, bg = 'light grey')
            self.root.after_cancel(self.open_loop_stop)
    
    def open_loop(self):
        self.open_loop_button.config(command = self.open_loop_state,
                                     relief = SUNKEN, bg = 'gold')
        self.func.open_loop_function()
        self.open_loop_stop = self.root.after(1 , self.open_loop)
    
    def quit_button(self):
        self.root.destroy()
        self.root.quit()
        
    
        
                    