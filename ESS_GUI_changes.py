## tkinter used for widgets that make up GUI framework
from tkinter import *
import numpy as np #https://scipy-lectures.org/intro/numpy/operations.html
from tkinter import messagebox

from tkinter.filedialog import askopenfilename
import tkinter.font as font

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

#only needed for external ADC and acquire with RPI
#import RPi.GPIO as GPIO
#import Adafruit_GPIO.SPI as SPI
#import Adafruit_MCP3008

''' _________ variable listing and meaning ___________
ser = serial port opening with specified baudrate and timeout

scan number = ID number for labeling acquired/saved data
reference number = ID number for labeling saved reference data

data_headers = blank array to hold headers to be used for add/remove of plots
data_headers_idx = helps to index headers array to save values for later use
reference_ratio = Allows for selection of reference in the add/remove listbox
reference_ratio_idx = index the reference that has been selected to save that location in the listbox
ref = the actual data array that is used as the selected reference

df = data frame to store all data that will be saved to csv files (append new data to df)
df_seq = data frame to store sequence data and written to sequence_file (below)

settings_file = csv file were all settings are stored and read from for each read
save_file = csv file for saving acquired data
seqeunce_file = csv to save sequence data, seperate file name to differentiate data type

# ________________ Function listing and description ________________________
class Main_GUI = the main GUI class that holds all attributes for saving
                 selecting and visualising the data acquired by spectrometers

settings_read = allows for reading of settings CSV file and saves to an array
                (settings[x][1] is the location in the CSV that the value is located)
settings_write = write the settings array to the settings CSV file

dark_subtract_func = used for dark subtraction to make acquire functions a little cleaner,
                     takes one measurement with zero pulses and returns array of data from spectrometer

acquire_avg = used to acquire measurements and take the average of x number given in settings
              given inputs of integ time, # pulses, dark_subtract?, # averages etc,
              takes the measurement with given parameters and returns an array of 288 values
              *** used whenever spectra need to be acquired
              
open_file = allows user to open previous experiment, and scans through it to find the highest scan/reference number
            to allow for more measurments to be added to the file
                ( files cannot be appended if they do not have a reference or scan number (ie a sequence file w diff. headers)
                
autorange = runs a for loop for the acquire avg function and checks the max value of the spectra and if < threshold max \
            then it increases the number of pulses and plots all data

openloop = takes a given number of measurments from the settings and plots all onto the screen, after all spectra have been
            acquired, a listbox pops up onto the screen to allow for saving of those spectra to the current experiment folder


'''

