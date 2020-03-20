## creating GUI
from tkinter import *
import numpy as np #https://scipy-lectures.org/intro/numpy/operations.html
from tkinter import messagebox
import os

#used for serial comm with arduino
import serial


#saving data to csv
import pandas as pd
import csv

### plotting data 
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
import matplotlib.pyplot as plt

#only needed for ADC and acquire with RPI
from time import sleep
import time
import RPi.GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

### setup GPIO for Spectrometer output
GPIO.setwarnings(False)    # Ignore warning for now
GPIO.setmode(GPIO.BOARD)   # Use physical pin numbering
Spec_trig = 3
Spec_ST = 13
Spec_Clk = 11
White_LED = 7
Laser_404 = 10
Spec_Video = 12
Spec_channels = 288
data = np.empty(Spec_channels, dtype = int)
wavelength = np.empty(Spec_channels, dtype = float)

#GPIO.setup(Spec_trig, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Spec_ST, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(Spec_Clk, GPIO.OUT, initial=GPIO.LOW)
#GPIO.setup(Spec_Video, GPIO.OUT, initial=GPIO.LOW)
#GPIO.setup(Laser_404, GPIO.OUT, initial=GPIO.LOW)
#GPIO.setup(White_LED, GPIO.OUT, initial=GPIO.LOW)
#delay_time = 0.0000001#
# Hardware SPI configuration:
SPI_PORT   = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

#Full screen for RPi touchscreen (True) or False for others






