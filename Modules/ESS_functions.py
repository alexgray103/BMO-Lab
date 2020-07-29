from tkinter import *
from tkinter.ttk import *
import matplotlib.pyplot
import time

# modules
from ESS_GUI_module import *
import serial
from settings import Settings as _Settings
from keyboard import *
from add_remove_popup import *

import pandas as pd
import numpy as np
import csv
from tkinter import messagebox

from tkinter.filedialog import askopenfilename
import os
import matplotlib.pyplot as plt


################# Global Variables ############################
global settings_file
global acquire_file
global path

settings_file = '/home/pi/Desktop/Spectrometer/settings/settings.csv'
acquire_file = '/home/pi/Desktop/Spectrometer/settings/acquire_file.csv'
path = '/home/pi/Desktop/Spectrometer/'
#################################################################


class functions:
    def __init__(self, parent, _canvas, figure):
        global settings_file
        global acquire_file
        global ESS_module
        self.parent = parent # whatever parent 
        self.save_file = None # initalize file for saving data
        self.scan_number = 1 # ID for saving to csv
        self.reference_number = 1 # ref ID for saving to csv
        self.exp_folder = '/home/pi/Desktop/Spectrometer' # experiment folder used for saving
        self.df = None # data frame array used for storing and plotting data
        
        # attributes to select data to be plotted
        self.ref = np.ones((288,1))*1000 # temporary reference
        
        # plotting view attributes
        self.ratio_view_handler = False
        self.autoscale_handler = False
        
            
        # these are two possible port names for the arduino attachment
        port = "/dev/ttyUSB0"
        port2 = "/dev/ttyUSB1"
        try:
            self.ser = serial.Serial(port, baudrate = 115200, timeout = 3)
        except:
            self.ser = serial.Serial(port2, baudrate = 115200, timeout =3)
        
        # two pseudo reads to initalize the spectrometer
        self.ser.write(b"read\n")
        data = self.ser.readline()
        self.ser.write(b"read\n")
        data = self.ser.readline()
        
        # intialize attributes for handling data and files
        self.acquire_file = acquire_file
        self.settings_file = settings_file
        self.canvas = _canvas
        self.fig = figure
        
        # create objects for different modules needs for some functions
        self.settings_func = _Settings(settings_file)
        (self.settings, self.wavelength) = self.settings_func.settings_read()
        self.add_remove_top = add_remove_popup(self.parent)
        
        
    def save_reference(self):
        try:
            self.ref = pd.DataFrame(np.loadtxt(self.acquire_file, delimiter = ','))
            self.df['Reference %d' % self.reference_number] = self.ref
            self.df.to_csv(self.save_file, mode = 'w', index = False)
            self.reference_number = self.reference_number +1 
        except TypeError:
            messagebox.showerror('Error', 'No Save File selected, create save file to save data')
    
    def save_spectra(self):
        keyboard = key_pad(self.parent)
        try:
            (save_file, save_folder) = keyboard.create_keypad()
            self.save_file = self.exp_folder + '/' + save_file + "_spectra.csv"
            
            open(self.save_file, 'w+')
            
            #create data frame for saving data to csv files
            spectra = pd.DataFrame(self.wavelength)
            spectra.columns = ['Wavelength (nm)']
            spectra['Saved Spectra'] = np.loadtxt(self.acquire_file, delimiter = ',')
            spectra.to_csv(self.save_file, mode = 'a', index=False)
            # reset scan and ref number for saving data when new file created
        
        except NameError:
           messagebox.showerror("Error", "No Filename Found! Please input again to create Experiment")
        
        
    def add_remove_func(self):
        self.add_remove_top.create_add_remove(self.save_file)
        
        if self.add_remove_top.ref_ratio is not None:
            self.ref = self.df[[self.add_remove_top.ref_ratio]].to_numpy() 
        
    def ratio_view(self):
        self.ratio_view_handler = not self.ratio_view_handler
    
    def autoscale(self):
        self.autoscale_handler = not self.autoscale_handler
        if self.autoscale_handler:
            plt.autoscale(enable= True, axis = 'y')
            self.fig.canvas.draw()
        elif not self.autoscale_handler and self.ratio_view_handler:
            plt.autoscale(enable = False, axis = 'y')
            plt.ylim(0,110)
            self.fig.canvas.draw()
        else:
            plt.autoscale(enable = False, axis = 'y')
            plt.ylim(0,66500)
            self.fig.canvas.draw()
    
    def plot_labels_axis(self):
        plt.subplots_adjust(bottom =0.14, right = 0.95, top = 0.96)

        if self.ratio_view_handler:
            plt.plot(self.wavelength, np.ones((288,1))*100, 'r--')
            if not self.autoscale_handler:
                plt.ylim(0,110)
            plt.xlim(300,900)
            plt.xlabel('Wavelength (nm)')
            plt.ylabel('Ratio (%)')
        elif not self.ratio_view_handler:
            if not self.autoscale_handler:
                plt.ylim(0,66500)
            plt.xlim(300,900)
            plt.xlabel('Wavelength (nm)')
            plt.ylabel('ADC counts')
        #self.fig.canvas.draw()
        
    def plotting(self, data):
        
        self.plot_labels_axis() # configure axis
        
        if self.ratio_view_handler:
            data = np.true_divide(data, self.ref)*100
            if self.add_remove_top.data_headers is not None:

                data_sel = pd.read_csv(self.save_file, header = 0)
                data_sel = data_sel[self.add_remove_top.data_headers]
                data_sel = np.true_divide(data_sel,self.ref)*100
                plt.plot(self.wavelength, data_sel)
                plt.legend(self.add_remove_top.data_headers, loc = "upper right", prop = {'size': 6})
        else:
            if self.add_remove_top.data_headers is not None:
                data_sel = pd.read_csv(self.save_file, header = 0)
                data_sel = data_sel[self.add_remove_top.data_headers]
                plt.plot(self.wavelength, data_sel)
                plt.legend(self.add_remove_top.data_headers, loc = "upper right", prop = {'size': 6})
            else:
                pass
        plt.plot(self.wavelength,self.ref, 'r--', label = 'Reference')
        plt.plot(self.wavelength, data)
        plt.xlim(int(self.settings[9][1]), int(self.settings[10][1]))
        self.fig.canvas.draw()
        
    def open_new_experiment(self):
        global path
        keyboard = key_pad(self.parent)
        try:
            (save_file, save_folder) = keyboard.create_keypad()
            self.save_file = save_folder + '/' + save_file + "_save.csv"
        
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
           messagebox.showerror("Error", "No Filename Found! Please input again to create Experiment")
                       
    def plot_selected(self):
        plt.clf()
        self.plot_labels_axis()
        try:
            plt.plot(self.wavelength, self.df[self.add_remove_top.data_headers])
            plt.legend(self.add_remove_top.data_headers, loc = "upper right", prop ={'size': 6})
            plt.subplots_adjust(bottom =0.14, right = 0.95)
            self.fig.canvas.draw()
        except:
            messagebox.showerror('Error','No data selected. Select data to plot')
    
    def clear(self):
        plt.clf()
        plt.ylim(0,66500)
        plt.xlim(300,900)
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('ADC Counts')
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
        data_dark = np.array([int(i) for i in data_read.split(b",")])
        
        #if x == 0:  # reached number of averages
        #data_dark = data_dark #take average of data and save
        if smoothing_used == 1:  # if smoothing is checked smooth array
            dummy = np.ravel(data_dark)
            for i in range(0,len(data_dark)-smoothing_width,1):
                data_dark[i] = sum(np.ones(smoothing_width)
                                       *dummy[i:i+smoothing_width])/(smoothing_width)
        return data_dark
    
    def acquire_avg(self, pulses):
        (self.settings, self.wavelength) = self.settings_func.settings_read()
        number_avg = int(self.settings[11][1])
        integ_time =float(self.settings[3][1])
        smoothing_used = int(self.settings[12][1])
        smoothing_width = int(self.settings[8][1])
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
        for idx in range(0,len(data)):
            if data[idx] <0:
                data[idx] = 1
        return data
    
    def acquire(self, save):
        (self.settings, self.wavelength) = self.settings_func.settings_read()
        data = self.acquire_avg(int(self.settings[1][1]))
        if save:
            if self.save_file == None:
                messagebox.showerror('Error', 'No Experiment File Found, create or open File to save Data')
            else:
                # save data array to save_file
                df_data_array = pd.DataFrame(data)
                self.df['Scan_ID %d' %self.scan_number] = df_data_array
                self.df.to_csv(self.save_file, mode = 'w', index = False)
                data = self.df[['Scan_ID %d' %self.scan_number]]
                self.scan_number = 1 + self.scan_number
                
        else: # temporary save
            np.savetxt(self.acquire_file, data, fmt="%d", delimiter=",")
            data = pd.read_csv(self.acquire_file, header = None)
        plt.clf()
        self.plotting(data)
    
    def open_loop_function(self):
        plt.xlim(int(self.settings[9][1]), int(self.settings[10][1]))
        plt.ylabel('ADC counts')
        plt.xlabel('Wavelength (nm)')
        
        plt.clf()
        data = self.acquire_avg(0)
        np.savetxt(self.acquire_file, data, fmt="%d", delimiter= ",")
        self.plotting(data)
        
    def sequence(self, save):
        (self.settings, self.wavelength) = self.settings_func.settings_read()       
        if save:
            #try:
            keyboard = key_pad(self.parent)
            (seq_file, save_folder) = keyboard.create_keypad()
            self.seq_file = self.exp_folder + '/' + seq_file + '_sequence.csv'
            open(self.seq_file, 'x')
                
            self.df_seq = pd.DataFrame(self.wavelength)
            self.df_seq.columns = ['Wavelength (nm)']
            self.df_seq.to_csv(self.seq_file, mode = "a", index = False)
            #except:
            #messagebox.showerror("Error", "No Filename found! Please input file name to save Sequence")
        else:
            pass
        number_avg = int(self.settings[11][1])
        integ_time = int(self.settings[3][1])
        smoothing_used = int(self.settings[12][1])
        smoothing_width = int(self.settings[8][1])
        dark_subtract = int(self.settings[4][1])
        burst_number = int(self.settings[22][1])
        burst_delay = float(self.settings[21][1])
        
        plt.xlim(int(self.settings[9][1]), int(self.settings[10][1]))
        
        for burst in range(0,burst_number):
            number_measurements_burst = int(self.settings[23+burst][1])
            measurement = 0
            for i in range(0,number_measurements_burst):
                graph_label = 'Burst ' + str(burst+1) + ' measurement ' + str(i+1)
                pulses = int(self.settings[33+burst][1])
                data = self.acquire_avg(pulses)
    
                plt.plot(self.wavelength, data, label = graph_label)
                plt.subplots_adjust(bottom = 0.14, right = 0.95)
                plt.legend(loc = "center right", prop = {'size': 6})
                self.fig.canvas.draw()
                measurement = measurement+1
                
                if save:
                    df_data_array = pd.DataFrame(data)
                    self.df_seq['Burst %d Measurement %d' % (burst+1, measurement)] = df_data_array
            sleep(burst_delay)
        # after all data is taken save to sequence csv
        if save:
            self.df_seq.to_csv(self.seq_file, mode = 'w', index = False)
    
    def autorange(self):
        (self.settings, self.wavelength) = self.settings_func.settings_read()       
        max_autorange = int(self.settings[7][1])
        autorange_thresh = int(self.settings[6][1])
        integ_time = int(self.settings[3][1])
        pulses = 1 # start with one pulse then increment
        plt.clf()
        
        plt.xlim(int(self.settings[9][1]), int(self.settings[10][1])) # change x axis limits to specified settings
        plt.ylabel('a.u.')
        plt.xlabel('Wavelength (nm)')
        # acquire data for the given # of loops plot, and prompt user to
        # select plots they wish to save with a popup window
        for x in range(0,max_autorange): 
            self.settings[1][1] = pulses
            # write settings array to csv 
            self.settings_func.settings_write(self.settings)
            data = self.acquire_avg(pulses)
            if max(data) < autorange_thresh:  
                if x < max_autorange-1:
                    pulses = pulses+1
                    plt.plot(self.wavelength,data, label = "Pulses: "+ str(self.settings[1][1]))
                    plt.subplots_adjust(bottom=0.14, right=0.86)
                    plt.legend(loc = "center right", prop={'size': 7}, bbox_to_anchor=(1.18, 0.5))
                    self.fig.canvas.draw()
                else: 
                    messagebox.showinfo("Pulses", "Max # of Pulses reached")
            else:
                self.settings[1][1] = pulses-1
                messagebox.showinfo("Pulses", str(self.settings[1][1]) + "  Pulses to reach threshold")
                break
        self.settings_func.settings_write(self.settings)
        
    def OpenFile(self):
            
        save_file = askopenfilename(initialdir="/home/pi/Desktop/Spectrometer",
                                    filetypes =(("csv file", "*.csv"),("All Files","*.*")),
                                    title = "Choose a file.")
        #try:
        if save_file: # check if file was selected if not dont change experiment file
            self.save_file = save_file 
            self.reference_number = 1
            self.scan_number = 1
            
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
            self.add_remove_top.data_headers_idx = None
            self.add_remove_top.data_headers = None
            self.add_remove_top.ref_ratio = None
            self.add_remove_top.ref_ratio_idx = None
            
    def scan(self, save):
        self.scan_file = []
        self.plot_labels_axis() # set axis and labels
        (self.settings, self.wavelength) = self.settings_func.settings_read()
        print('hello')
        if save:
            try:
                keyboard = key_pad(self.parent)
                (scan_file, save_folder) = keyboard.create_keypad()
                self.scan_file = self.exp_folder + '/' + scan_file + '_scan.csv'
                open(self.scan_file, 'x')
                
                self.df_scan = pd.DataFrame(self.wavelength)
                self.df_scan.columns = ['Wavelength (nm)']
                self.df_scan.to_csv(self.scan_file, mode = "a", index = False)
            except FileExistsError:
                messagebox.showerror('Error', 'FileName already Exists try again with different Filename')
        else:
            pass
        grid_size = int(self.settings[14][1])
        scan_resolution = int(self.settings[13][1])
        start = time.time()
        def scan_move():
            for x in range(0,grid_size):
                for y in range(0,grid_size):
                    idx = (x*grid_size) + y
                                
                    data = self.acquire_avg(int(self.settings[1][1]))
                    df_data_array = pd.DataFrame(data)
                    if (x % 2) == 0:
                        idx = (x*grid_size) + y
                        self.ser.write(b"y 0\n") # move in y after one scan
                        self.df_scan['X: %d Y: %d' % (x, y)] = df_data_array

                    else:
                        idx = (x*grid_size) + grid_size - y -1
                        self.ser.write(b"y 1\n")
                        self.df_scan['X: %d Y: %d' % (x, grid_size-y-1)] = df_data_array

                    self.button[idx].configure(bg = 'Green')
                    self.parent.update_idletasks()
                    self.progress_popup.update_idletasks()


                self.ser.write(b"x\n")
            
            self.ser.write(b"home\n")
            self.progress_popup.destroy()
            plt.plot(self.wavelength, self.df_scan)
            self.fig.canvas.draw()
            self.df_scan.to_csv(self.scan_file, mode = 'w', index = False)
            end = time.time()
            print(end-start)
        
        self.progress_popup = Toplevel(self.parent, bg = 'sky blue')
        self.progress_popup.focus_force()
        self.progress_popup.geometry('450x450')
        self.button = list(range(0,grid_size**2 +1))
        
        for x_button in range(0,grid_size):
            for y_button in range(0, grid_size):
                idx = (x_button*grid_size) + y_button
                self.button[idx] = Button(self.progress_popup, bg = 'red', width = 1, height = 1)
                self.button[idx].grid(row = 1+y_button, column = x_button, sticky = 'nsew')

        start_button = Button(self.progress_popup, fg = 'black', command = scan_move, text = 'Scan')
        start_button.grid(row = 0, column = 0, columnspan = grid_size)
        #self.progress_popup.rowconfigure(0, weight = 2)
        self.progress_popup.columnconfigure(0, weight =1)
        for i in range(1,grid_size+1):
            self.progress_popup.rowconfigure(i, weight = 1)
            self.progress_popup.columnconfigure(i-1, weight =1)