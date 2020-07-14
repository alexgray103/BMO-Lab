from tkinter import *
import matplotlib.pyplot as plt
import ESS_GUI_module
import serial
from settings import Settings as _Settings
import pandas as pd
import numpy as np
import csv
from keyboard import *
from tkinter.filedialog import askopenfilename
import os



################# Global Variables ############################
global settings_file
global acquire_file
global path

settings_file = '/home/pi/Desktop/Spectrometer/settings/settings.csv'
acquire_file = '/home/pi/Desktop/Spectrometer/settings/acquire_file.csv'
path = '/home/pi/Desktop/Spectrometer/'
#################################################################


class functions:
    def __init__(self, parent, _canvas, figure, df):
        global settings_file
        global acquire_file
        self.parent = parent # whatever parent 
        self.save_file = None # initalize file for saving data
        self.scan_number = 0 # ID for saving to csv
        self.reference_number = 0 # ref ID for saving to csv
    
        
        # these are two possible port names for the arduino attachment
        port = "/dev/ttyUSB0"
        port2 = "/dev/ttyUSB1"
        try:
            self.ser = serial.Serial(port, baudrate = 115200, timeout = 3)
        except:
            self.ser = serial.Serial(port2, baudrate = 115200, timeout =3)
        # two pseudo reads to initalize the spectrometer
        self.ser.write(b'read\n')
        data = self.ser.readline()
        self.ser.write(b'read\n')
        data = self.ser.readline()
        
        # intialize attributes for handling data and files
        self.acquire_file = acquire_file
        self.settings_file = settings_file
        self.df = df
        self.canvas = _canvas
        self.fig = figure
        self.settings_func = _Settings(settings_file)
        (self.settings, self.wavelength) = self.settings_func.settings_read()
    
    def open_new_experiment(self):
        global path
        keyboard = key_pad(self.parent)
        try:
            (save_file, save_folder) = keyboard.create_keypad()
            self.save_file = save_folder + '/' + save_file
        
            self.exp_folder = str(save_folder)
            if not os.path.exists(self.exp_folder):
                os.makedirs(self.exp_folder)
        
            open(self.save_file, 'w+')
            
            #create data frame for saving data to csv files
            self.df = pd.DataFrame(self.wavelength)
            self.df.columns = ['Wavelength (nm)']
            save_csv = self.df.to_csv(self.save_file, mode = 'a', index=False)
            # reset scan and ref number for saving data when new file created
            self.scan_number = 1
            self.reference_number = 1
        except NameError:
            pass
                       
    def plot_selected(self):
        plt.clf()
        x = range(0,288)
        plt.plot(x,self.wavelength)
        self.fig.canvas.draw()
        
    def dark_subtract_func(self):
        (self.settings, self.wavelength) = self.settings_func.settings_read()
        number_avg = int(self.settings[11][1])
        integ_time =float(self.settings[3][1])
        smoothing_used = int(self.settings[12][1])
        smoothing_width = int(self.settings[8][1])
        pulses = int(self.settings[1][1])
        dark_subtract = int(self.settings[4][1])
        
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
        if smoothing_used == 1:  # if smoothing is checked smooth array
            dummy = np.ravel(data_dark)
            for i in range(0,len(data_dark)-smoothing_width,1):
                data_dark[i] = sum(np.ones(smoothing_width)
                                       *dummy[i:i+smoothing_width])/(smoothing_width)
        return data_dark
    
    def acquire_avg(self):
        (self.settings, self.wavelength) = self.settings_func.settings_read()
        number_avg = int(self.settings[11][1])
        integ_time =float(self.settings[3][1])
        smoothing_used = int(self.settings[12][1])
        smoothing_width = int(self.settings[8][1])
        pulses = int(self.settings[1][1])
        dark_subtract = int(self.settings[4][1])
            
        if dark_subtract == 1:
            data_dark = self.dark_subtract_func()
        else: 
            data_dark = 0
                
        self.ser.write(b"set_integ %0.6f\n" % integ_time)
        self.ser.write(b"pulse %d\n" % pulses)
            
        # tell spectromter to send data
        data = 0
        for x in range(0,number_avg,1): #take scans then average
            self.ser.write(b"read\n") # tell arduino to read spectrometer
            data_read = self.ser.readline()
            data_temp = np.array([int(p) for p in data_read.split(b",")])
            data = data + data_temp 
            
            if x == number_avg-1:  # reached number of averages
                data = data/number_avg #take average of data and save
                if smoothing_used == 1:  # if smoothing is checked smooth array
                    dummy = np.ravel(data)
                    for i in range(0,len(data)-smoothing_width,1):
                        data[i] = sum(np.ones(smoothing_width)
                                        *dummy[i:i+smoothing_width])/(smoothing_width)
        data = data-data_dark        
        return data
    
    def acquire(self, save):
        data = self.acquire_avg()
        # if acquire and save, save to save_file csv 
        if save:
            df_data_array = pd.DataFrame(data)
            self.df['Scan_ID %d' %self.scan_number] = df_data_array
            self.df.to_csv(self.save_file, mode = 'w', index = False)
            data = self.df[['Scan_ID %d' %self.scan_number]]
            self.scan_number = 1 + self.scan_number
            self.ratio_view_button.config(state = NORMAL)
        else: # if only acquire save to temporary file
            np.savetxt(self.acquire_file, data, fmt="%d", delimiter=",")
            data = pd.read_csv(self.acquire_file, header = None)
            # get selected data arrays for plotting
        plt.clf()
        plt.plot(self.wavelength, data)
        self.fig.canvas.draw()
        '''
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
        '''
    def open_loop(self):
        x = 1
    def open_loop_state():
        if self.open_loop_stop is not None:
            self.open_loop_button.config(command = open_loop, relief = RAISED, bg = 'light grey')
            root.after_cancel(self.open_loop_stop)
            
    def OpenFile(self):
            
        save_file = askopenfilename(initialdir="/home/pi/Desktop/Spectrometer",
                                    filetypes =(("csv file", "*.csv"),("All Files","*.*")),
                                    title = "Choose a file.")
        #try:
        if save_file: # check if file was selected if not dont change experiment file
            self.save_file = save_file 
                
            # try to scan through reference and scan number to set to correct value for further saving
            self.df = pd.read_csv(self.save_file, header = 0)
            headers = list(self.df.columns.values)
    
        #find the scan number from the opened file
        # only works for files with the specified headers
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
            
            #reset indexing attrubtues for later use in
            #add remove functions 
            self.data_headers_idx = None
            self.data_headers = None
            self.reference_ratio = None
            self.reference_ratio_idx = None
            self.parent.open_loop_button.config(state = NORMAL)
        #except:
        #messagebox.showerror("Error", "Oops! Something went wrong. Try Again!")
    