# Create main window with all neccassary buttons and plot
class Main_GUI:
    def __init__(self, master):
        self.master = root
        root.title("ESS System Interface")
        global full_screen
        full_screen = False
        if full_screen == True:
            root.attributes('-fullscreen', True) # fullscreen on touchscreen
        else:
            root.geometry('800x480') # actual size of RPi touchscreen
        root.configure(bg= "sky blue")
        # help with button layout
        right_corner = 690
        left_corner = 0
        
        # setup Serial port
        port = "/dev/ttyACM0"
        port2 = "/dev/ttyACM1"
        try:
            ser = serial.Serial(port, baudrate = 115200, timeout = 2)
        except other_serial:
            ser = serial.Serial(port2, baudrate = 115200, timeout = 2)
        except:
            messagebox.showerror("Error", "Could Not Connect to Spectrometer")
        # allow serial port to initialize for spectromter
        sleep(1.5)

        # initialize file for saving values
        global filename
        global foldername
        global settings_file
        global reference_file
        global wavelength
        global pixel
        pixel = np.arange(1,289)
        A = 315.2446842
        B1 = 2.688494791
        B2 = -8.964262020*(10**-4)
        B3 = -1.03088017*(10**-5)
        B4 = 2.083514791*(10**-8)
        B5 = -1.290505933*(10**-11)
        wavelength = A + B1*pixel + B2*pixel**2 + B3*pixel**3 + B4*pixel**4+ B5*pixel**5
        print(wavelength)
        test = True
        if test == True:
            filename = '/home/pi/Desktop/Spectrometer/file.csv'
            reference_file = '/home/pi/Desktop/Spectrometer/ref.csv'
            try:
                open(filename, 'x')
                pixel_ref = np.arange(288).reshape(288,1)
                open(filename, 'w')
                np.savetxt(filename, pixel_ref, fmt="%d", delimiter=",")
            except:
                pixel_ref = np.arange(288).reshape(288,1)
                open(filename, 'w')
                np.savetxt(filename, pixel_ref, fmt="%d", delimiter=",")
            try:
                open(reference_file, 'x')
            except:
                #overwrite previous reference file
                pixel_ref = np.arange(288).reshape(288,1)
                open(reference_file, 'w')
                np.savetxt(reference_file, pixel_ref, fmt="%d", delimiter=",")
            
        
        #create spectrometer folder to store all data and settings
        folder_path = '/home/pi/Desktop/Spectrometer'
        folder_settings = '/home/pi/Desktop/Spectrometer/settings'
        try:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
        except:
            messagebox.showinfo("Directory", "All Files will be stored in folder:\n            Spectrometer")
        else:
            if not os.path.exists(folder_settings):
                os.makedirs(folder_settings)
        
        #create settings and acquire folders to hold temporary data
        settings_file = '/home/pi/Desktop/Spectrometer/settings/settings.csv'
        # intialize fake file to save just acquire values
        file_acquire = '/home/pi/Desktop/Spectrometer/settings/acquire.csv'
        # create acquire pseudo file if not already within spectrometer folder
        try:
            open_acquire_file = open(file_acquire, 'x')
        except:
            open_acquire_file = open(file_acquire, 'a')
        
        # intialize arduino with one pseudo read
        ser.write(b"read\n")
        data = ser.readline()
        
        # Check if there is already a settings folder,
        #otherwise create new with default settings into Spec Folder
        try:
            open(settings_file, 'r')
        except:
            open(settings_file, 'x')
            settings_open = open(settings_file, 'w', newline = '')
            csv_row = [('Settings', ''),('pulse',1),('pulse_rate',60),\
                   ('integration_time',100),('dark_subtract',1),\
                   ('lamp_voltage',1000), ('autopulse_threshold',52000),\
                   ('max_autopulse_number',10),('smoothing_half_width',2),\
                   ('min_wavelength',300),('max_wavelength',900)]
            with settings_open:
                csv_writer = csv.writer(settings_open, delimiter = ',')
                csv_writer.writerows(csv_row)

        def acquire_save():
            plt.clf()
            settings_open = open(settings_file, 'r')
            csv_reader = csv.reader(settings_open, delimiter=',')
            settings = list(csv_reader)
            integ_time = int(settings[3][1])
            integ = b"set_integ %0.6f\n" % integ_time
            ser.write(integ)
            sleep(1)
            ser.write(b"read\n")
            try:
                data = ser.readline()
                data_array = np.array([int(d) for d in data.split(b",")])
                dummy = pd.read_csv(filename, header = None)
                data_saved = np.column_stack([dummy, data_array])
                np.savetxt(filename, data_saved, fmt="%d", delimiter=",")
                pixel = range(0,288,1)
                data = pd.read_csv(filename, header = None)
                ref = pd.read_csv(reference_file, header = None)
                for col in range(1, len(data.columns),1):
                    try:
                        plt.plot(wavelength,data.loc[:,col])
                        plt.plot(wavelength,ref[:,1])
                    except:
                        plt.plot(wavelength,data.loc[:,col])
                fig.canvas.draw()
                '''
                data = ser.readline()
                data_array = np.array([int(d) for d in data.split(b",")])
                dummy = pd.read_csv(filename, header = None)
                data_saved = np.column_stack([dummy, data_array])
                np.savetxt(filename, data_saved, fmt="%d", delimiter=",")
                pixel = range(0,288,1)
                data = pd.read_csv(filename, header = None)
                ref = pd.read_csv(reference_file, header = None)
                for col in range(1, len(data.columns),1):
                    plt.plot(pixel,data.loc[:,col])
                plt.plot(pixel,ref[:,1], '--')
                fig.canvas.draw()
                '''
            except:
                messagebox.showerror("Error", "No File Path Entered, Open New file with Open/New Experiment")
        
                
                        
        def acquire():
            # open settings and send integ time to spectrometer 
            settings_open = open(settings_file, 'r')
            csv_reader = csv.reader(settings_open, delimiter=',')
            settings = list(csv_reader)
            integ_time = int(settings[3][1])
            integ = b"set_integ %0.6f\n" % integ_time
            ser.write(integ)
            sleep(1)
            # tell spectromter to send data 
            ser.write(b"read\n")
            #read data and save to pseudo csv to plot 
            data = ser.readline()
            data = np.array([int(p) for p in data.split(b",")])
            # save current spectra then draw on canvas 
            np.savetxt(file_acquire, data, fmt="%d", delimiter=",")
            pixel = range(0,288,1)
            data = pd.read_csv(file_acquire, header = None)
            plt.plot(wavelength,data)
            plt.ylabel('a.u.')
            plt.xlabel('Wavelength (nm)')
            fig.canvas.draw()
                               
        #Plot all saved spectra 
        def plot_all():
            # Clear figure from any acquired (unsaved) spectra
            plt.clf()
            # plot the saved spectra from your file
            #(if there is none just draw a blank canvas 
            try:
                pixel = range(0,288,1)
                data = pd.read_csv(filename, header = None)
                for col in range(1, len(data.columns),1):
                    plt.plot(wavelength,data.loc[:,col])
                data = pd.read_csv(reference_file, header = None)
                plt.plot(pixel,data, '--')
                fig.canvas.draw()
            except:
                fig.canvas.draw()
        
        #Clear canvas
        def clear():
            plt.clf()
            fig.canvas.draw()
            
        def ratio_view():
            plt.clf()
            fig.canvas.draw()
            #try:
            pixel = range(0,288,1)
            data_ratio = pd.read_csv(filename, header = None)
            print(data_ratio)
            data_np = data_ratio.to_numpy()
            #Import reference and convert to numpy and divide by data
            ref_pd = pd.read_csv(reference_file, header = None)
            ref= ref_pd.to_numpy()
            print(len(data_ratio.columns))
           
            for col in range(0, len(data_ratio.columns),1):
                for column in range(0,len(ref_pd.columns),1):
                    #ratio = np.true_divide(ref, data_np[:,col])
                    if col > 0:
                        ratio = np.true_divide(data_np[:,col],ref[:, column])
                        plt.plot(wavelength,ratio)
            plt.ylabel('Reflectance')
            plt.xlabel('Pixel value')
            plt.ylim((0,1.2))
            fig.canvas.draw()
                #except:
                #messagebox.showerror("Error", "No Reference Spectrum Taken! Add Reference Spectrum to use Ratio-View")
                
        def reference():
            # open settings and send integ time to spectrometer 
            settings_open = open(settings_file, 'r')
            csv_reader = csv.reader(settings_open, delimiter=',')
            settings = list(csv_reader)
            integ_time = int(settings[3][1])
            integ = b"set_integ %0.6f\n" % integ_time
            ser.write(integ)
            sleep(1)
            # tell spectromter to send data 
            ser.write(b"read\n")
            #read data and save to pseudo csv to plot
            plt.clf()
            data = ser.readline()
            data = np.array([int(p) for p in data.split(b",")])
            # save current spectra then draw on canvas 
            np.savetxt(reference_file, data, fmt="%d", delimiter=",")
            pixel = range(0,288,1)
            ref = pd.read_csv(reference_file, header = None)
            data = pd.read_csv(filename, header = None)
            for col in range(1, len(data.columns),1):
                plt.plot(wavelength,data.loc[:,col])
            plt.plot(wavelength,ref, '--')
            fig.canvas.draw()
              
        ### read in default settings
        settings_open = open(settings_file, 'r')
        csv_reader = csv.reader(settings_open, delimiter=',')
        settings = list(csv_reader)
        pulse = int(settings[1][1])
        pulse_rate = int(settings[2][1])
        integ_time = int(settings[3][1])
        dark_subtract = int(settings[4][1])
        lamp_voltage = int(settings[5][1])
        auto_pulse_threshold = int(settings[6][1])
        auto_pulse_max = int(settings[7][1])
        smoothing_half_width = int(settings[8][1])
        min_wavelength = int(settings[9][1])
        max_wavelength = int(settings[10][1])
        
        #create all the buttons onto to the main window
        # with all their corresponding functions (command)
        self.quit_button = Button(root, text = "Quit", fg = 'Red', command = root.destroy, width = 10, height = 3)
        self.quit_button.place(x = right_corner, y = 2)
        
        self.help_button = Button(root, text = "Help", fg = 'black', command = self.help_window, width = 10, height = 3)
        self.help_button.place(x = right_corner- 110, y = 2)
        
        self.settings_button = Button(root, text = "Settings", fg = 'black', command = self.settings_window, width = 10, height = 3)
        self.settings_button.place(x = right_corner - 220, y = 2)
        
        self.save_spectra_button = Button(root, text = "Save as Spectra", wraplength = 80, fg = 'black', command = self.save_spectra, width = 10, height = 3)
        self.save_spectra_button.place(x = right_corner - 345, y = 2)
        
        self.save_reference_button = Button(root, text = "Save as Reference", wraplength = 80, fg = 'black', command = reference, width = 10, height = 3)
        self.save_reference_button.place(x = right_corner - 455, y = 2)
        
        self.open_new_button = Button(root, text = "Open/New Experiment", wraplength = 80, fg = 'black', command = self.key_pad, width = 10, height = 3)
        self.open_new_button.place(x = right_corner- 580, y = 2)
        
        self.open_loop_button = Button(root, text = "Open Loop", fg = 'black', command = self.open_loop, width = 10, height = 3)
        self.open_loop_button.place(x = right_corner - right_corner, y = 2)
        
        self.acquire_button = Button(root, text = "Acquire", wraplength = 80, fg = 'black', command = acquire, width = 10, height = 3)
        self.acquire_button.place(x = left_corner, y = 105)
        
        self.acquire_save_button = Button(root, text = "Acquire and Save", fg = 'black', wraplength = 80, command = acquire_save, width = 10, height = 3)
        self.acquire_save_button.place(x = left_corner, y = 170)
        
        self.autorange_button = Button(root, text = "Auto-Range", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 3)
        self.autorange_button.place(x = left_corner, y = 235)
        
        self.sequence_button = Button(root, text = "Sequence", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 3)
        self.sequence_button.place(x = left_corner, y = 340)
        
        self.sequence_button = Button(root, text = "Sequence and Save", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 3)
        self.sequence_button.place(x = left_corner, y = 405)
        
        self.smoothing_button = Button(root, text = "Smoothing", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 2)
        self.smoothing_button.place(x = left_corner + 110, y = 430)
        
        self.ratio_view_button = Button(root, text = "Ratio View", fg = 'black', wraplength = 80, command = ratio_view, width = 10, height = 2)
        self.ratio_view_button.place(x = left_corner + 220, y = 430)
        
        self.zoom_button = Button(root, text = "Zoom", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 2)
        self.zoom_button.place(x = left_corner + 345, y = 430)
        
        self.plot_all_button = Button(root, text = "Plot All", fg = 'black', wraplength = 80, command = plot_all, width = 10, height = 2)
        self.plot_all_button.place(x = left_corner + 455, y = 430)
        
        self.clear_button = Button(root, text = "Clear", fg = 'black', wraplength = 80, command = clear, width = 10, height = 2)
        self.clear_button.place(x = left_corner + 565, y = 430)
        
        self.add_remove_button = Button(root, text = "Add/Remove Plots", fg = 'black', wraplength = 85, command = self.acquire, width = 10, height = 2)
        self.add_remove_button.place(x = left_corner + 690, y = 430)
        
        ## Graphing Frame and fake plot
        self.graph_frame = Frame(root, width = 675, height =355, background = "white")
        self.graph_frame.place(x = 115, y = 70)
    
        #fig = Figure(figsize=(6.75, 3.2), dpi=100)
        fig = plt.figure(figsize = (6.75, 3.2), dpi = 100)
        pixel = range(0, 300, 1)
        
        
        try:
            df = pd.read_csv(file_acquire, header = None)
        except:
            x = 1
            
        
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)  # A tk.DrawingArea.
        
        canvas.get_tk_widget().pack()
        fig.canvas.draw()
        try:
            df = pd.read_csv(file_acquire, header = None)
            fig.canvas.draw()
        except:
            plt.clf()
            fig.canvas.draw()
        # create toolbar for figure
        toolbar = NavigationToolbar2Tk(canvas, self.graph_frame)
        toolbar.update()
        canvas.get_tk_widget().pack()
        sleep(1)
        
        
              
             
              
    def settings_window(self):
        self.setting_window = Toplevel(root)
        self.setting_window.title('Settings')
        self.setting_window.configure(bg= "sky blue")
        if full_screen == True:
            self.setting_window.attributes('-fullscreen', True) # Fullscreen on touch screen
        else:
            self.setting_window.geometry('800x480') # PC size of the touch screen window
        
        quit_button = Button(self.setting_window, text = "Quit", fg = 'Red', command = self.setting_window.destroy, width = 10, height = 3)
        quit_button.grid(row= 0, column = 1)
        
        save_button = Button(self.setting_window, text = "Save", fg = 'Green', command = self.settings_write, width = 10, height = 3)
        save_button.grid(row = 0, column = 2)
        
        default_button = Button(self.setting_window, text = "Reset To Default Settings", command = self.default, width = 10, height = 3, wraplength = 85)
        default_button.grid(row = 0, column = 3)
        
        numpad_button = Button(self.setting_window, text = "Open Numpad", command = self.Num_Pad, width = 10, height = 3).grid(row = 0, column = 0)
        
        #read in settings
        settings_open = open(settings_file, 'r')
        csv_reader = csv.reader(settings_open, delimiter=',')
        settings = list(csv_reader)
        pulse = int(settings[1][1])
        pulse_rate = int(settings[2][1])
        integ_time = int(settings[3][1])
        dark_subtract = int(settings[4][1])
        lamp_voltage = int(settings[5][1])
        auto_pulse_threshold = int(settings[6][1])
        auto_pulse_max = int(settings[7][1])
        smoothing_half_width = int(settings[8][1])
        min_wavelength = int(settings[9][1])
        max_wavelength = int(settings[10][1])
        
        # Start to create Frames for settings window
        
        # Single Acquisition Frame
        single_acquisition_frame = Frame(self.setting_window, width = 340, height =120, background = "white")
        single_acquisition_frame.place(x = 440, y = 5)
        single_acquisition_label = Label(single_acquisition_frame, text = "Single Acquisition Settings", fg = "Black", bg= "white").grid(row = 0, column = 0, columnspan = 2)
        self.acquisition_number = IntVar()
        self.acquisition_number.set(pulse)
        acq_number_button = Button(single_acquisition_frame, text = "Pulses:", fg = "Black", bg = "white", command = lambda: self.Num_Pad(1))
        acq_number_button.grid(row = 1, column = 0, pady = 2, padx = 3)
        acq_number_entry = Entry(single_acquisition_frame, textvariable = self.acquisition_number, width = 8).grid(row = 1, column = 1, padx = 8)
        
        self.pulse_rate = IntVar()
        self.pulse_rate.set(pulse_rate)
        pulse_rate_button = Button(single_acquisition_frame, text = "Pulse Rate (Hz):", fg = "Black", bg = "white", command = lambda: self.Num_Pad(2))
        pulse_rate_button.grid(row = 2, column = 0, pady = 2, padx = 3)
        pulse_rate_entry = Entry(single_acquisition_frame, textvariable = self.pulse_rate, width = 8).grid(row = 2, column = 1, padx = 8)
  
        self.integ_time = IntVar()
        self.integ_time.set(integ_time)
        integ_time_button = Button(single_acquisition_frame, text = "Integration Time (usec):", fg = "Black", bg = "white",\
                                   command = lambda: self.Num_Pad(3))
        integ_time_button.grid(row = 3, column = 0, pady = 2, padx = 3)
        integ_time_entry = Entry(single_acquisition_frame, textvariable = self.integ_time, width = 8).grid(row = 3, column = 1, padx = 8)
        
        self.dark_subtract = IntVar()
        self.dark_subtract.set(dark_subtract)
        dark_subtraction_entry = Checkbutton(single_acquisition_frame, text = "Use Dark Subtraction", variable = self.dark_subtract).grid(row = 4, columnspan = 2)
        
        # Lamp Frame
        lamp = Frame(self.setting_window, width = 340, height = 75, background = "white")
        lamp.place(x = 440, y = 165)
        lamp_label = Label(lamp, text = "Lamp", fg = "Black", bg = "White").grid(row = 0, column = 0, columnspan = 2)
        self.lamp_voltage = IntVar()
        self.lamp_voltage.set(lamp_voltage)
        lamp_entry_button= Button(lamp, text = "Lamp Voltage (volts):", fg = "Black", bg = "white", command = lambda: self.Num_Pad(5))
        lamp_entry_button.grid(row = 1, column = 0, pady = 2, padx = 3)
        lamp_entry = Entry(lamp, textvariable = self.lamp_voltage, width = 8).grid(row = 1, column = 1, padx = 8)
        
        #AutoRange Frame 
        Auto_range_frame = Frame(self.setting_window, width = 340, height = 100, background = "white")
        Auto_range_frame.place(x = 440, y = 230)
        auto_range_label = Label(Auto_range_frame, text = "Auto-Ranging:", fg = "Black", bg = "white").grid(row = 0, column = 0, columnspan = 2)
        self.threshold = IntVar()
        self.threshold.set(auto_pulse_threshold)
        autopulse_entry_button = Button(Auto_range_frame, text = "AutoPulse Threshold(counts):", fg = "Black", bg = "white", command = lambda: self.Num_Pad(6))
        autopulse_entry_button.grid(row = 1, column = 0, pady = 2, padx = 3)
        autopulse_entry = Entry(Auto_range_frame, textvariable = self.threshold, width = 8).grid(row = 1, column = 1, padx = 8)
        
        self.max_pulses = IntVar()
        self.max_pulses.set(auto_pulse_max)
        max_pulses_entry_button = Button(Auto_range_frame, text = "Max # of Pulses:", fg = "Black", bg = "white", command = lambda: self.Num_Pad(7))
        max_pulses_entry_button.grid(row = 2, column = 0)
        max_pulses_entry = Entry(Auto_range_frame, textvariable = self.max_pulses, width = 8).grid(row = 2, column = 1, padx = 8)
        
        # Graphing settings frame
        graph_frame = Frame(self.setting_window, width = 340, height = 200, background = "white")
        graph_frame.place(x = 440, y = 340)
        auto_range_label = Label(graph_frame, text = "Smoothing Half-Width (pixels):", fg = "Black", bg = "white").grid(row = 0, column = 0, columnspan = 2)
        self.smoothing = IntVar()
        self.smoothing.set(smoothing_half_width)
        smoothing_entry_button = Button(graph_frame, text = "AutoPulse Threshold(counts):", fg = "Black", bg = "white", command = lambda: self.Num_Pad(8))
        smoothing_entry_button.grid(row = 1, column = 0, pady = 2, padx = 3)
        smoothing_entry = Entry(graph_frame, textvariable = self.smoothing, width = 8).grid(row = 1, column = 1, padx = 8)
        
        self.min_wavelength = IntVar()
        self.min_wavelength.set(min_wavelength)
        min_Wavelength_entry_button = Button(graph_frame, text = "Min-Wavelength:", fg = "Black", bg = "white", command = lambda: self.Num_Pad(9))
        min_Wavelength_entry_button.grid(row = 2, column = 0, pady = 2, padx = 3)
        min_Wavelength_entry = Entry(graph_frame, textvariable = self.min_wavelength, width = 8).grid(row = 2, column = 1, padx = 8)
        
        self.max_wavelength = IntVar()
        self.max_wavelength.set(max_wavelength)
        max_wavelength_entry_button = Button(graph_frame, text = "Max-Wavelength:", fg = "Black", bg = "white", command = lambda: self.Num_Pad(10))
        max_wavelength_entry_button.grid(row = 3, column = 0, pady = 2, padx = 3)
        max_wavelength_entry = Entry(graph_frame, textvariable = self.max_wavelength, width = 8).grid(row = 3, column = 1, padx = 8)
        
    def default(self):
        self.acquisition_number.set('1')
        self.pulse_rate.set('60')
        self.integ_time.set('100')
        self.dark_subtract.set('1')
        self.lamp_voltage.set('1000')
        self.threshold.set('52000')
        self.smoothing.set('2')
        self.min_wavelength.set('300')
        self.max_wavelength.set('900')
        settings_open = open(settings_file, 'r')
        csv_reader = csv.reader(settings_open, delimiter=',')
        settings = list(csv_reader)
        settings[1][1]  = int(self.acquisition_number.get())
        settings[2][1] = int(self.pulse_rate.get())
        settings[3][1] = int(self.integ_time.get())
        settings[4][1] = int(self.dark_subtract.get())
        settings[5][1] = int(self.lamp_voltage.get())
        settings[6][1] = int(self.threshold.get())
        settings[7][1]= int(self.max_pulses.get())
        settings[8][1] = int(self.smoothing.get())
        settings[9][1] = int(self.min_wavelength.get())
        settings[10][1] = int(self.max_wavelength.get())
        
        settings_open = open(settings_file, 'w')
        with settings_open:
           csv_writer = csv.writer(settings_open, delimiter = ',')
           csv_writer.writerows(settings)
        #print(settings)
        
    # setup number pad as toplevel window 
    def Num_Pad(self, button_number):
        
        #number pad attributes
        num = StringVar()  # variable for extracting entry number
        self.numpad = Toplevel(self.setting_window)
        self.numpad.title('Input pad')
        self.numpad.geometry('230x300')
        self.numpad_frame = Frame(self.numpad, width = 230, height = 15).grid(row = 1, column = 0, columnspan = 3)
        number_entry = Entry(self.numpad, textvariable = num, justify = CENTER).grid(row = 1, column = 0, columnspan = 3)
        
        def button_click(number):
            current = num.get() # save current entry value
            num.set('') # erase entry 
            num.set(str(current) + str(number)) # rewrite entry with additional values 
    
        def num_pad_delete():
            num.set('') # erase current entry 
        
        def num_pad_save(button_number):
            self.setting_window.destroy()
            settings_open = open(settings_file, 'r')
            csv_reader = csv.reader(settings_open, delimiter=',')
            settings = list(csv_reader)
            # read in settings to particular button ID on settings page
            settings[button_number][1]  = int(num.get())
            #write settings to csv file
            settings_open = open(settings_file, 'w')
            with settings_open:
               csv_writer = csv.writer(settings_open, delimiter = ',')
               csv_writer.writerows(settings)
            self.numpad.destroy()
            self.settings_window()
            
        btn_list = [
        '7', '8', '9',
        '4', '5', '6',
        '1', '2', '3',
        '0', 'Del', 'OK']
    
        r = 2
        c = 0
        n = 0
    
        btn = list(range(len(btn_list)))
        
        for label in btn_list:
            btn[n] = Button(self.numpad, text = label, width = 6, height = 3)
            btn[n].grid(row = r, column = c)
            n+= 1
            c+= 1
            if c>2:
                c = 0
                r+= 1
        btn[0].configure(command = lambda: button_click(7))
        btn[1].configure(command = lambda: button_click(8))
        btn[2].configure(command = lambda: button_click(9))
        btn[3].configure(command = lambda: button_click(4))
        btn[4].configure(command = lambda: button_click(5))
        btn[5].configure(command = lambda: button_click(6))
        btn[6].configure(command = lambda: button_click(1))
        btn[7].configure(command = lambda: button_click(2))
        btn[8].configure(command = lambda: button_click(3))
        btn[9].configure(command = lambda: button_click(0))
        btn[10].configure(command = num_pad_delete)
        btn[11].configure(command = lambda: num_pad_save(button_number))
        
        
    def settings_write(self):
        settings_open = open(settings_file, 'r')
        csv_reader = csv.reader(settings_open, delimiter=',')
        settings = list(csv_reader)
        settings[1][1]  = int(self.acquisition_number.get())
        settings[2][1] = int(self.pulse_rate.get())
        settings[3][1] = int(self.integ_time.get())
        settings[4][1] = int(self.dark_subtract.get())
        settings[5][1] = int(self.lamp_voltage.get())
        settings[6][1] = int(self.threshold.get())
        settings[7][1]= int(self.max_pulses.get())
        settings[8][1] = int(self.smoothing.get())
        settings[9][1] = int(self.min_wavelength.get())
        settings[10][1] = int(self.max_wavelength.get())
        
        settings_open = open(settings_file, 'w')
        with settings_open:
           csv_writer = csv.writer(settings_open, delimiter = ',')
           csv_writer.writerows(settings)
        print(settings)
        self.setting_window.destroy()
        
    def key_pad(self):
        self.keypad = Toplevel(root)
        path = '/home/pi/Desktop/Spectrometer/'
        key = StringVar()
        
        self.keypad.title('Input New FileName into entry box')
        self.keypad.geometry('520x220')
        keypad_frame = Frame(self.keypad)
        keypad_frame.grid(row = 1, column = 0, columnspan = 10)
        key_entry = Entry(keypad_frame, textvariable =key, justify = CENTER)
        key_entry.grid(row = 1, column = 0, columnspan = 10)
        
        def press(letter):
             current = key.get()
             key.set('')
             key.set(str(current) + str(letter))

        def key_pad_delete():
            key.set('')
        
        def key_pad_save():
            try:
                global filename
                global reference_file
            
                filename = str(path + key.get())
                if not os.path.exists(filename):
                    os.makedirs(filename)
                reference_file = str(filename +'/' + key.get() + '_ref.csv')
                filename = str(filename +'/' + key.get() + '.csv')
                print(filename)
                open(filename, 'x')
                open(reference_file,'x')
                pixel_ref = np.arange(288).reshape(288,1)
                open(filename, 'w')
                np.savetxt(filename, pixel_ref, fmt="%d", delimiter=",")
                self.keypad.destroy()
                
            except:
                self.keypad.destroy()
                messagebox.showerror("Error", "File Name already Exists! Please enter New Filename")
               
                
                
             
            
        btn_list = [
        '1', '2', '3', '4', '5', '6','7', '8', '9', '0',
        'Q', 'W', 'E','R', 'T', 'Y', 'U', 'I', 'O','P',
        'A', 'S', 'D','F', 'G', 'H', 'J', 'K', 'L','Del',
        'Z', 'X', 'C','V', 'B', 'N', 'M', '_', '-','OK']
    
        r = 2
        c = 0
        n = 0
    
        btn = list(range(len(btn_list)))
        
        for label in btn_list:
            btn[n] = Button(self.keypad, text = label, width = 3, height = 2)
            btn[n].grid(row = r, column = c)
            n+= 1
            c+= 1
            if c>9:
                c = 0
                r+= 1
        # first row commands
        btn[0].configure(command = lambda: press(1))
        btn[1].configure(command = lambda: press(2))
        btn[2].configure(command = lambda: press(3))
        btn[3].configure(command = lambda: press(4))
        btn[4].configure(command = lambda: press(5))
        btn[5].configure(command = lambda: press(6))
        btn[6].configure(command = lambda: press(7))
        btn[7].configure(command = lambda: press(8))
        btn[8].configure(command = lambda: press(9))
        btn[9].configure(command = lambda: press(0))
        # second row commands
        btn[10].configure(command = lambda: press('q'))
        btn[11].configure(command = lambda: press('w'))
        btn[12].configure(command = lambda: press('e'))
        btn[13].configure(command = lambda: press('r'))
        btn[14].configure(command = lambda: press('t'))
        btn[15].configure(command = lambda: press('y'))
        btn[16].configure(command = lambda: press('u'))
        btn[17].configure(command = lambda: press('i'))
        btn[18].configure(command = lambda: press('o'))
        btn[19].configure(command = lambda: press('p'))
        #third row commands
        btn[20].configure(command = lambda: press('a'))
        btn[21].configure(command = lambda: press('s'))
        btn[22].configure(command = lambda: press('d'))
        btn[23].configure(command = lambda: press('f'))
        btn[24].configure(command = lambda: press('g'))
        btn[25].configure(command = lambda: press('h'))
        btn[26].configure(command = lambda: press('j'))
        btn[27].configure(command = lambda: press('k'))
        btn[28].configure(command = lambda: press('l'))
        btn[29].configure(command = key_pad_delete)

        #fourth row commandxs
        btn[30].configure(command = lambda: press('z'))
        btn[31].configure(command = lambda: press('x'))
        btn[32].configure(command = lambda: press('c'))
        btn[33].configure(command = lambda: press('v'))
        btn[34].configure(command = lambda: press('b'))
        btn[35].configure(command = lambda: press('n'))
        btn[36].configure(command = lambda: press('m'))
        btn[37].configure(command = lambda: press('_'))
        btn[38].configure(command = lambda: press('-'))
        btn[39].configure(command = key_pad_save)
            
    def help_window(self):
        print(acquisition_number)
    def save_spectra(self):
        print("saving spectra needed to be added later")
    def save_reference(self):
        print("saving reference needed to be added")
    def open_new(self):
        self.open_new = Toplevel(root)
        self.open_new.title('Enter your new filename in the entry box')
        self.open_new.configure(bg= "sky blue")
        
        
        
        
        
    def open_loop(self):
        print("open loop needs to be added")
          
    def acquire(self):
        print("HELLO")
        #ser.write(b"set_integ 500\n")
        #sleep(2)
        '''
        settings_open = open('/home/pi/Desktop/BMO Lab/settings.csv', 'r')
        csv_reader = csv.reader(settings_open, delimiter=',')
        settings = list(csv_reader)
        integ_time = int(settings[3][1])
        integ = b"set_integ %0.6f\n" % integ_time
        ser.write(integ)
        sleep(1)
        ser.write(b"read\n")
        data = ser.readline()
        data = np.array([int(p) for p in data.split(b",")])
        np.savetxt(file_acquire, data, fmt="%d", delimiter=",")
        pixel = range(0,288,1)
        #plt.plot(pixel, data)
        #plt.show()
        plt.clf()
        data = pd.read_csv(file_acquire, header = None)
        plt.plot(pixel,data)
        '''
        '''
        startall = time.time()
        
        GPIO.setwarnings(False)    # Ignore warning for now
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(Spec_ST, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(Spec_Clk, GPIO.OUT, initial=GPIO.LOW)
          
         #self.acquire_button.configure(state = 'disable')
        settings_open = open('/home/pi/Desktop/BMO Lab/settings.csv', 'r')
        csv_reader = csv.reader(settings_open, delimiter=',')
        settings = list(csv_reader)
        integ_micros = int(settings[3][1])/1000000
        
        delay_time_clock = 0
        GPIO.output(Spec_Clk, GPIO.HIGH)
        sleep(delay_time_clock)
        GPIO.output(Spec_Clk, GPIO.LOW)
        GPIO.output(Spec_ST, GPIO.HIGH)
        sleep(delay_time_clock)
        
        start_clock3 = time.time()
        for x in range(0, 3, 1):
            
            GPIO.output(Spec_Clk, GPIO.HIGH)
            sleep(delay_time_clock)
            GPIO.output(Spec_Clk, GPIO.LOW)
            sleep(delay_time_clock)
        end_clock3 = time.time()
            
        start = 0
        
        elapsed = 0
       
        
        x = 0
        integ_blocks = int(integ_micros/((0.000025)))
        print(integ_blocks)
        start_elapsed = time.time()
        for x in range(0,integ_blocks,1):
            
            GPIO.output(Spec_Clk, GPIO.HIGH)
            sleep(delay_time_clock)
            GPIO.output(Spec_Clk, GPIO.LOW)
            sleep(delay_time_clock)
            elapsed = time.time()-start

        end_elapsed = time.time()
        
        GPIO.output(Spec_ST, GPIO.LOW)
        start_clock48 = time.time()
        for x in range(0,48,1):
            GPIO.output(Spec_Clk, GPIO.HIGH)
            sleep(delay_time_clock)
            GPIO.output(Spec_Clk, GPIO.LOW)
            sleep(delay_time_clock)
        end_clock48 = time.time()
        start_clock1 = time.time()
        for x in range(0,40,1):
            GPIO.output(Spec_Clk, GPIO.HIGH)
            sleep(delay_time_clock)
            GPIO.output(Spec_Clk, GPIO.LOW)
            sleep(delay_time_clock)
        end_clock1 = time.time()
    
        start1 = time.time()
        for x in range(0,Spec_channels,1):
            
            data[x] = mcp.read_adc(2)
            
            GPIO.output(Spec_Clk, GPIO.HIGH)
            sleep(delay_time_clock)
            GPIO.output(Spec_Clk, GPIO.LOW)
            sleep(delay_time_clock)
        end1 = time.time()
        print('ADC read takes:', end1-start1, 'Seconds')
        print('40 clock pulses:', end_clock1-start_clock1, 'seconds')
        print('3 clock pulses:', end_clock3 - start_clock3, 'seconds')
        print('48 clock pulses:', end_clock48 - start_clock48, 'seconds')
        print('integ_elapsed: ', end_elapsed-start_elapsed)
        
        
        sleep(1)
        pixel = range(0,288,1)
        plt.plot(pixel, data)
        plt.show()  
        GPIO.cleanup()
        #self.acquire_button.configure(state = 'enable')
        '''
    
    
    def acquire_save(self):
       print('OK')
    def auto_range(self):
        print("autorange needs to be added")
    def sequence(self):
        print("Sequence needs to be added")
        
 

# Actually create window with all the above functionality
root = Tk()
my_gui = Main_GUI(root)
root.mainloop()