'''
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
'''
# Create main GUI class 
class Main_GUI:
    def __init__(self, master):
        self.master = root
        root.title("ESS System Interface")
        global full_screen
        full_screen = False
        root.tk.call('wm','iconphoto', root._w, PhotoImage(file = "/home/pi/Desktop/BMO_Lab/ESS_png"))
        
        
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
        
        # setup Serial port- these are two possible port names for the arduino attachement
        port = "/dev/ttyUSB0"
        port2 = "/dev/ttyUSB1"
        try:
            self.ser = serial.Serial(port, baudrate = 115200, timeout = 3)
        except:
            self.ser = serial.Serial(port2, baudrate = 115200, timeout =3)
        
        # allow time for serial port to initialize
        sleep(0.5)
        
        #used for saving to csv with headers of increasing ID number
        self.scan_number = 1
        self.reference_number = 1
        self.integ_free = False
        self.open_loop_stop = None
        
        #variables for selection of plots (add/remove)
        self.data_headers_idx = None
        self.data_headers = None
        self.reference_ratio = None
        self.reference_ratio_idx = None
        self.ref = None # reference data array
        
        # Default folder to save into
        self.folder = '/home/pi/Desktop/Spectrometer/'
        self.exp_folder = None
        
        # Images for the helper page
        #self.auto_range_help = PhotoImage(file = '/home/pi/Desktop/BMO_Lab/Auto Range Schematic.png')
        #self.acquire_help = PhotoImage(file = '/home/pi/Desktop/BMO_Lab/Acquire Schematic.png')
        #self.open_loop_help = PhotoImage(file = '/home/pi/Desktop/BMO_Lab/Open Loop Schematic.png')
        #self.sequence_help = PhotoImage(file = '/home/pi/Desktop/BMO_Lab/Open Loop Schematic.png')
        
        self.help_window_image = PhotoImage(file = '/home/pi/Desktop/BMO_Lab/Help_window.png')        
        pixel = np.arange(0,288)
        '''
        A = 335.2446842
        B1 = 2.688494791
        B2 = -8.964262020*(10**-4)
        B3 = -1.03088017*(10**-5)
        B4 = 2.083514791*(10**-8)
        B5 = -1.290505933*(10**-11)
        '''
        #wavelength = pixel
        
        #create spectrometer folder to store all data and settings
        spec_folder_path = '/home/pi/Desktop/Spectrometer'
        spec_folder_settings = '/home/pi/Desktop/Spectrometer/settings'
        
        if not os.path.exists(spec_folder_path):
                os.makedirs(spec_folder_path)
                
        if not os.path.exists(spec_folder_settings):
                os.makedirs(spec_folder_settings)
                
        # create acquire pseudo file if not already within spectrometer folder
        file_acquire = '/home/pi/Desktop/Spectrometer/settings/acquire.csv'
        try:
            #create pseudo files
            open_acquire_file = open(file_acquire, 'x')
        except:
            open_acquire_file = open(file_acquire, 'a')
        
        # intialize arduino with two pseudo read (first two reads always noisy)
        self.ser.write(b'read\n')
        data = self.ser.readline()
        self.ser.write(b'read\n')
        data = self.ser.readline()
        
        # Check if there is already a settings folder,
        #otherwise create new with default settings into Spec Folder
        #create settings file
        self.settings_file = '/home/pi/Desktop/Spectrometer/settings/settings.csv'
        try:
            open(self.settings_file, 'r')
        except: 
            open(self.settings_file, 'x')
            settings_open = open(self.settings_file, 'w', newline = '')
            csv_row = [('Settings', ''),('pulse',1),('pulse_rate',60),\
                   ('integration_time',300),('dark_subtract',1),\
                   ('lamp_voltage',1000), ('autopulse_threshold',4000),\
                   ('max_autopulse_number',10),('smoothing_half_width',2),\
                   ('min_wavelength',300),('max_wavelength',900),\
                   ('Number_of_Averages', 2), ('smoothing', 1),\
                   ('Open Measurements', 5), ('open_pulses', 1),\
                   ('a_0', 308.6578728), ('b_1', 2.71512091),\
                   ('b_2', -1.581742352), ('b_3', -3.64516878),\
                   ('b_4', -6.471720765), ('b_5', 27.41135617),\
                   ('burst_delay', 1.0), ('burst_number', 1),\
                   ('measurement_per_burst_1', 5),('measurement_per_burst_2', 5),\
                   ('measurement_per_burst_3', 5),('measurement_per_burst_4', 5),\
                   ('measurement_per_burst_5', 5),('measurement_per_burst_6', 5),\
                   ('measurement_per_burst_7', 5),('measurement_per_burst_8', 5),\
                   ('measurement_per_burst_9', 5),('measurement_per_burst_10', 5),\
                   ('pulse_per_measurement_1', 1),('pulse_per_measurement_2', 1),\
                   ('pulse_per_measurement_3', 1),('pulse_per_measurement_4', 1),\
                   ('pulse_per_measurement_5', 1),('pulse_per_measurement_6', 1),\
                   ('pulse_per_measurement_7', 1),('pulse_per_measurement_8', 1),\
                   ('pulse_per_measurement_9', 1),('pulse_per_measurement_10', 1)]   # allocate 10 spaces for burst info
            
            with settings_open:
                csv_writer = csv.writer(settings_open, delimiter = ',')
                csv_writer.writerows(csv_row)
                
        # read settings csv and return list of settings
        def settings_read(settings_file):
                settings_open = open(settings_file, 'r')
                csv_reader = csv.reader(settings_open, delimiter=',')
                settings = list(csv_reader)
                return settings
            
        def save_settings_var():
            #read in settings and save them as attributes on main class GUI
            settings = settings_read(self.settings_file)
            self.pulse_number_var = int(settings[1][1])
            self.pulse_rate_var = int(settings[2][1])
            self.integration_time_var = int(settings[3][1])
            self.dark_subtract_var = int(settings[4][1])
            self.lamp_voltage_var = int(settings[5][1])
            self.auto_threshold_var = int(settings[6][1])
            self.max_autopulse_var = int(settings[7][1])
            self.smoothing_half_var = int(settings[8][1])
            self.min_wavelength_var = int(settings[9][1])
            self.max_wavelength_var =  int(settings[10][1])
            self.number_avg_var = int(settings[11][1])
            self.smoothing_var = int(settings[12][1])
            self.step_resolution_var = int(settings[13][1])
            self.step_size_var = int(settings[14][1])
            self.a0_var = float(settings[15][1])
            self.b1_var = float(settings[16][1])
            self.b2_var = float(settings[17][1])
            self.b3_var = float(settings[18][1])
            self.b4_var = float(settings[19][1])
            self.b5_var = float(settings[20][1])
            self.burst_delay_var = float(settings[21][1])
            self.burst_number_var = int(settings[22][1])
        
        # save all settings as attributes to the main class
        # for later use 
        save_settings_var()
        
        def settings_write(settings):
                settings_open = open(self.settings_file, 'w')
                with settings_open:
                   csv_writer = csv.writer(settings_open, delimiter = ',')
                   csv_writer.writerows(settings)
                   
        def dark_subtract_func(smoothing_width):
            settings = settings_read(self.settings_file)
            number_avg = int(settings[11][1])
            integ_time = int(settings[3][1])
            smoothing_used = int(settings[12][1])
            smoothing_width = int(settings[8][1])
            pulses = int(settings[1][1])
            dark_subtract = int(settings[4][1])
            self.ser.write(b"set_integ %0.6f\n" % integ_time)
            self.ser.write(b"pulse 0\n")
            # tell spectromter to send data
            data = 0
            data_dark = 0
            #for x in range(0,1,1): #take scans then average for dark subtract
            self.ser.write(b"read\n")
            #read data and save to pseudo csv to plot
            data_read = self.ser.readline()
            #data = self.ser.read_until('\n', size=None)
            data_temp = np.array([int(p) for p in data_read.split(b",")])
            data_dark = data_temp
            #if x == 0:  # reached number of averages
            #data_dark = data_dark #take average of data and save
            if self.smoothing_var == 1:  # if smoothing is checked smooth array
                dummy = np.ravel(data_dark)
                for i in range(0,len(data_dark)-self.smoothing_width_var,1):
                    data_dark[i] = sum(np.ones(self.smoothing_width_var)
                                       *dummy[i:i+self.smoothing_width_var])/(self.smoothing_width_var)
            return data_dark
                        
            
        def acquire_avg():  # function to acquire data from spectrometer (multiple scans)
            # open settings and send integ time to spectrometer
            settings = settings_read(self.settings_file)
            number_avg = int(settings[11][1])
            integ_time = int(settings[3][1])
            smoothing_used = int(settings[12][1])
            smoothing_width = int(settings[8][1])
            pulses = int(settings[1][1])
            dark_subtract = int(settings[4][1])
            
            if self.dark_subtract_var == 1:
               data_dark = dark_subtract_func(smoothing_width)
            else: 
                data_dark = 0
                
            self.ser.write(b"set_integ %0.6f\n" % self.integration_time_var)
            self.ser.write(b"pulse %d\n" % self.pulse_number_var)
            
            # tell spectromter to send data
            data = 0
            for x in range(0,self.number_avg_var,1): #take scans then average
                self.ser.write(b"read\n")
                data_read = self.ser.readline()
                #data = self.ser.read_until('\n', size=None)
                data_temp = np.array([int(p) for p in data_read.split(b",")])
                data = data + data_temp
                if x == number_avg-1:  # reached number of averages
                    data = data/number_avg #take average of data and save
                    if self.smoothing_var == 1:  # if smoothing is checked smooth array
                        dummy = np.ravel(data)
                        for i in range(0,len(data)-self.smoothing_width_var,1):
                            data[i] = sum(np.ones(self.smoothing_width_var)
                                          *dummy[i:i+smoothing_width_var])/(smoothing_width_var)
            data = data-data_dark        
            return data
            
        def OpenFile():
            
            save_file = askopenfilename(initialdir="/home/pi/Desktop/Spectrometer",
                            filetypes =(("csv file", "*.csv"),("All Files","*.*")),
                            title = "Choose a file.")
            
            try:
                if save_file: # check if file was selected if not dont change experiment file
                    self.save_file = save_file 
                
                    # try to scan through reference and scan number to set to correct value for further saving
                    self.df = pd.read_csv(self.save_file, header = 0)
                    headers = list(self.df.columns.values)
                    #find the scan number from the opened file
                    while True:
                        result = [i for i in headers if i.startswith('Scan_ID %d' %self.scan_number)]
                        if result == []:
                            break
                        self.scan_number = self.scan_number+1 # increment scan number until we reach correct value
                    while True:
                        result = [i for i in headers if i.startswith('Reference %d' %self.reference_number)]
                        if result == []:
                            break
                        self.reference_number = self.reference_number+1
                    self.ref = pd.DataFrame(self.df['Reference %d' %(self.reference_number-1)])
                    # reset to allow for selection in the future
                    self.data_headers_idx = None
                    self.data_headers = None
                    self.reference_ratio = None
                    self.reference_ratio_idx = None
                    
                    # set all buttons to active 
                    self.save_spectra_button.config(state = NORMAL)
                    self.save_reference_button.config(state = NORMAL)
                    self.acquire_save_button.config(state = NORMAL)
                    self.plot_selected_button.config(state =DISABLED)
                    self.add_remove_button.config(state = NORMAL)
                    self.ratio_view_button.config(state = NORMAL)
                    self.open_loop_button.config(state = NORMAL)
            except:
                messagebox.showerror("Error", "Oops! Something went wrong with Opening File. Try again or select different file")
                    
            
            
        def autorange():
            settings = settings_read(self.settings_file)
            max_autorange = int(settings[7][1])
            autorange_thresh = int(settings[6][1])
            integ_time = int(settings[3][1])
            pulses = 1 # start with one pulse then increment
            plt.clf()
            max_data = 0
            if self.autoscale_button['relief'] != SUNKEN: # if autoscale is not active then change y axis limits
                plt.ylim((0,66500))
            plt.xlim(int(settings[9][1]), int(settings[10][1])) # change x axis limits to specified settings
            plt.ylabel('a.u.')
            plt.xlabel('Wavelength (nm)')
            # acquire data for the given # of loops plot, and prompt user to
            # select plots they wish to save with a popup window
            for x in range(0,max_autorange): 
                settings[1][1] = pulses
                # write settings array to csv 
                settings_write(settings)
                data = acquire_avg()
                if max(data) < autorange_thresh:  
                    if x == max_autorange-1:
                        messagebox.showinfo("Pulses", "Max # of Pulses reached")
                    else:
                        pulses = pulses+1
                        plt.plot(self.wavelength,data, label = "Pulses: "+ str(settings[1][1]))
                        plt.subplots_adjust(bottom=0.14, right=0.86)
                        plt.legend(loc = "center right", prop={'size': 7}, bbox_to_anchor=(1.18, 0.5))
                        self.fig.canvas.draw()
                else:
                    settings[1][1] = pulses 
                    settings_write(settings)
                    messagebox.showinfo("Pulses", str(settings[1][1]) + "  Pulses to reach threshold")
                    break
        
        # allows for switching of button state from pressed to released
        def open_loop_state():
            if self.open_loop_stop is not None:
                self.open_loop_button.config(command = open_loop, relief = RAISED, bg = 'light grey')
                root.after_cancel(self.open_loop_stop)
                
        def open_loop():
                # change open loop button  appearance and change command so that when clicked it will
                # deactivate open_loop function
                self.open_loop_button.config(command = open_loop_state, relief = SUNKEN, bg = 'gold')
                settings = settings_read(self.settings_file)
                
                # acquire data for the given # of loops plot, and prompt user to
                # select plots they wish to save with a popup window
                if self.autoscale_button['relief'] != SUNKEN: # if autoscale is not active then change y axis limits
                    plt.ylim((0,66500))
                plt.xlim(int(settings[9][1]), int(settings[10][1])) # change x axis limits to specified settings
                plt.ylabel('a.u.')
                plt.xlabel('Wavelength (nm)')
                plt.clf()
                data = acquire_avg()
                np.savetxt(file_acquire, data, fmt="%d", delimiter=",")
                plt.plot(self.wavelength,data)
                plt.subplots_adjust(bottom=0.14, right=0.86)
                self.fig.canvas.draw()
                self.open_loop_stop = root.after(1, open_loop)
                
                '''
                settings = settings_read(self.settings_file)
                number_loops = int(settings[13][1])
                loop_number = 1
                open_loop_data = pd.DataFrame(self.wavelength)
                open_loop_data.columns = ['Wavelength (nm)']
                plt.clf()
                # acquire data for the given # of loops plot, and prompt user to
                # select plots they wish to save with a popup window
                if self.autoscale_button['relief'] != SUNKEN: # if autoscale is not active then change y axis limits
                    plt.ylim((0,66500))
                plt.xlim(int(settings[9][1]), int(settings[10][1])) # change x axis limits to specified settings
                plt.ylabel('a.u.')
                plt.xlabel('Wavelength (nm)')
                for x in range(0,number_loops): 
                    data = acquire_avg()
                    df_data_array = pd.DataFrame(data)
                    open_loop_data['open_loop %d' %loop_number] = df_data_array
                    plt.plot(self.wavelength,data, label = open_loop_data.columns[x+1])
                    loop_number += 1
                    plt.subplots_adjust(bottom=0.14, right=0.86)
                    plt.legend(loc = "center right", prop={'size': 7}, bbox_to_anchor=(1.18, 0.5))
                    self.fig.canvas.draw()
                self.clear_button.config(state = NORMAL)
                open_loop_window = Toplevel(root)
                open_loop_window .title('Select plot(s) to view')
                open_loop_window .geometry('325x380')
                scrollbar = Scrollbar(open_loop_window)
                scrollbar.pack(side = RIGHT, fill = Y )
                #create function to save the selected plot names and plot them
                def save_selected():
                    #globalself.scan_numberr
                    loop_headers_idx = lb.curselection()
                    loop_headers = [lb.get(idx) for idx in lb.curselection()]
                    for x in range(0,len(loop_headers),1):
                        data = pd.DataFrame(open_loop_data[loop_headers[x]])
                        self.df[['Scan_ID %d' %self.scan_number]] = data
                        self.scan_number += 1
                    #check if the data headers is empty to set to none for future plotting
                    self.df.to_csv(self.save_file, mode = 'w', index = False) 
                    open_loop_window.destroy()
                def select_all(): 
                    lb.select_set(0, END)
                def unselect_all():
                    lb.select_clear(0, END)
            
                headers = StringVar()
                lb = Listbox(open_loop_window, listvariable=headers, selectmode = MULTIPLE, yscrollcommand = scrollbar.set)
                lb.configure(width = 30, height = 10, font=("Times New Roman", 16))
                
                loop_headers_dummy = list(open_loop_data.columns.values)
                for col in range(1, len(loop_headers_dummy),1):
                    lb.insert('end', loop_headers_dummy[col])
                lb.pack()
                save_selected_button = Button(open_loop_window, text = 'Save Selected', width = 30, height = 2, command = save_selected)
                save_selected_button.pack()
                select_all_button = Button(open_loop_window, text = 'Select_all', width = 30, height = 2, command = select_all)
                select_all_button.pack()
                Unselect_all_button = Button(open_loop_window, text = 'Un-Select_all', width = 30, height = 2, command = unselect_all)
                Unselect_all_button.pack()
                '''
        '''     
        def acquire_save():
            plt.clf()
            data = acquire_avg()
            #acquire then save to csv file 
            df_data_array = pd.DataFrame(data)
            self.df['Scan_ID %d' %self.scan_number] = df_data_array
            self.df.to_csv(self.save_file, mode = 'w', index = False)
            data = self.df[['Scan_ID %d' %self.scan_number]]
            
            # check for selected data and ratio view and then plot all data 
            if self.data_headers is not None and self.ratio_view_button['relief'] == SUNKEN:
                data_sel = pd.read_csv(self.save_file, header = 0) # selected data
                data_sel = data_sel[self.data_headers]
                data_sel = np.true_divide(data_sel,self.ref)*100
                plt.plot(self.wavelength,data_sel[self.data_headers])
                plt.legend(self.data_headers, loc = "upper right", prop={'size': 6})
                data = np.true_divide(data,self.ref)*100
                plt.plot(self.wavelength, np.ones(288)*100, 'r')
                if self.autoscale_button['relief'] == SUNKEN: # if autoscale is active, pass, if not set limits to 105%
                    pass
                else:
                    plt.ylim((0,105))
            if self.ratio_view_button['relief'] == SUNKEN and self.data_headers is None:
                data = np.true_divide(data,self.ref)*100
                plt.plot(self.wavelength, np.ones(288)*100, 'r')
                if self.autoscale_button['relief'] == SUNKEN: # if autoscale is active, pass, if not set limits to set graphing parameters%
                    pass
                else:
                    plt.ylim((0,105))
            
            # if data is selected plot that as well
            if self.data_headers is not None:
                data_sel = pd.read_csv(self.save_file, header = 0) # selected data 
                plt.plot(self.wavelength,data_sel[self.data_headers])
                plt.legend(self.data_headers, loc = "upper right", prop={'size': 6})
            if self.ref is not None:
                plt.plot(self.wavelength,self.ref, '--')
            
            plt.plot(self.wavelength,data)
            plt.ylabel('a.u.')
            plt.xlabel('Wavelength (nm)')
            plt.xlim(int(settings[9][1]), int(settings[10][1])) # change x axis limits to specified settings
            self.fig.canvas.draw()
            self.scan_number = 1 + self.scan_number
            self.ratio_view_button.config(state = NORMAL)
        '''
        
        def acquire(save):
            data = acquire_avg()
            settings = settings_read(self.settings_file)
            # is acquire and save, save to designtated csv 
            if save:
                df_data_array = pd.DataFrame(data)
                self.df['Scan_ID %d' %self.scan_number] = df_data_array
                self.df.to_csv(self.save_file, mode = 'w', index = False)
                data = self.df[['Scan_ID %d' %self.scan_number]]
                self.scan_number = 1 + self.scan_number
                self.ratio_view_button.config(state = NORMAL)
            else: # if only acquire save to temporary file
                np.savetxt(file_acquire, data, fmt="%d", delimiter=",")
                data = pd.read_csv(file_acquire, header = None)
            # get selected data arrays for plotting
            plt.clf()
            # if ratio is activated take the ratio of all selected or just current ratio and plot
            if self.data_headers is not None:
                data_sel = pd.read_csv(self.save_file, header = 0) # selected data
                data_sel = data_sel[self.data_headers]
                if self.autoscale_button['relief'] != SUNKEN: # if autoscale is active, pass, if not set limits to 105%
                    plt.ylim((0,66500))
                if self.ratio_view_button['relief'] == SUNKEN:
                    data_sel = np.true_divide(data_sel,self.ref)*100 # ratio view activated, overwrite selected data array into ratio
                    data = np.true_divide(data,self.ref)*100
                    plt.plot(self.wavelength, np.ones(288)*100, 'r')
                    if self.autoscale_button['relief'] != SUNKEN: # if autoscale is active, pass, if not set limits to 105%
                        plt.ylim((0,105))
                plt.plot(self.wavelength,data_sel[self.data_headers])
                plt.legend(self.data_headers, loc = "upper right", prop={'size': 6})
                
            elif self.data_headers is None:
                if self.ratio_view_button['relief'] == SUNKEN:
                    data = np.true_divide(data,self.ref)*100
                    plt.plot(self.wavelength, np.ones(288)*100, 'r')
                    if self.autoscale_button['relief'] != SUNKEN: # if autoscale is active, pass, if not set limits to set graphing parameters%
                        plt.ylim((0,105))  
                else: # if autoscale is active, pass, if not set limits to set graphing parameters%
                    if self.autoscale_button['relief'] != SUNKEN:
                        plt.ylim((0,66500)) # default axis limits on graphing frame 
            
            plt.plot(self.wavelength,data)
            plt.ylabel('a.u.')
            plt.xlabel('Wavelength (nm)')
            
            plt.xlim(int(settings[9][1]), int(settings[10][1])) # change x axis limits to specified settings
            self.fig.canvas.draw()
            self.clear_button.config(state = NORMAL)
            
        def plot_selected():
            # Clear unsaved spectra 
            plt.clf()
            # plot Selected columns (headers) from add_remove plots
            plt.plot(self.wavelength,self.df[self.data_headers])
            plt.legend(self.data_headers, loc = "upper right", prop={'size': 6}, bbox_to_anchor=(1.18, 0.5))
            plt.subplots_adjust(bottom=0.14, right=0.86)
            
            
            self.fig.canvas.draw()
            
        #Clear canvas
        def clear():
            plt.clf()
            self.fig.canvas.draw()
            
        def ratio_view():
            
            if self.ratio_view_button['relief'] == SUNKEN:
                self.ratio_view_button.config(bg = 'light grey', relief = RAISED)
            else:
                self.ratio_view_button.config(bg = 'gold', relief = SUNKEN)
            

            
                
        def reference():
            # save current spectra then draw on canvas \
            data = pd.read_csv(self.save_file, header = 0)
            # take latest acquire and save as rference 
            self.ref = pd.DataFrame(np.loadtxt(file_acquire, delimiter=",")) #reference changed to most recent acquire
            self.df['Reference %d' %self.reference_number] = self.ref # append data to global df data frame for saved spectra 
            self.df.to_csv(self.save_file, mode = 'w', index = False) # save to csv file with new reference 
            plt.clf()
            
            if self.data_headers is not None:
                data_sel = pd.read_csv(self.save_file, header = 0) # selected data 
                plt.plot(self.wavelength,data_sel[self.data_headers],'--')
                plt.legend(self.data_headers, loc = "upper right", prop={'size': 6})
            plt.plot(self.wavelength,self.ref, 'b--')
            plt.ylabel('a.u.')
            plt.xlabel('Wavelength (nm)')
            self.fig.canvas.draw()
            self.clear_button.config(state = NORMAL)
            self.acquire_save_button.config(state = NORMAL)
            self.add_remove_button.config(state = NORMAL)
            self.reference_number = 1 + self.reference_number
            '''
            data = acquire_avg()
            df_data_array = pd.DataFrame(data)
            self.df['Reference %d' %self.reference_number] = df_data_array
            self.df.to_csv(self.save_file, mode = 'w', index = False)
            data = self.df[['Reference %d' %self.reference_number]]
            plt.clf()
            plt.plot(self.wavelength,data)
            self.fig.canvas.draw()
            self.acquire_save_button.config(state = NORMAL)
            self.add_remove_button.config(state = NORMAL)
            self.reference_number = 1 + self.reference_number
            '''
            
        def scan(save): 
            self.scan_file = []
            #sequence and save prompts user to input new file name
            #that will create new folder or go into experiment folder w/ sequence data
            if save:
                self.key_pad(4)
                root.wait_window(self.keypad) #wait until folder name is entered to take measurments 
                    
            # open settings and send integ time to spectrometer 
            settings = settings_read(self.settings_file)
            plt.clf()
            number_avg = int(settings[11][1])
            integ_time = int(settings[3][1])
            smoothing_used = int(settings[12][1])
            smoothing_width = int(settings[8][1])            
            dark_subtract = int(settings[4][1])
            burst_number = int(settings[22][1])
            burst_delay = float(settings[21][1])
            
            if self.autoscale_button['relief'] != SUNKEN: # if autoscale is not active then change y axis limits
                plt.ylim((0,66500))
            plt.xlim(int(settings[9][1]), int(settings[10][1])) # change x axis limits to specified settings
            #loop through the number of bursts and measurements per burst then send that info to spectrometer
            # and take measurements
            '''
            for burst in range(0,burst_number):
                number_measurements = int(settings[23+burst][1])
                measurement = 0
                for i in range(0,number_measurements):
                    if dark_subtract == 1:
                        data_dark = dark_subtract_func(smoothing_width)
                    else:
                        data_dark = 0
                    graph_label = 'burst #' + str(burst+1) + ' measurement #' + str(i+1)
                    pulses = int(settings[33+burst][1])
                    self.ser.write(b"set_integ %0.6f\n" % integ_time)
                    self.ser.write(b"pulse %d\n" % pulses)
                    sleep(0.5)
                    # tell spectromter to send data
                    data = 0
                    for x in range(0,number_avg,1): #take scans then average
                        self.ser.write(b"read\n")
                        #read data and save to pseudo csv to plot
                        data_read = self.ser.readline()
                        #data = self.ser.read_until('\n', size=None)
                        data_temp = np.array([int(i) for i in data_read.split(b",")])
                        data = data + data_temp
                        if x == number_avg-1:  # reached number of averages
                            data = data/number_avg #take average of data and save
                            if smoothing_used == 1:  # if smoothing is checked smooth array
                                dummy = np.ravel(data)
                                for i in range(0,len(data)-smoothing_width,1):
                                    data[i] = sum(np.ones(smoothing_width)*dummy[i:i+smoothing_width])/(smoothing_width)
                    data = data-data_dark
            '''
            # iterate through x and y on steppers
            for x in range(0,20):
                for y in range(0,20):
                    data = acquire_avg()
                    df_data_array = pd.DataFrame(data)
                    self.df_scan['X: %d Y: %d' % (x, y)] = df_data_array
                    if (x % 2) == 0:
                        self.ser.write(b"y+\n") # move in y after one scan
                    else:
                        self.ser.write(b"y-\n")
                self.ser.write(b"x\n") # move in x after all y scans
            # after all scans are taken and saved to array save to CSV then plot all
            self.df_scan.to_csv(self.scan_file, mode = 'w', index = False)
            data_pd = pd.read_csv(self.scan_file)
            # get col header names to add to listbox text
            data_headers_dummy = list(data_pd.columns.values)
            for col in range(1, len(data_headers_dummy),1):
                plt.plot(self.wavelength, self.df_scan[data_headers_dummy[col]])
                self.fig.canvas.draw()
                
        def sequence(save):
            self.sequence_file = []
            #sequence and save prompts user to input new file name
            #that will create new folder or go into experiment folder w/ sequence data
            if save:
                self.key_pad(3)
                root.wait_window(self.keypad) #wait until folder name is entered to take measurments 
                    
            # open settings and send integ time to spectrometer 
            settings = settings_read(self.settings_file)
            plt.clf()
            number_avg = int(settings[11][1])
            integ_time = int(settings[3][1])
            smoothing_used = int(settings[12][1])
            smoothing_width = int(settings[8][1])            
            dark_subtract = int(settings[4][1])
            burst_number = int(settings[22][1])
            burst_delay = float(settings[21][1])
            
            if self.autoscale_button['relief'] != SUNKEN: # if autoscale is not active then change y axis limits
                plt.ylim((0,66500))
            plt.xlim(int(settings[9][1]), int(settings[10][1])) # change x axis limits to specified settings
            #loop through the number of bursts and measurements per burst then send that info to spectrometer
            # and take measurements
            for burst in range(0,burst_number):
                number_measurements = int(settings[23+burst][1])
                measurement = 0
                for i in range(0,number_measurements):
                    if dark_subtract == 1:
                        data_dark = dark_subtract_func(smoothing_width)
                    else:
                        data_dark = 0
                    graph_label = 'burst #' + str(burst+1) + ' measurement #' + str(i+1)
                    pulses = int(settings[33+burst][1])
                    self.ser.write(b"set_integ %0.6f\n" % integ_time)
                    self.ser.write(b"pulse %d\n" % pulses)
                    # tell spectromter to send data
                    data = 0
                    for x in range(0,number_avg,1): #take scans then average
                        self.ser.write(b"read\n")
                        #read data and save to pseudo csv to plot
                        data_read = self.ser.readline()
                        #data = self.ser.read_until('\n', size=None)
                        data_temp = np.array([int(p) for p in data_read.split(b",")])
                        data = data + data_temp
                        if x == number_avg-1:  # reached number of averages
                            data = data/number_avg #take average of data and save
                            if smoothing_used == 1:  # if smoothing is checked smooth array
                                dummy = np.ravel(data)
                                for i in range(0,len(data)-smoothing_width,1):
                                    data[i] = sum(np.ones(smoothing_width)*dummy[i:i+smoothing_width])/(smoothing_width)
                    data = data-data_dark
                    if self.autoscale_button['relief'] == SUNKEN: # if autoscale is active, pass, if not set limits to set graphing parameters%
                        pass
                    else:
                        plt.ylim((0,66500)) # default axis limits on graphing frame 
                    plt.plot(self.wavelength,data, label = graph_label)
                    plt.subplots_adjust(bottom=0.14, right=0.86)
                    plt.legend(loc = "center right", prop={'size': 7}, bbox_to_anchor=(1.18, 0.5))
                    self.fig.canvas.draw()
                    measurement = measurement + 1
                    # save files to 
                    if save:
                        df_data_array = pd.DataFrame(data)
                        self.df_seq['burst %d measurement %d' % (burst+1, measurement)] = df_data_array
                        self.df_seq.to_csv(self.sequence_file, mode = 'w', index = False)
                sleep(burst_delay)
                
        ### read in default settings
        settings_open = open(self.settings_file, 'r')
        csv_reader = csv.reader(settings_open, delimiter=',')
        settings = list(csv_reader)
        A = float(settings[15][1])
        B1 = float(settings[16][1])
        B2 = float(settings[17][1])/1000
        B3 = float(settings[18][1])/1000000
        B4 = float(settings[19][1])/1000000000
        B5 = float(settings[20][1])/1000000000000
        self.min_wavelength = int(settings[9][1])
        self.max_wavelength = int(settings[10][1])
        pulse = int(settings[1][1])
        if pulse == 0:
            self.integ_free = True
        
        #initialize wavelength array with zeros then solve given pixel coefficients
        self.wavelength = np.zeros(288)
        for pixel in range(1,289,1):
            self.wavelength[pixel-1] = A + B1*pixel + B2*(pixel**2) + B3*(pixel**3) + B4*(pixel**4) + B5*(pixel**5)
        
        #create all the buttons onto to the main window
        button_width = 10
        button_big_height = 4
        button_small_height = 3
        sticky_to = 'nsew' # allows all buttons to resize
        
        
        # with all their corresponding functions (command)
        self.quit_button = Button(root, text = "Quit", fg = 'Red', command = self.quit_button, width = button_width, height = button_big_height)
        self.quit_button.grid(row = 0, column = 6, padx = 1, sticky = sticky_to)
        
        self.help_button = Button(root, text = "Help", fg = 'black', command = self.help_window, width = button_width, height = button_big_height)
        self.help_button.grid(row = 0, column = 5, sticky = sticky_to)
        
        self.settings_button = Button(root, text = "Settings", fg = 'black', command = self.settings_window, width = button_width, height = button_big_height)
        self.settings_button.grid(row = 0, column = 4, padx = (8,1), sticky = sticky_to)
        
        self.save_spectra_button = Button(root, text = "Save as Spectra", wraplength = 80, fg = 'black', command = lambda: self.key_pad(2), width = button_width, height = button_big_height, state = DISABLED)
        self.save_spectra_button.grid(row = 0, column = 3, padx = (1,8), sticky = sticky_to)
        
        self.save_reference_button = Button(root, text = "Save as Reference", wraplength = 80, fg = 'black', command = reference, width = button_width, height = button_big_height, state = DISABLED)
        self.save_reference_button.grid(row = 0, column = 2, padx = (10,0), sticky = sticky_to)
        
        self.open_new_button = Button(root, text = "New Experiment", wraplength = 80, fg = 'black', command = lambda: self.key_pad(1), width = button_width, height = button_big_height)
        self.open_new_button.grid(row = 0, column = 1, padx = (0,5), sticky = sticky_to)
        
        self.open_experiment_button = Button(root, text = "Open Experiment", wraplength = 80, fg = 'black', command = OpenFile, width = button_width, height = button_big_height)
        self.open_experiment_button.grid(row = 0, column = 0, sticky = sticky_to)
        
        self.acquire_button = Button(root, text = "Acquire", wraplength = 80, fg = 'black',
                                     command = lambda: acquire(save = False), width = button_width, height = button_big_height)
        self.acquire_button.grid(row = 1, column = 0, pady = (3,1), sticky = sticky_to)
        
        self.acquire_save_button = Button(root, text = "Acquire and Save", fg = 'black', wraplength = 80, command = lambda: acquire(save = True), width = button_width, height = button_big_height, state = DISABLED)
        self.acquire_save_button.grid(row = 2, column = 0, pady = (0,1), sticky = sticky_to)
        
        self.autorange_button = Button(root, text = "Auto-Range", fg = 'black', wraplength = 80, command = autorange, width = button_width, height = button_big_height)
        self.autorange_button.grid(row = 3, column = 0, pady = (0,5), sticky = sticky_to)
        
        self.open_loop_button = Button(root, text = "Open Loop", fg = 'black',state = DISABLED, command = open_loop, width = button_width, height = button_big_height)
        self.open_loop_button.grid(row = 4, column = 0, pady = (5,1), sticky = sticky_to)
        
        self.sequence_button = Button(root, text = "Sequence", fg = 'black', wraplength = 80, command = lambda: sequence(save = False), width = button_width, height = button_big_height)
        self.sequence_button.grid(row = 5, column = 0, sticky = sticky_to)
        
        self.scan_button = Button(root, text = "Sequence and Save", fg = 'black', wraplength = 80, command = lambda: sequence(save =True), width = button_width, height = button_big_height)
        self.scan_button.grid(row = 6, column = 0, sticky = sticky_to)
        
        self.water_pump_button = Button(root, text = "Scan", fg = 'black', wraplength = 80, command = lambda: scan(save = True), width = button_width, height = button_small_height)
        self.water_pump_button.grid(row = 6, column = 1, padx = 1, sticky = sticky_to)
        
        self.ratio_view_button = Button(root, text = "Ratio View", fg = 'black', wraplength = 80, command = ratio_view, width = button_width, height = button_small_height, state = DISABLED)
        self.ratio_view_button.grid(row = 6, column = 2, padx = 1, sticky = sticky_to)
        
        self.autoscale_button = Button(root, text = "Autoscale", fg = 'black', wraplength = 80, command = self.autoscale, width = button_width, height = button_small_height)
        self.autoscale_button.grid(row = 6, column = 3, padx = 1, sticky = sticky_to)
        
        self.plot_selected_button = Button(root, text = "Plot Selected", fg = 'black', wraplength = 80, command = plot_selected, state = DISABLED, width = button_width, height = button_small_height)
        self.plot_selected_button.grid(row = 6, column = 4, padx = 1, sticky = sticky_to)
        
        self.clear_button = Button(root, text = "Clear", fg = 'black', wraplength = 80, command = clear, width = button_width, height = button_small_height)
        self.clear_button.grid(row = 6, column = 5, padx = 1, sticky = sticky_to)
        
        self.add_remove_button = Button(root, text = "Add/Remove Plots", fg = 'black', wraplength = 85, state = DISABLED, command = self.add_remove_plots, width = button_width, height = button_small_height)
        self.add_remove_button.grid(row = 6, column = 6, padx = 5, pady = 1, sticky = sticky_to)
        
        ## Graphing Frame and fake plot
        self.graph_frame = Frame(root, background = "white")
        self.graph_frame.grid(row = 1, column = 1, columnspan = 6, rowspan = 5, padx = 1, pady = 3, sticky = sticky_to)
        
        #initalize figure
        self.fig = plt.figure()
            
        #initalize canvas for plotting
        canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)  # A tk.DrawingArea.
        
        # create toolbar for canvas
        toolbar = NavigationToolbar2Tk(canvas, self.graph_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(fill = BOTH, expand = True)
        
        # allow buttons and frames to resize with the resizing of the root window
        root.grid_columnconfigure((0,1,2,3,4,5,6),weight = 1)
        root.grid_rowconfigure((0,1,2,3,4,5,6),weight = 1)
        
    def help_window(self):
        self.help_window = Toplevel(root)
        self.help_window.title('Help')
        self.help_window.configure(bg= "sky blue")
        if full_screen == True:
            self.help_window.attributes('-fullscreen', True) # Fullscreen on touch screen
        else:
            self.help_window.geometry(self.screensize) # set the size of the monitor
            
        sticky_to = "nsew"
        frame_padding = 5
        
        
        
        label = Label(self.help_window, image = self.help_window_image)
        label.pack()
        
        back_button = Button(self.help_window, text = 'Back', fg = 'red', command = self.help_window.destroy)
        back_button.pack()
        
        
        
    def settings_window(self):
        self.settings_popup = Toplevel(root)
        self.settings_popup.title('Settings')
        self.settings_popup.configure(bg= "sky blue")
        if full_screen == True:
            self.settings_popup.attributes('-fullscreen', True) # Fullscreen on touch screen
        else:
            self.settings_popup.geometry(self.screensize) # set the size of the monitor
            
        sticky_to = "nsew"
        frame_padding = 5
        
        settings_button_frame = Frame(self.settings_popup, width = 350, height =120, background = "sky blue")
        #settings_button_frame.place(x = 585, y = 340)
        settings_button_frame.grid(row = 3, column = 2, sticky = sticky_to, padx = 2, pady = 2)
            
        quit_button = Button(settings_button_frame, text = "Back", fg = 'Red', command = self.settings_popup.destroy, width = 9, height = 3)
        quit_button.grid(row = 1, column = 0, sticky = sticky_to)
        
        save_button = Button(settings_button_frame, text = "Save", fg = 'Green', command = self.settings_save, width = 22, height = 3)
        save_button.grid(row = 0, column = 0, columnspan = 2, pady = 2, sticky = sticky_to)
        
        default_button = Button(settings_button_frame, text = "Reset To Default Settings", command = self.default, width = 9, height = 3, wraplength = 85)
        default_button.grid(row = 1, column = 1, sticky = sticky_to)
        
        #read in settings
        settings_open = open(self.settings_file, 'r')
        csv_reader = csv.reader(settings_open, delimiter=',')
        settings = list(csv_reader)
        pulse = int(settings[1][1])
        pulse_rate = int(settings[2][1])
        if self.integ_free == True:
            integ_time = int(settings[3][1])
        else:
            integ_time = int(120 + (pulse-1)*(1000000/pulse_rate))
            if pulse > 1:
                integ_time = int(integ_time + 1000000/pulse_rate)
                
        dark_subtract = int(settings[4][1])
        lamp_voltage = int(settings[5][1])
        auto_pulse_threshold = int(settings[6][1])
        auto_pulse_max = int(settings[7][1])
        smoothing_half_width = int(settings[8][1])
        min_wavelength = int(settings[9][1])
        max_wavelength = int(settings[10][1])
        average_scans = int(settings[11][1])
        smoothing_used = int(settings[12][1])
        step_resolution = int(settings[13][1])
        grid_size = int(settings[14][1])
        a_0 = str(settings[15][1])
        b_1 = str(settings[16][1])
        b_2 = str(settings[17][1])
        b_3 = str(settings[18][1])
        b_4 = str(settings[19][1])
        b_5 = str(settings[20][1])
        burst_delay_sec = float(settings[21][1])
        burst_number = int(settings[22][1])
        self.measurement_burst = ["" for x in range(burst_number)]
        self.pulse_burst = ["" for x in range(burst_number)]
        
        # try to read bursts settings from the csv, if it is empty it will cause
        # an exception and write default values to those new bursts
        for x in range(0,burst_number):
            try:
                self.measurement_burst[x] = str(settings[23+x][1]) 
                self.pulse_burst[x] =  str(settings[33+x][1]) 
            except:
                self.measurement_burst[x] =  str(5) 
                self.pulse_burst[x] =  str(1) 
        
        # Start to create Frames for settings window
        button_background = "white"
        frame_background = 'white'
        fground = "Black"
        
        # _____________Single Acquisition Frame_________________________________
        single_acquisition_frame = Frame(self.settings_popup, background = frame_background)
        #single_acquisition_frame.place(x = left_side, y = 5)
        single_acquisition_frame.grid(row = 0, rowspan = 2, column = 0, sticky = sticky_to, padx = frame_padding, pady=frame_padding)
        
        single_acquisition_label = Label(single_acquisition_frame, text = "Single Acquisition Settings", fg = fground, bg= frame_background)
        single_acquisition_label.grid(row = 0, column = 0, columnspan = 2, sticky = sticky_to)
        self.acquisition_number = IntVar() 
        self.acquisition_number.set(pulse)
        acq_number_button = Button(single_acquisition_frame, text = "Pulses:", fg = fground, bg = button_background, command = lambda: self.Num_Pad(1))
        acq_number_button.grid(row = 1, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        acq_number_entry = Entry(single_acquisition_frame, textvariable = self.acquisition_number, justify = CENTER)
        acq_number_entry.grid(row = 1, column = 1, padx = 14, pady = 2, sticky = sticky_to)
        
        self.pulse_rate = IntVar()
        self.pulse_rate.set(pulse_rate)
        pulse_rate_button = Button(single_acquisition_frame, text = "Pulse Rate (Hz):", fg = fground, bg = button_background, command = lambda: self.Num_Pad(2))
        pulse_rate_button.grid(row = 2, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        pulse_rate_entry = Entry(single_acquisition_frame, textvariable = self.pulse_rate, justify = CENTER)
        pulse_rate_entry.grid(row = 2, column = 1, padx = 14, pady = 2, sticky = sticky_to)
  
        self.integ_time = IntVar()
        self.integ_time.set(integ_time)
        integ_time_button = Button(single_acquisition_frame, text = "Integration Time (usec):", fg = fground, bg = button_background,\
                                   command = lambda: self.Num_Pad(3))
        integ_time_button.grid(row = 3, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        integ_time_entry = Entry(single_acquisition_frame, textvariable = self.integ_time, justify = CENTER)
        integ_time_entry.grid(row = 3, column = 1, padx = 14,pady = 2, sticky = sticky_to)
        
        self.average_scans = IntVar()
        self.average_scans.set(average_scans)
        average_scans_button = Button(single_acquisition_frame, text = "# of Averages:", fg = fground, bg = button_background,\
                                   command = lambda: self.Num_Pad(11))
        average_scans_button.grid(row = 4, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        average_scans_entry = Entry(single_acquisition_frame, textvariable = self.average_scans, justify = CENTER)
        average_scans_entry.grid(row = 4, column = 1, padx = 14, pady = 2, sticky = sticky_to)
        
        self.dark_subtract = IntVar()
        self.dark_subtract.set(dark_subtract)
        dark_subtraction_entry = Checkbutton(single_acquisition_frame, text = "Use Dark Subtraction ", variable = self.dark_subtract)
        dark_subtraction_entry.grid(row = 5, column =0, pady = 2, padx = 2, sticky = sticky_to)
        
        self.smoothing_used = IntVar()
        self.smoothing_used.set(smoothing_used)
        smoothing_entry = Checkbutton(single_acquisition_frame, text = "Smoothing  ", variable = self.smoothing_used)
        smoothing_entry.grid(row = 5, column =1, pady = 2, padx = 14, sticky = sticky_to)
        
        
        #___________________ Lamp Frame _______________________________________
        
        lamp = Frame(self.settings_popup, width = 340, height = 75, background = frame_background)
        #lamp.place(x = left_side, y = 195)
        #lamp.grid(row = 1, column = 0, sticky = sticky_to, padx = frame_padding, pady=frame_padding)
        
        lamp_label = Label(lamp, text = "Lamp", fg = fground, bg = frame_background)
        #lamp_label.grid(row = 0, column = 0, columnspan = 2, sticky = sticky_to)
        self.lamp_voltage = IntVar()
        self.lamp_voltage.set(lamp_voltage)
        lamp_entry_button= Button(lamp, text = "Lamp Voltage (volts):", fg = fground, bg = button_background, command = lambda: self.Num_Pad(5))
        #lamp_entry_button.grid(row = 1, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        lamp_entry = Entry(lamp, textvariable = self.lamp_voltage, justify = CENTER)
        #lamp_entry.grid(row = 1, column = 1, padx = 14, pady = 2, sticky = sticky_to)
        
        #__________________AutoRange Frame ____________________
        Auto_range_frame = Frame(self.settings_popup, background = frame_background)
        #Auto_range_frame.place(x = left_side, y = 255)
        Auto_range_frame.grid(row = 2, column =0, sticky = sticky_to, padx = frame_padding, pady=frame_padding)
        auto_range_label = Label(Auto_range_frame, text = "Auto-Ranging:", fg = fground, bg = frame_background)
        auto_range_label.grid(row = 0, column = 0, columnspan = 2, sticky = sticky_to)
        self.threshold = IntVar()
        self.threshold.set(auto_pulse_threshold)
        autopulse_entry_button = Button(Auto_range_frame, text = "AutoPulse Threshold(counts):", fg = fground, bg = button_background, command = lambda: self.Num_Pad(6))
        autopulse_entry_button.grid(row = 1, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        autopulse_entry = Entry(Auto_range_frame, textvariable = self.threshold, justify = CENTER)
        autopulse_entry.grid(row = 1, column = 1, padx = 8, sticky = sticky_to)
        
        self.max_pulses = IntVar()
        self.max_pulses.set(auto_pulse_max)
        max_pulses_entry_button = Button(Auto_range_frame, text = "Max # of Pulses:", fg = fground, bg = button_background, command = lambda: self.Num_Pad(7))
        max_pulses_entry_button.grid(row = 2, column = 0, sticky = sticky_to, padx = 1, pady=1)
        max_pulses_entry = Entry(Auto_range_frame, textvariable = self.max_pulses, justify = CENTER)
        max_pulses_entry.grid(row = 2, column = 1, padx = 8, pady = 4, sticky = sticky_to)
        
        #_________________ Graph settings frame __________________
        graph_frame = Frame(self.settings_popup, width = 340, height = 200, background = frame_background)
        #graph_frame.place(x = left_side, y = 350)
        graph_frame.grid(row = 3, column = 0, sticky = sticky_to, padx = frame_padding, pady=frame_padding)
        
        graph_frame_label = Label(graph_frame, text = "Graphing Options:", fg = fground, bg = frame_background)
        graph_frame_label.grid(row = 0, column = 0, columnspan = 2, sticky = sticky_to)
        self.smoothing = IntVar()
        self.smoothing.set(smoothing_half_width)
        smoothing_entry_button = Button(graph_frame, text = "Smoothing Half-Width (pixels):", fg = fground, bg = button_background, command = lambda: self.Num_Pad(8))
        smoothing_entry_button.grid(row = 1, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        smoothing_entry = Entry(graph_frame, textvariable = self.smoothing, justify = CENTER)
        smoothing_entry.grid(row = 1, column = 1, padx = 8, sticky = sticky_to)
        
        self.min_wavelength = IntVar()
        self.min_wavelength.set(min_wavelength)
        min_wavelength_entry_button = Button(graph_frame, text = "Min-Wavelength:", fg = fground, bg = button_background, command = lambda: self.Num_Pad(9))
        min_wavelength_entry_button.grid(row = 2, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        min_wavelength_entry = Entry(graph_frame, textvariable = self.min_wavelength, justify = CENTER)
        min_wavelength_entry.grid(row = 2, column = 1, padx = 8, sticky = sticky_to)
        
        self.max_wavelength = IntVar()
        self.max_wavelength.set(max_wavelength)
        max_wavelength_entry_button = Button(graph_frame, text = "Max-Wavelength:", fg = fground, bg = button_background, command = lambda: self.Num_Pad(10))
        max_wavelength_entry_button.grid(row = 3, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        max_wavelength_entry = Entry(graph_frame, textvariable = self.max_wavelength, justify = CENTER)
        max_wavelength_entry.grid(row = 3, column = 1, padx = 8, sticky = sticky_to)
        
        #_________calibration Coefficients frame ______________________
        wavelength_pixel_frame = Frame(self.settings_popup, width = 340, height =120, background = frame_background)
        #wavelength_pixel_frame.place(x = 325, y = 245)
        wavelength_pixel_frame.grid(row = 2, column = 1, sticky = sticky_to, padx = frame_padding, pady=frame_padding, rowspan = 2)
        wavelength_pixel_label = Label(wavelength_pixel_frame, text = "Calibration Coefficients", fg = fground, bg= frame_background, justify = CENTER)
        wavelength_pixel_label.grid(row = 0, column = 0, columnspan = 3, sticky = sticky_to)
        self.a_0 = StringVar()
        self.a_0.set(a_0)
        a0_button = Button(wavelength_pixel_frame, text = "A_0: ", fg = fground, bg = button_background, command = lambda: self.Num_Pad(15))
        a0_button.grid(row = 1, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        a0_entry = Entry(wavelength_pixel_frame, textvariable = self.a_0, width = 16)
        a0_entry.grid(row = 1, column = 1, padx = 8, sticky = sticky_to)
        
        self.b_1 = StringVar()
        self.b_1.set(b_1)
        b1_button = Button(wavelength_pixel_frame, text = "B_1: ", fg = fground, bg = button_background, command = lambda: self.Num_Pad(16))
        b1_button.grid(row = 2, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        b1_entry = Entry(wavelength_pixel_frame, textvariable = self.b_1, width = 16)
        b1_entry.grid(row = 2, column = 1, padx = 8, sticky = sticky_to)
        
        self.b_2 = StringVar()
        self.b_2.set(b_2)
        b2_button = Button(wavelength_pixel_frame, text = "B_2: ", fg = fground, bg = button_background, command = lambda: self.Num_Pad(17))
        b2_button.grid(row = 3, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        b2_entry = Entry(wavelength_pixel_frame, textvariable = self.b_2, width = 16)
        b2_entry.grid(row = 3, column = 1, padx = 8, sticky = sticky_to)
        b2_exp_label = Label(wavelength_pixel_frame, text = "e-03", fg = fground, bg= "white", justify = CENTER)
        b2_exp_label.grid(row = 3, column = 2,  sticky = sticky_to)
        
        self.b_3 = StringVar()
        self.b_3.set(b_3)
        b3_button = Button(wavelength_pixel_frame, text = "B_3: ", fg = fground, bg = button_background, command = lambda: self.Num_Pad(18))
        b3_button.grid(row = 4, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        b3_entry = Entry(wavelength_pixel_frame, textvariable = self.b_3, width = 16)
        b3_entry.grid(row = 4, column = 1, padx = 8, sticky = sticky_to)
        b3_exp_label = Label(wavelength_pixel_frame, text = "e-06", fg = fground, bg= "white", justify = CENTER)
        b3_exp_label.grid(row = 4, column = 2,  sticky = sticky_to)
        
        self.b_4 = StringVar()
        self.b_4.set(b_4)
        b4_button = Button(wavelength_pixel_frame, text = "B_4: ", fg = fground, bg = button_background, command = lambda: self.Num_Pad(19))
        b4_button.grid(row = 5, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        b4_entry = Entry(wavelength_pixel_frame, textvariable = self.b_4, width = 16)
        b4_entry.grid(row = 5, column = 1, padx = 8, sticky = sticky_to)
        b4_exp_label = Label(wavelength_pixel_frame, text = "e-09", fg = fground, bg= "white", justify = CENTER)
        b4_exp_label.grid(row = 5, column = 2, sticky = sticky_to)
        
        self.b_5 = StringVar()
        self.b_5.set(b_5)
        b5_button = Button(wavelength_pixel_frame, text = "B_5: ", fg = fground, bg = button_background, command = lambda: self.Num_Pad(20))
        b5_button.grid(row = 6, column = 0, pady = 2, padx = 3, sticky = sticky_to)
        b5_entry = Entry(wavelength_pixel_frame, textvariable = self.b_5, width = 16)
        b5_entry.grid(row = 6, column = 1, padx = 8, sticky = sticky_to)
        b5_exp_label = Label(wavelength_pixel_frame, text = "e-12", fg = fground, bg= "white", justify = CENTER)
        b5_exp_label.grid(row = 6, column = 2, sticky = sticky_to)
        
        #_______open Loop frame_______________
        stepper_frame = Frame(self.settings_popup, width = 340, height =120, background = frame_background)
        #open_loop_frame.place(x = 325, y = 145)
        stepper_frame.grid(row = 1, column = 1, sticky = sticky_to, padx = frame_padding, pady=frame_padding)
        stepper_label = Label(stepper_frame, text = "Scan Settings",fg = fground, bg = frame_background)
        stepper_label.grid(row = 0, column = 0, columnspan = 2, sticky = sticky_to)
        
        self.step_size = IntVar()
        self.step_size.set(step_resolution)
        step_size_button = Button(stepper_frame, text = "Step Size (um)", fg = 'black', bg = button_background, command = lambda: self.Num_Pad(13))
        step_size_button.grid(row = 1, column = 0, padx = 3, pady = 3, sticky = sticky_to)
        step_size_entry = Entry(stepper_frame, textvariable = self.step_size, justify = CENTER)
        step_size_entry.grid(row = 1, column = 1, padx = 8, sticky = sticky_to)
        
        self.grid_size = IntVar()
        self.grid_size.set(grid_size)
        grid_size_button = Button(stepper_frame, text = "Grid Size", fg = 'black', bg = button_background, command = lambda: self.Num_Pad(14))
        grid_size_button.grid(row = 2, column = 0, padx = 3, pady = 3, sticky = sticky_to)
        open_loop_pulse_entry = Entry(stepper_frame, textvariable = self.grid_size, justify = CENTER)
        open_loop_pulse_entry.grid(row = 2, column = 1, padx = 8, sticky = sticky_to)
        
        #___________ sequence Frame _______________________
        sequence_frame = Frame(self.settings_popup, width = 340, height =120, background = frame_background)
        #sequence_frame.place(x = 325, y = 5)
        sequence_frame.grid(row = 0, column = 1, sticky = sticky_to, padx = frame_padding, pady=frame_padding)
        sequence_label = Label(sequence_frame, text = "Sequence Settings",fg = fground, bg = frame_background)
        sequence_label.grid(row = 0, column = 0, columnspan = 2, sticky = sticky_to)
        
        self.burst_number = IntVar()
        self.burst_number.set(burst_number)
        burst_number_button = Button(sequence_frame, text = "# of Bursts: ", fg = 'black', bg = button_background, command = lambda: self.Num_Pad(22))
        burst_number_button.grid(row = 1, column = 0, padx = 3, pady = 10, sticky = sticky_to)
        burst_number_entry = Entry(sequence_frame, textvariable = self.burst_number, justify = CENTER)
        burst_number_entry.grid(row = 1, column = 1, padx = 8, pady = 10, sticky = sticky_to)
        
        self.burst_delay_number = StringVar()
        self.burst_delay_number.set(burst_delay_sec)
        burst_delay_button = Button(sequence_frame, text = "Interburst delay: ", fg = 'black', bg = button_background, command = lambda: self.Num_Pad(21))
        burst_delay_button.grid(row = 2, column = 0, padx = 3, pady = 10, sticky = sticky_to)
        burst_delay_entry = Entry(sequence_frame, textvariable = self.burst_delay_number, justify = CENTER)
        burst_delay_entry.grid(row = 2, column = 1, padx = 8,pady = 10, sticky = sticky_to)
        
        #___________burst Frame ______________
        self.burst_frame = Frame(self.settings_popup, width = 340, height =120, background = frame_background)
        #self.burst_frame.place(x = 585, y = 5)
        self.burst_frame.grid(row = 0, column = 2, sticky = sticky_to, padx = frame_padding, pady=frame_padding, rowspan = 3)
        number_measurements_burst_label = Label(self.burst_frame, justify = CENTER, wraplength = 100, text = "# Measurements",fg = fground, bg = button_background,borderwidth=1, relief="solid")
        number_measurements_burst_label.grid(row = 0, column = 0, padx = 4, pady = 3, sticky = sticky_to)
        pulses_per_burst_label = Label(self.burst_frame,justify = CENTER, wraplength = 100, text = "Pulses per Measurement",fg = fground, bg = button_background, borderwidth=1, relief="solid")
        pulses_per_burst_label.grid(row = 0, column = 1, padx = 4, pady = 3, sticky = sticky_to)
        myFont = font.Font(size=8)
        #create x number of buttons depending on number of bursts provided
        #limited to 10 bursts for spacing reasons
        for x in range(0,burst_number):
            self.measurement_burst_button = Button(self.burst_frame, text = self.measurement_burst[x], fg = 'black', bg = button_background, command = lambda x =x: self.Num_Pad(23+x), font = myFont)
            self.measurement_burst_button.grid(row = 1+x, column = 0, padx = 3, pady = 1, sticky = sticky_to)
        
            self.pulse_burst_button= Button(self.burst_frame, text = self.pulse_burst[x], fg = 'black', bg = button_background, command = lambda x =x: self.Num_Pad(33+x), font = myFont)
            self.pulse_burst_button.grid(row = 1+x, column = 1, padx = 3, pady = 1, sticky = sticky_to)
            
        # resizable buttons and frames within this window
        self.settings_popup.grid_columnconfigure((0,1,2),weight = 1)
        self.settings_popup.grid_rowconfigure((0,1,2),weight = 1)
        single_acquisition_frame.grid_columnconfigure((0,1),weight = 1)
        single_acquisition_frame.grid_rowconfigure((0,1,2,3,4,5),weight = 1)
        #lamp.grid_columnconfigure((0,1,2,3,4,5,6),weight = 1)
        #lamp.grid_rowconfigure((0,1,2,3,4,5,6),weight = 1)
        Auto_range_frame.grid_columnconfigure((0,1),weight = 1)
        Auto_range_frame.grid_rowconfigure((0,1,2),weight = 1)
        graph_frame.grid_columnconfigure((0,1),weight = 1)
        graph_frame.grid_rowconfigure((0,1,2,3),weight = 1)
        wavelength_pixel_frame.grid_columnconfigure((0,1,2),weight = 1)
        wavelength_pixel_frame.grid_rowconfigure((0,1,2,3,4,5,6),weight = 1)
        stepper_frame.grid_columnconfigure((0,1),weight = 1)
        stepper_frame.grid_rowconfigure((0,1,2),weight = 1)
        sequence_frame.grid_columnconfigure((0,1),weight = 1)
        sequence_frame.grid_rowconfigure((0,1,2),weight = 1)
        self.burst_frame.grid_columnconfigure((0,1),weight = 1)
        self.burst_frame.grid_rowconfigure((0,1,2,3,4,5,6,7,8,9,10),weight = 1)
        settings_button_frame.grid_columnconfigure((0,1),weight = 1)
        settings_button_frame.grid_rowconfigure((0,1),weight = 1)
        
    
    def default(self):
        self.acquisition_number.set('1')
        self.pulse_rate.set('60')
        self.integ_time.set('120')
        self.dark_subtract.set('1')
        self.lamp_voltage.set('1000')
        self.threshold.set('60000')
        self.smoothing.set('2')
        self.min_wavelength.set('300')
        self.max_wavelength.set('900')
        self.average_scans.set('2')
        self.smoothing_used.set('1')
        self.step_size.set('500')
        self.grid_size.set('10')
        self.a_0.set('308.6578728')
        self.b_1.set('2.715120910')
        self.b_2.set('-1.581742352')
        self.b_3.set('-3.645168780')
        self.b_4.set('-6.471720765')
        self.b_5.set('27.41135617')
        self.burst_delay_number.set('1.0')
        self.burst_number.set('1')
        self.measurement_burst = str(5)
        self.pulse_burst = str(1) 
        
        #reset Bursts buttons 
        sticky_to = "nsew"
        self.measurement_burst_button = Button(self.burst_frame, text = self.measurement_burst, fg = 'black', bg = "white", command = lambda: self.Num_Pad(23))
        self.measurement_burst_button.grid(row = 2, column = 0, padx = 3, pady = 3, sticky = sticky_to)
        
        self.pulse_burst_button= Button(self.burst_frame, text = self.pulse_burst, fg = 'black', bg = "white", command = lambda: self.Num_Pad(24))
        self.pulse_burst_button.grid(row = 2, column = 1, padx = 3, pady = 3, sticky = sticky_to)
        
        settings_open = open(self.settings_file, 'r')
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
        settings[11][1] = int(self.average_scans.get())
        settings[12][1] = int(self.smoothing_used.get())
        settings[13][1] = int(self.step_size.get())
        settings[14][1] = int(self.grid_size.get())
        settings[15][1] = float(self.a_0.get())
        settings[16][1] = float(self.b_1.get())
        settings[17][1] = float(self.b_2.get())
        settings[18][1] = float(self.b_3.get())
        settings[19][1] = float(self.b_4.get())
        settings[20][1] = float(self.b_5.get())
        settings[21][1] = float(self.burst_delay_number.get())
        settings[22][1] = int(self.burst_number.get())
        settings[23][1] = int(self.measurement_burst)
        settings[33][1] = int(self.pulse_burst)
        
        # write settings array to csv 
        settings_open = open(self.settings_file, 'w')
        with settings_open:
            csv_writer = csv.writer(settings_open, delimiter = ',')
            csv_writer.writerows(settings)
        
        #set wavelength values for plotting
        A = float(settings[15][1])
        B1 = float(settings[16][1])
        B2 = float(settings[17][1])/1000
        B3 = float(settings[18][1])/1000000
        B4 = float(settings[19][1])/1000000000
        B5 = float(settings[20][1])/1000000000000
        
        # solve for new wavelength array based on inputted wavelength coefficients
        for pixel in range(1,289,1):
            self.wavelength[pixel-1] = A + B1*pixel + B2*(pixel**2) + B3*(pixel**3) + B4*(pixel**4) + B5*(pixel**5)
        #reset settings window
        self.settings_popup.destroy()
        self.settings_window()
        
    # setup number pad as toplevel window for settings window input
    #button number saves data to corresponding cell in settings array for saving to csv
    def Num_Pad(self, button_number):
        
        #number pad attributes
        num = StringVar()  # variable for extracting entry number
        self.numpad = Toplevel(self.settings_popup)
        self.numpad.title('Input pad')
        numpad_size = str(self.w-600) + 'x' + str(self.h - 600)
        numpad_size = '330x450'
        self.numpad.geometry(numpad_size)
        
        #self.numpad_frame = Frame(self.numpad, width = 230, height = 15).grid(row = 0, column = 0, columnspan = 3)
        number_entry = Entry(self.numpad, textvariable = num, justify = CENTER).grid(row = 0, column = 0, columnspan = 3, sticky = 'ew')
        
        def button_click(number):
            global current
            current = num.get() # save current entry value
            num.set('') # erase entry
            current = str(current) + str(number)
            num.set(current) # rewrite entry with additional values 
    
        def num_pad_delete():
            num.set('') # erase current entry
            
        def backspace():
            global current
            current = current[:-1] # Remove last digit
            num.set(current)
        
        def num_pad_save(button_number):
            try:
                self.settings_popup.destroy() # reset settings popup with new settings
                settings_open = open(self.settings_file, 'r')
                csv_reader = csv.reader(settings_open, delimiter=',')
                settings = list(csv_reader)
                
                # read in settings to particular button ID on settings page
                # arbitrary number depending on location in CSV file
                if button_number<15 or button_number>21:
                    if button_number == 1 and int(num.get()) == 0:
                        self.integ_free = True
                        settings[3][1] = 100
                    elif button_number == 1 and int(num.get()) != 0:
                        self.integ_free = False
                        settings[3][1] = 120 + (int(settings[1][1]) - 1)*(1000000/int(settings[2][1]))
                    settings[button_number][1]  = int(num.get())
                else:
                    settings[button_number][1]  = float(num.get())
        
                #write settings to csv file
                settings_open = open(self.settings_file, 'w')
                with settings_open:
                    csv_writer = csv.writer(settings_open, delimiter = ',')
                    csv_writer.writerows(settings)
                self.numpad.destroy()
                #open settings window back up and refresh values
                self.settings_window()
                
            # if value or type of returned value isnt an int or float then raise error
            except ValueError or TypeError:
                messagebox.showerror("Error", "Input must be a valid integer or float")
                self.settings_window()
            
        btn_list = [
        '7', '8', '9',
        '4', '5', '6',
        '1', '2', '3',
        '0', 'Del', 'OK']
    
        r = 1
        c = 0
        n = 0
        btn = list(range(len(btn_list)+2))
        for label in btn_list:
            btn[n] = Button(self.numpad, text = label)
            btn[n].grid(row = r, column = c, sticky = 'nsew')
            n+= 1
            c+= 1
            if c>2:
                c = 0
                r+= 1
        if button_number>15:
            if button_number<22:
                # for buttons that require decimal places
                btn[12] = Button(self.numpad, text = '.')
                btn[12].grid(row = 6, column = 0)
                btn[13] = Button(self.numpad, text = 'Backspace')
                btn[13].grid(row = 6, column = 1, columnspan = 2)
                btn[12].configure(command = lambda: button_click('.'))
                btn[13].configure(command = backspace)
                #self.numpad.geometry('230x350')
        else:
            pass
            #self.numpad.geometry('230x290')
        # atttach a number or func to each button
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
        
        self.numpad.grid_columnconfigure((0,1,2), weight = 1)
        self.numpad.grid_rowconfigure((0,1,2,3,4), weight = 1)
        
        
    def settings_save(self):
        settings_open = open(self.settings_file, 'r')
        csv_reader = csv.reader(settings_open, delimiter=',')
        settings = list(csv_reader)
        # get all values from the entry boxes and save to settings CSV file
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
        settings[11][1] = int(self.average_scans.get())
        settings[12][1] = int(self.smoothing_used.get())
        settings[13][1] = int(self.step_size.get())
        settings[14][1] = int(self.grid_size.get())
        settings[15][1] = float(self.a_0.get())
        settings[16][1] = float(self.b_1.get())
        settings[17][1] = float(self.b_2.get())
        settings[18][1] = float(self.b_3.get())
        settings[19][1] = float(self.b_4.get())
        settings[20][1] = float(self.b_5.get())
        settings[21][1] = float(self.burst_delay_number.get())
        settings[22][1] = int(self.burst_number.get())
        
        for x in range(0,settings[22][1]):
            settings[23+x][1] = int(self.measurement_burst[x])
            settings[33+x][1] = int(self.pulse_burst[x])
        
        #save_settings_var() # save settings to main class attributes   
        settings_open = open(self.settings_file, 'w')
        with settings_open:
           csv_writer = csv.writer(settings_open, delimiter = ',')
           csv_writer.writerows(settings)
        A = float(settings[15][1])
        B1 = float(settings[16][1])
        B2 = float(settings[17][1])/1000
        B3 = float(settings[18][1])/1000000
        B4 = float(settings[19][1])/1000000000
        B5 = float(settings[20][1])/1000000000000
        
        
        #global wavelength
        #initialize wavelength array with zeros then solve given pixel coefficients
        self.wavelength = np.zeros(288)
        for pixel in range(1,289,1):
            self.wavelength[pixel-1] = A + B1*pixel + B2*(pixel**2) + B3*(pixel**3) + B4*(pixel**4) + B5*(pixel**5)
        self.settings_popup.destroy()
        
    def autoscale(self): # just a visual change to keep the button "pushed" and used for graphing purposes
            if self.autoscale_button['relief'] == SUNKEN:
                self.autoscale_button.config(bg = 'light grey', relief = RAISED)
            else:
                self.autoscale_button.config(bg = 'gold', relief = SUNKEN)
                
    def key_pad(self,number):
        self.keypad = Toplevel(root)
        path = '/home/pi/Desktop/Spectrometer/'
        big_font = ('Times New Roman', 24)
        
        self.keypad.title('Input New FileName into entry box')
        #if full_screen == True:
        #self.key_pad.attributes('-fullscreen', True) # fullscreen on touchscreen
        size = str(self.w-300) + 'x' + str(self.h - 300)
        self.keypad.geometry('680x400')
            
        keypad_frame = Frame(self.keypad)
        keypad_frame.grid(row = 0, column = 0, columnspan = 10, sticky = 'nsew')
        key = StringVar()
        key_entry = Entry(keypad_frame, textvariable =key, font = big_font, justify = CENTER, )
        key_entry.grid(row = 0, column = 0, sticky = 'nsew')
        
        def press(letter):
            global current
            current = key.get()
            key.set('')
            current = str(current) + str(letter)
            key.set(current)
        def back():
            self.keypad.destroy()
            
        def key_pad_delete():
            global current
            current = current[:-1] # Remove last digit
            key.set(current)
        
        def key_pad_save(number):
            if number == 1:
                #try:
                self.exp_folder = str(path + key.get())
                if not os.path.exists(self.exp_folder):
                    os.makedirs(self.exp_folder)
                self.save_file = str(self.exp_folder + '/' + key.get() +'_save.csv')
                open(self.save_file, 'w+')
                    
                #create data frame for saving data to csv files
                self.df = pd.DataFrame(self.wavelength)
                self.df.columns = ['Wavelength (nm)']
                save_csv = self.df.to_csv(self.save_file, mode = 'a', index=False)
                root.title("ESS System Interface: " + self.save_file)
                # reset scan and ref number for saving data when new file created
                self.scan_number = 1
                self.reference_number = 1
                    
                self.keypad.destroy()
                self.acquire_save_button.config(state = DISABLED)
                self.save_reference_button.config(state = NORMAL)
                self.save_spectra_button.config(state = NORMAL)
                self.open_loop_button.config(state = NORMAL)
                self.sequence_save_button.config(state = NORMAL)
                #except :
                #self.keypad.destroy()
                #messagebox.showerror("Error", "File Name already Exists! Please enter New Filename")
            elif number ==2:
                try:
                    spectra_save_file = self.exp_folder + '/' + key.get() + '.csv'
                    open(spectra_save_file, 'w+')
                    settings_open = open(self.settings_file, 'r')
                    csv_reader = csv.reader(settings_open, delimiter=',')
                    settings = list(csv_reader)
                    integ_time = int(settings[3][1])
                    integ = b"set_integ %0.6f\n" % integ_time
                    self.ser.write(integ)
                    sleep(1)
                    self.ser.write(b"read\n")
                    #save to pseudo files
                    data = self.ser.readline()
                    data_array = np.array([int(d) for d in data.split(b",")])
                    pixel = np.arange(288).reshape(288,1)
                    data_saved = np.column_stack([self.wavelength, data_array])                
                    #create header string to add to final saved csv_file
                    name = "wavelength, Saved Spectra"
                    np.savetxt(spectra_save_file, data_saved, fmt="%d", delimiter=",", header = name)
                
                    pixel = range(0,288,1)
                    plt.plot(pixel, data_array, '-.')
                    self.fig.canvas.draw()
                    self.keypad.destroy()
                except ValueError:
                    self.keypad.destroy()
                    messagebox.showerror("Error", "File Name already Exists! Please enter New Filename")
            elif number ==3:  
                # if there is no experiment folder save to spectrometer main folder
                if self.exp_folder is not None:
                    self.sequence_file = str(self.exp_folder + '/' + key.get() +'_sequence.csv')
                else:
                    self.sequence_file = str(self.folder+ '/' + key.get() +'_sequence.csv')
                    
                open(self.sequence_file, 'w+')
                #create data frame for saving data to csv files
                self.df_seq = pd.DataFrame(self.wavelength)
                self.df_seq.columns = ['Wavelength (nm)']
                seq_csv = self.df_seq.to_csv(self.sequence_file, mode = 'a', index=False)
                root.title("ESS System Interface: " + self.sequence_file)
                #reset scan and ref number for saving data 
                self.keypad.destroy()
                '''
                except:
                    self.keypad.destroy()
                    messagebox.showerror("Error", "File Name already Exists! Please enter New Filename")
                '''
            elif number ==4:
                 # if there is no experiment folder save to spectrometer main folder
                if self.exp_folder is not None:
                    self.scan_file = str(self.exp_folder + '/' + key.get() +'_scan.csv')
                else:
                    self.scan_file = str(self.folder+ '/' + key.get() +'_scan.csv')
                    
                open(self.scan_file, 'w+')
                #create data frame for saving data to csv files
                self.df_scan = pd.DataFrame(self.wavelength)
                self.df_scan.columns = ['Wavelength (nm)']
                scan_csv = self.df_scan.to_csv(self.scan_file, mode = 'a', index=False)
                #root.title("ESS System Interface: " + self.scan_file)
                #reset scan and ref number for saving data 
                self.keypad.destroy()
                
        btn_list = [
        '1', '2', '3', '4', '5', '6','7', '8', '9', '0',
        'Q', 'W', 'E','R', 'T', 'Y', 'U', 'I', 'O','P',
        'A', 'S', 'D','F', 'G', 'H', 'J', 'K', 'L','bkspce',
        'Z', 'X', 'C','V', 'B', 'N', 'M', '_', 'BACK','OK']
    
        r = 1
        c = 0
        n = 0
    
        btn = list(range(len(btn_list)))
        
        for label in btn_list:
            btn[n] = Button(self.keypad, text = label, width = 5, height = 4)
            btn[n].grid(row = r, column = c, sticky = 'nsew')
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
        btn[38].configure(command = back)
        btn[39].configure(command = lambda: key_pad_save(number))
        
        self.keypad.grid_columnconfigure((0,1,2,3,4,5,6,7,8,9), weight = 2)
        self.keypad.grid_rowconfigure((1,2,3,4), weight = 2)
        keypad_frame.grid_rowconfigure((0), weight = 1)
        keypad_frame.grid_columnconfigure((0), weight = 1)
        
    def add_remove_plots(self):
        self.add_remove = Toplevel(root)
        self.add_remove.title('Select plot(s) to view')
        self.add_remove.geometry('325x380')
        self.add_remove.config(bg = "sky blue")
        # create frames for 2 different listboxes
        select_frame = Frame(self.add_remove, bg = 'sky blue')
        select_frame.grid(row = 0, column = 1)
    
        
        
        #create function to save the selected plot names and plot them
        def save_selected():
            data = pd.read_csv(self.save_file, header = 0)
            self.data_headers = [lb.get(idx) for idx in lb.curselection()]
            self.reference_ratio = lb_reference.get(lb_reference.curselection()) # get reference selected and save name
            self.reference_ratio_idx = lb_reference.curselection()
            self.ref = self.df[[self.reference_ratio]].to_numpy() # save selected reference to use for ratio conversion
            #check if the data headers is empty to set to none for future plotting 
            if self.data_headers == []:
                self.data_headers = None
                self.data_headers_idx = None
                self.plot_selected_button.config(state =DISABLED)
            else:
                self.data_headers_idx = lb.curselection()
                self.plot_selected_button.config(state =NORMAL)
            self.add_remove.destroy()
            
        def select_all():
            lb.select_set(0, END)
        def unselect_all():
            lb.select_clear(0, END)
             
        #add listbox with scrollbar to select data to be plotted 
        lb = Listbox(select_frame, selectmode = MULTIPLE)
        scrollbar = Scrollbar(select_frame)
        scrollbar.config(command = lb.yview)
        scrollbar.grid(row = 0, column = 3, sticky = N+S)
        lb.configure(width = 15, height = 10,
                     font=("Times New Roman", 14),
                     yscrollcommand = scrollbar.set,
                     exportselection = False)
        
        lb_reference = Listbox(select_frame, selectmode = SINGLE)
        #create reference listbox with scroll bar to select reference to be used 
        scrollbar_ref =Scrollbar(select_frame)
        scrollbar_ref.config(command = lb_reference.yview)
        scrollbar_ref.grid(row = 0, column = 1, sticky = N+S)
        lb_reference.configure(width = 15, height = 10,
                               font=("Times New Roman", 14),
                               yscrollcommand = scrollbar_ref.set,
                               exportselection = False)
        
        
        data_pd = pd.read_csv(self.save_file)
        # get col header names to add to listbox text
        data_headers_dummy = list(data_pd.columns.values)
        for col in range(1, len(data_headers_dummy),1):
            lb.insert('end', data_headers_dummy[col])
        
        lb.grid(row = 0, column = 2)
        #select previously selected 
        if self.data_headers_idx is not None:
            for i in self.data_headers_idx:
                lb.selection_set(i)
        
                
        #find all reference columns then insert into the listbox
        reference_headers = [i for i in data_headers_dummy if i.startswith('Reference')]
        for col in range(0, len(reference_headers),1):
            lb_reference.insert('end', reference_headers[col])
        lb_reference.grid(row = 0, column = 0)
        
        if self.reference_ratio_idx is not None:
            lb_reference.selection_set(self.reference_ratio_idx)
        else:
            lb_reference.selection_set(END)
            
        save_selected_button = Button(select_frame, text = 'Save Selected', width = 20, height = 2, command = save_selected)
        save_selected_button.grid(row = 1, column = 0, columnspan = 4)
        select_all_button = Button(select_frame, text = 'Select_all', width = 20, height = 2, command = select_all)
        select_all_button.grid(row = 2, column = 0, columnspan = 4)
        Unselect_all_button = Button(select_frame, text = 'Un-Select_all', width = 20, height = 2, command = unselect_all)
        Unselect_all_button.grid(row = 3, column = 0, columnspan = 4)
    
        
    def on_off_led(self):
        self.ser.write(b"ON\n")
        sleep(2)
        self.ser.write(b"OFF\n")
        sleep(2)
        
        
    def quit_button(self):
        try:
            self.ser.reset_output_buffer()
            self.ser.reset_input_buffer()
            self.ser.close()
            root.destroy()
        except:
            root.destroy()
        
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
        
# Actually create window with all the above functionality
root = Tk()
my_gui = Main_GUI(root)
root.mainloop()
'''
try:
    root = Tk()
    my_gui = Main_GUI(root)
    root.mainloop()
except:
    messagebox.showerror("Error", "Spectrometer Not connected. Connect and Try Again")
    root.destroy()
'''