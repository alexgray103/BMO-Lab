## creating GUI
from tkinter import *
import numpy as np #https://scipy-lectures.org/intro/numpy/operations.html
from tkinter import messagebox
import os
from tkinter.filedialog import askopenfilename
from astropy.convolution import convolve, Box1DKernel


#used for serial comm with arduino
import serial
from time import sleep
import time
 

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

#only needed for external ADC and acquire with RPI
import RPi.GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
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
        global ser
        port = "/dev/ttyACM0"
        port2 = "/dev/ttyACM1"
        try:
            ser = serial.Serial(port, baudrate = 115200, timeout = 3)
        except:
            ser = serial.Serial(port2, baudrate = 115200, timeout =3)
        
        # allow serial port to initialize for spectrometer
        sleep(1.5)

        # initialize file for saving values
        global filename
        global foldername
        global settings_file
        global save_file
        global reference_file
        global wavelength
        global pixel
        
        #used for saving to csv with headers of increasing ID number
        global scan_number
        global reference_number
        scan_number = 1
        reference_number = 1
        
        
        #Used for selection of plots
        global data_headers
        global data_headers_idx
        data_headers_idx = None
        data_headers = None
        
        #dataframe to save all values
        global df
        
        pixel = np.arange(1,289)
        '''
        A = 335.2446842
        B1 = 2.688494791
        B2 = -8.964262020*(10**-4)
        B3 = -1.03088017*(10**-5)
        B4 = 2.083514791*(10**-8)
        B5 = -1.290505933*(10**-11)
        '''
        wavelength = pixel
        
        #create spectrometer folder to store all data and settings
        folder_path = '/home/pi/Desktop/Spectrometer'
        folder_settings = '/home/pi/Desktop/Spectrometer/settings'
        
        if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                
        if not os.path.exists(folder_settings):
                os.makedirs(folder_settings)
                
        # create acquire pseudo file if not already within spectrometer folder
        file_acquire = '/home/pi/Desktop/Spectrometer/settings/acquire.csv'
        try:
            #create pseudo files
            open_acquire_file = open(file_acquire, 'x')
        except:
            open_acquire_file = open(file_acquire, 'a')
        
        # intialize arduino with one pseudo read (first read is always noisy)
        ser.write(b'read\n')
        data = ser.readline()
        
        # Check if there is already a settings folder,
        #otherwise create new with default settings into Spec Folder
        #create settings file
        settings_file = '/home/pi/Desktop/Spectrometer/settings/settings.csv'
        try:
            open(settings_file, 'r')
        except:
            open(settings_file, 'x')
            settings_open = open(settings_file, 'w', newline = '')
            csv_row = [('Settings', ''),('pulse',1),('pulse_rate',60),\
                   ('integration_time',300),('dark_subtract',1),\
                   ('lamp_voltage',1000), ('autopulse_threshold',52000),\
                   ('max_autopulse_number',10),('smoothing_half_width',2),\
                   ('min_wavelength',300),('max_wavelength',900),\
                   ('Number_of_Averages', 2), ('smoothing', 1),\
                   ('a_0', 311.1585037), ('b_1', 2.706594330),\
                   ('b_2', -1.292296203), ('b_3', -6.644532253),\
                   ('b_4', 5.749476565), ('b_5', 9.954642163)]
            with settings_open:
                csv_writer = csv.writer(settings_open, delimiter = ',')
                csv_writer.writerows(csv_row)
                
        # read settings csv and return list of settings
        def settings_read():
                settings_open = open(settings_file, 'r')
                csv_reader = csv.reader(settings_open, delimiter=',')
                settings = list(csv_reader)
                return settings
            
        def acquire_avg():  # function to acquire data from spectrometer (multiple scans)
            # open settings and send integ time to spectrometer 
            settings = settings_read()
            number_avg = int(settings[11][1])
            integ_time = int(settings[3][1])
            smoothing_used = int(settings[12][1])
            smoothing_width = int(settings[8][1])
            ser.write(b"set_integ %0.6f\n" % integ_time)
            sleep(0.5)
            # tell spectromter to send data
            data = 0
            for x in range(0,number_avg,1): #take scans then average
                ser.write(b"read\n")
                #read data and save to pseudo csv to plot
                data_read = ser.readline()
                #data = ser.read_until('\n', size=None)
                data_temp = np.array([int(p) for p in data_read.split(b",")])
                data = data + data_temp
                if x == number_avg-1:  # reached number of averages
                    data = data/number_avg #take average of data and save
                    if smoothing_used == 1:  # if smoothing is checked smooth array
                        dummy = np.ravel(data)
                        for i in range(0,len(data)-smoothing_width,1):
                            data[i] = sum(np.ones(smoothing_width)*dummy[i:i+smoothing_width])/(smoothing_width)
                    return data
            
        def OpenFile():
            global save_file
            global reference_number
            global scan_number
            global df
            save_file = askopenfilename(initialdir="/home/pi/Desktop/Spectrometer",
                           filetypes =(("csv file", "*.csv"),("All Files","*.*")),
                           title = "Choose a file."
                           )
            df = pd.read_csv(save_file, header = 0)
            headers = list(df.columns.values)
            #find the scan number from the opened file
            while True:
                result = [i for i in headers if i.startswith('Scan_ID %d' %scan_number)]
                if result == []:
                    break
                scan_number = scan_number+1
            while True:
                result = [i for i in headers if i.startswith('Reference %d' %reference_number)]
                if result == []:
                    break
                reference_number = reference_number+1
                
            self.save_spectra_button.config(state = NORMAL)
            self.save_reference_button.config(state = NORMAL)
            self.acquire_save_button.config(state = NORMAL)
            self.plot_selected_button.config(state =DISABLED)
            self.add_remove_button.config(state = NORMAL)
            
        def open_loop():
                
                loop_number = 1
                open_loop_data = pd.DataFrame(wavelength)
                open_loop_data.columns = ['Wavelength (nm)']
                number_loops = 3
                plt.clf()
                for x in range(0,number_loops):
                    data = acquire_avg()
                    open_loop_data['open_loop %d' %loop_number] = data
                    plt.plot(wavelength,data)
                    loop_number += 1
                print(open_loop_data)
                open_loop_window = Toplevel(root)
                open_loop_window .title('Select plot(s) to view')
                open_loop_window .geometry('400x400')
                scrollbar = Scrollbar(open_loop_window)
                scrollbar.pack(side = RIGHT, fill = Y )
                #create function to save the selected plot names and plot them
                def save_selected():
                    global scan_number
                    global df
                    data_headers = [lb.get(idx) for idx in lb.curselection()]
                    for x in range(0,len(data_headers),1):
                        print(open_loop_data[data_headers[x]])
    
                        #df[['Scan_ID %d' %scan_number]] = open_loop_data[data_headers[0]]
                        scan_number += 1
                    #check if the data headers is empty to set to none for future plotting 
                    open_loop_window.destroy()
                def select_all():
                    lb.select_set(0, END)
                def unselect_all():
                    lb.select_clear(0, END)
            
                headers = StringVar()
                lb = Listbox(open_loop_window, listvariable=headers, selectmode = MULTIPLE, yscrollcommand = scrollbar.set)
                lb.configure(width = 30, height = 10, font=("Times New Roman", 16))
                
                data_headers_dummy = list(open_loop_data.columns.values)
                for col in range(1, len(data_headers_dummy),1):
                    lb.insert('end', data_headers_dummy[col])
                lb.pack()
                
                save_selected_button = Button(open_loop_window, text = 'Save Selected', width = 30, height = 2, command = save_selected)
                save_selected_button.pack()
                select_all_button = Button(open_loop_window, text = 'Select_all', width = 30, height = 2, command = select_all)
                select_all_button.pack()
                Unselect_all_button = Button(open_loop_window, text = 'Un-Select_all', width = 30, height = 2, command = unselect_all)
                Unselect_all_button.pack()
                
                
                
            
            
            
            
            
        def acquire_save():
            global scan_number
            plt.clf()
            #try:
            global data_headers
            global df
            data = acquire_avg()
            df_data_array = pd.DataFrame(data)
            df['Scan_ID %d' %scan_number] = df_data_array
            df.to_csv(save_file, mode = 'w', index = False)
            data = df[['Scan_ID %d' %scan_number]]
            #plt.plot(wavelength,data)
            plt.plot(wavelength,data) 
            fig.canvas.draw()    
                
            if data_headers is not None:
                data_sel = pd.read_csv(save_file, header = 0)
                plt.plot(wavelength,data_sel[data_headers])
                plt.legend(data_headers, loc = "upper right", prop={'size': 6})
                    
            fig.canvas.draw()
            scan_number = 1 + scan_number
            self.ratio_view_button.config(state = NORMAL)
        def acquire():
            data = acquire_avg()
            # save current spectra then draw on canvas 
            np.savetxt(file_acquire, data, fmt="%d", delimiter=",")
            data = pd.read_csv(file_acquire, header = None)
            plt.plot(wavelength,data)
            plt.ylabel('a.u.')
            plt.xlabel('Wavelength (nm)')
            fig.canvas.draw()                  
            
        def plot_selected():
            global data_headers
            # Clear unsaved spectra 
            plt.clf()
            # plot Selected files from add_remove plots
            data = pd.read_csv(save_file, header = 0)
            plt.plot(wavelength,data[data_headers])
            plt.legend(data_headers, loc = "upper right", prop={'size': 6})
            fig.canvas.draw()
            
        #Clear canvas
        def clear():
            plt.clf()
            fig.canvas.draw()
            
        def ratio_view():
            global data_headers
            plt.clf()
            data = pd.read_csv(save_file, header = 0)
            ref = data[['Reference %d' %(reference_number-1)]].to_numpy()
            data_ratio = df[['Scan_ID %d' %(scan_number-1)]].to_numpy()
            ratio = np.true_divide(ref,data_ratio)*100
            plt.plot(wavelength,ratio)
            plt.ylabel('Ratio (%)')
            plt.xlabel('Pixel value')
            plt.ylim((0,105))
            fig.canvas.draw()
                
        def reference():
            global reference_number
            data = acquire_avg()
            df_data_array = pd.DataFrame(data)
            df['Reference %d' %reference_number] = df_data_array
            df.to_csv(save_file, mode = 'w', index = False)
            data = df[['Reference %d' %reference_number]]
            plt.clf()
            plt.plot(wavelength,data)
            fig.canvas.draw()
            self.acquire_save_button.config(state = NORMAL)
            self.add_remove_button.config(state = NORMAL)
            reference_number = 1 + reference_number
            
        def smoothing(): 
            global data_headers
            if data_headers is not None:
                plt.clf()
                settings = settings_read()
                smoothing_half_width = int(settings[8][1])
                df = pd.read_csv(save_file, header = 0)
                smoothed_data = df[data_headers]
                kernel = Box1DKernel(smoothing_half_width)
                for col in range(0,len(data_headers),1):
                    test = np.ravel(smoothed_data[data_headers[col]])
                    test = np.append(test[0:smoothing_half_width],test)
                    test = np.append(test,test[-1-smoothing_half_width:-1])
                    smoothed = np.convolve(kernel, test, mode = 'valid')
                    plt.plot(wavelength,smoothed)
                plt.legend(data_headers, loc = "upper right", prop={'size': 6}) 
                fig.canvas.draw()
            else:
                pass
              
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
        average_scans = int(settings[11][1])
        smoothing_used = int(settings[12][1])
        A = float(settings[13][1])
        B1 = float(settings[14][1])
        B2 = float(settings[15][1])/1000
        B3 = float(settings[16][1])/1000000
        B4 = float(settings[17][1])/1000000000
        B5 = float(settings[18][1])/1000000000000
        #wavelength = A + B1*pixel + B2*pixel**2 + B3*pixel**3 + B4*pixel**4+ B5*pixel**5
        
        #create all the buttons onto to the main window
        # with all their corresponding functions (command)
        self.quit_button = Button(root, text = "Quit", fg = 'Red', command = self.quit_button, width = 10, height = 3)
        self.quit_button.place(x = right_corner, y = 2)
        
        self.help_button = Button(root, text = "Help", fg = 'black', command = self.help_window, width = 10, height = 3)
        self.help_button.place(x = right_corner- 110, y = 2)
        
        self.settings_button = Button(root, text = "Settings", fg = 'black', command = self.settings_window, width = 10, height = 3)
        self.settings_button.place(x = right_corner - 220, y = 2)
        
        self.save_spectra_button = Button(root, text = "Save as Spectra", wraplength = 80, fg = 'black', command = lambda: self.key_pad(2), width = 10, height = 3, state = DISABLED)
        self.save_spectra_button.place(x = right_corner - 345, y = 2)
        
        self.save_reference_button = Button(root, text = "Save as Reference", wraplength = 80, fg = 'black', command = reference, width = 10, height = 3, state = DISABLED)
        self.save_reference_button.place(x = right_corner - 455, y = 2)
        
        self.open_new_button = Button(root, text = "Open/New Experiment", wraplength = 80, fg = 'black', command = lambda: self.key_pad(1), width = 10, height = 3)
        self.open_new_button.place(x = right_corner- 580, y = 2)
        
        self.open_loop_button = Button(root, text = "Open Loop", fg = 'black', command = OpenFile, width = 10, height = 3)
        self.open_loop_button.place(x = right_corner - right_corner, y = 2)
        
        self.acquire_button = Button(root, text = "Acquire", wraplength = 80, fg = 'black', command = acquire, width = 10, height = 3)
        self.acquire_button.place(x = left_corner, y = 105)
        
        self.acquire_save_button = Button(root, text = "Acquire and Save", fg = 'black', wraplength = 80, command = acquire_save, width = 10, height = 3, state = DISABLED)
        self.acquire_save_button.place(x = left_corner, y = 170)
        
        self.autorange_button = Button(root, text = "Auto-Range", fg = 'black', wraplength = 80, command = smoothing, width = 10, height = 3)
        self.autorange_button.place(x = left_corner, y = 235)
        
        self.sequence_button = Button(root, text = "Sequence", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 3)
        self.sequence_button.place(x = left_corner, y = 340)
        
        self.sequence_button = Button(root, text = "Sequence and Save", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 3)
        self.sequence_button.place(x = left_corner, y = 405)
        
        self.smoothing_button = Button(root, text = "Smoothing", fg = 'black', wraplength = 80, command = smoothing, width = 10, height = 2)
        self.smoothing_button.place(x = left_corner + 110, y = 430)
        
        self.ratio_view_button = Button(root, text = "Ratio View", fg = 'black', wraplength = 80, command = ratio_view, width = 10, height = 2, state = DISABLED)
        self.ratio_view_button.place(x = left_corner + 220, y = 430)
        
        self.zoom_button = Button(root, text = "Zoom", fg = 'black', wraplength = 80, command = open_loop, width = 10, height = 2)
        self.zoom_button.place(x = left_corner + 345, y = 430)
        
        self.plot_selected_button = Button(root, text = "Plot Selected", fg = 'black', wraplength = 80, command = plot_selected, state = DISABLED, width = 10, height = 2)
        self.plot_selected_button.place(x = left_corner + 455, y = 430)
        
        self.clear_button = Button(root, text = "Clear", fg = 'black', wraplength = 80, command = clear, width = 10, height = 2)
        self.clear_button.place(x = left_corner + 565, y = 430)
        
        self.add_remove_button = Button(root, text = "Add/Remove Plots", fg = 'black', wraplength = 85, state = DISABLED, command = self.add_remove_plots, width = 10, height = 2)
        self.add_remove_button.place(x = left_corner + 690, y = 430)
        
        ## Graphing Frame and fake plot
        self.graph_frame = Frame(root, width = 675, height =355, background = "white")
        self.graph_frame.place(x = 115, y = 70)
    
        #fig = Figure(figsize=(6.75, 3.2), dpi=100)
        global fig 
        fig = plt.figure(figsize = (6.75, 3.2), dpi = 100)
        pixel = range(0, 300, 1)
        
        
        try:
            df_acquire = pd.read_csv(file_acquire, header = None)
        except:
            x = 1
            
        
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)  # A tk.DrawingArea.
        
        canvas.get_tk_widget().pack()
        fig.canvas.draw()
        try:
            df_acquire = pd.read_csv(file_acquire, header = None)
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
        average_scans = int(settings[11][1])
        smoothing_used = int(settings[12][1])
        a_0 = str(settings[13][1])
        b_1 = str(settings[14][1])
        b_2 = str(settings[15][1])
        b_3 = str(settings[16][1])
        b_4 = str(settings[17][1])
        b_5 = str(settings[18][1])
        
        
        # Start to create Frames for settings window
        # Single Acquisition Frame
        single_acquisition_frame = Frame(self.setting_window, width = 350, height =120, background = "white")
        single_acquisition_frame.place(x = 460, y = 5)
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
        pulse_rate_entry = Entry(single_acquisition_frame, textvariable = self.pulse_rate, width = 8).grid(row = 2, column = 1, padx = 8, pady = 3)
  
        self.integ_time = IntVar()
        self.integ_time.set(integ_time)
        integ_time_button = Button(single_acquisition_frame, text = "Integration Time (usec):", fg = "Black", bg = "white",\
                                   command = lambda: self.Num_Pad(3))
        integ_time_button.grid(row = 3, column = 0, pady = 2, padx = 3)
        integ_time_entry = Entry(single_acquisition_frame, textvariable = self.integ_time, width = 8).grid(row = 3, column = 1, padx = 8)
        
        self.dark_subtract = IntVar()
        self.dark_subtract.set(dark_subtract)
        dark_subtraction_entry = Checkbutton(single_acquisition_frame, text = "Use Dark Subtraction ", variable = self.dark_subtract).grid(row = 5, column =0, pady = 2)
        
        self.smoothing_used = IntVar()
        self.smoothing_used.set(smoothing_used)
        smoothing_entry = Checkbutton(single_acquisition_frame, text = "Smoothing  ", variable = self.smoothing_used)
        smoothing_entry.grid(row = 5, column =1, pady = 2, padx = 8)
        
        self.average_scans = IntVar()
        self.average_scans.set(average_scans)
        average_scans_button = Button(single_acquisition_frame, text = "# of Averages:", fg = "Black", bg = "white",\
                                   command = lambda: self.Num_Pad(11))
        average_scans_button.grid(row = 4, column = 0, pady = 2, padx = 3)
        average_scans_entry = Entry(single_acquisition_frame, textvariable = self.average_scans, width = 8).grid(row = 4, column = 1, padx = 8)
  
        
        # Lamp Frame
        lamp = Frame(self.setting_window, width = 340, height = 75, background = "white")
        lamp.place(x = 460, y = 195)
        lamp_label = Label(lamp, text = "Lamp", fg = "Black", bg = "White").grid(row = 0, column = 0, columnspan = 2)
        self.lamp_voltage = IntVar()
        self.lamp_voltage.set(lamp_voltage)
        lamp_entry_button= Button(lamp, text = "Lamp Voltage (volts):", fg = "Black", bg = "white", command = lambda: self.Num_Pad(5))
        lamp_entry_button.grid(row = 1, column = 0, pady = 2, padx = 3)
        lamp_entry = Entry(lamp, textvariable = self.lamp_voltage, width = 8).grid(row = 1, column = 1, padx = 8, pady = 4)
        
        #AutoRange Frame 
        Auto_range_frame = Frame(self.setting_window, width = 340, height = 100, background = "white")
        Auto_range_frame.place(x = 460, y = 255)
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
        max_pulses_entry = Entry(Auto_range_frame, textvariable = self.max_pulses, width = 8).grid(row = 2, column = 1, padx = 8, pady = 4)
        
        # Graphing settings frame
        graph_frame = Frame(self.setting_window, width = 340, height = 200, background = "white")
        graph_frame.place(x = 460, y = 350)
        grpah_frame_label = Label(graph_frame, text = "Graphing Options:", fg = "Black", bg = "white").grid(row = 0, column = 0, columnspan = 2)
        self.smoothing = IntVar()
        self.smoothing.set(smoothing_half_width)
        smoothing_entry_button = Button(graph_frame, text = "Smoothing Half-Width (pixels):", fg = "Black", bg = "white", command = lambda: self.Num_Pad(8))
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
        
        wavelength_pixel_frame = Frame(self.setting_window, width = 340, height =120, background = "white")
        wavelength_pixel_frame.place(x = 200, y = 230)
        wavelength_pixel_label = Label(wavelength_pixel_frame, text = "Calibration Coefficients", fg = "Black", bg= "white", justify = CENTER).grid(row = 0, column = 0, columnspan = 3)
        self.a_0 = StringVar()
        self.a_0.set(a_0)
        a0_button = Button(wavelength_pixel_frame, text = "A_0: ", fg = "Black", bg = "white", command = lambda: self.Num_Pad(13))
        a0_button.grid(row = 1, column = 0, pady = 2, padx = 3)
        a0_entry = Entry(wavelength_pixel_frame, textvariable = self.a_0, width = 16).grid(row = 1, column = 1, padx = 8)
        
        self.b_1 = StringVar()
        self.b_1.set(b_1)
        b1_button = Button(wavelength_pixel_frame, text = "B_1: ", fg = "Black", bg = "white", command = lambda: self.Num_Pad(14))
        b1_button.grid(row = 2, column = 0, pady = 2, padx = 3)
        b1_entry = Entry(wavelength_pixel_frame, textvariable = self.b_1, width = 16).grid(row = 2, column = 1, padx = 8)
        
        self.b_2 = StringVar()
        self.b_2.set(b_2)
        b2_button = Button(wavelength_pixel_frame, text = "B_2: ", fg = "Black", bg = "white", command = lambda: self.Num_Pad(15))
        b2_button.grid(row = 3, column = 0, pady = 2, padx = 3)
        b2_entry = Entry(wavelength_pixel_frame, textvariable = self.b_2, width = 16).grid(row = 3, column = 1, padx = 8)
        b2_exp_label = Label(wavelength_pixel_frame, text = "e-03", fg = "Black", bg= "white", justify = CENTER).grid(row = 3, column = 2, columnspan = 2)
        
        self.b_3 = StringVar()
        self.b_3.set(b_3)
        b3_button = Button(wavelength_pixel_frame, text = "B_3: ", fg = "Black", bg = "white", command = lambda: self.Num_Pad(16))
        b3_button.grid(row = 4, column = 0, pady = 2, padx = 3)
        b3_entry = Entry(wavelength_pixel_frame, textvariable = self.b_3, width = 16).grid(row = 4, column = 1, padx = 8)
        b3_exp_label = Label(wavelength_pixel_frame, text = "e-06", fg = "Black", bg= "white", justify = CENTER).grid(row = 4, column = 2, columnspan = 2)
        
        self.b_4 = StringVar()
        self.b_4.set(b_4)
        b4_button = Button(wavelength_pixel_frame, text = "B_4: ", fg = "Black", bg = "white", command = lambda: self.Num_Pad(17))
        b4_button.grid(row = 5, column = 0, pady = 2, padx = 3)
        b4_entry = Entry(wavelength_pixel_frame, textvariable = self.b_4, width = 16).grid(row = 5, column = 1, padx = 8)
        b4_exp_label = Label(wavelength_pixel_frame, text = "e-09", fg = "Black", bg= "white", justify = CENTER).grid(row = 5, column = 2, columnspan = 2)
        
        self.b_5 = StringVar()
        self.b_5.set(b_5)
        b5_button = Button(wavelength_pixel_frame, text = "B_5: ", fg = "Black", bg = "white", command = lambda: self.Num_Pad(18))
        b5_button.grid(row = 6, column = 0, pady = 2, padx = 3)
        b5_entry = Entry(wavelength_pixel_frame, textvariable = self.b_5, width = 16).grid(row = 6, column = 1, padx = 8)
        b5_exp_label = Label(wavelength_pixel_frame, text = "e-12", fg = "Black", bg= "white", justify = CENTER).grid(row = 6, column = 2, columnspan = 2)
        
        
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
        self.average_scans.set('2')
        self.smoothing_used.set('1')
        self.a_0.set('311.1585037')
        self.b_1.set('2.70659433')
        self.b_2.set('-1.292296203')
        self.b_3.set('-6.644532253')
        self.b_4.set('5.749476565')
        self.b_5.set('9.954642163')
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
        settings[11][1] = int(self.average_scans.get())
        settings[12][1] = int(self.smoothing_used.get())
        settings[13][1] = float(self.a_0.get())
        settings[14][1] = float(self.b_1.get())
        settings[15][1] = float(self.b_2.get())
        settings[16][1] = float(self.b_3.get())
        settings[17][1] = float(self.b_4.get())
        settings[18][1] = float(self.b_5.get())
        # write settings array to csv 
        settings_open = open(settings_file, 'w')
        with settings_open:
           csv_writer = csv.writer(settings_open, delimiter = ',')
           csv_writer.writerows(settings)
        #print(settings)
        
    # setup number pad as toplevel window for settings window input 
    def Num_Pad(self, button_number):
        
        #number pad attributes
        num = StringVar()  # variable for extracting entry number
        self.numpad = Toplevel(self.setting_window)
        self.numpad.title('Input pad')
        
        self.numpad_frame = Frame(self.numpad, width = 230, height = 15).grid(row = 1, column = 0, columnspan = 3)
        number_entry = Entry(self.numpad, textvariable = num, justify = CENTER).grid(row = 1, column = 0, columnspan = 3)
        
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
            current = current = current[:-1] # Remove last digit
            num.set(current)
        
        def num_pad_save(button_number):
            try:
                self.setting_window.destroy()
                settings_open = open(settings_file, 'r')
                csv_reader = csv.reader(settings_open, delimiter=',')
                settings = list(csv_reader)
                # read in settings to particular button ID on settings page
                if button_number<13:
                    settings[button_number][1]  = int(num.get())
                else:
                    settings[button_number][1]  = float(num.get())
        
                #write settings to csv file
                settings_open = open(settings_file, 'w')
                with settings_open:
                    csv_writer = csv.writer(settings_open, delimiter = ',')
                    csv_writer.writerows(settings)
                self.numpad.destroy()
                self.settings_window()
            except:
                messagebox.showerror("Error", "Input must be a valid integer or float")
                self.settings_window()
                
        btn_list = [
        '7', '8', '9',
        '4', '5', '6',
        '1', '2', '3',
        '0', 'Del', 'OK']
    
        r = 2
        c = 0
        n = 0
    
        btn = list(range(len(btn_list)+2))
        
        for label in btn_list:
            btn[n] = Button(self.numpad, text = label, width = 6, height = 3)
            btn[n].grid(row = r, column = c)
            n+= 1
            c+= 1
            if c>2:
                c = 0
                r+= 1
        if button_number>12:
            btn[12] = Button(self.numpad, text = '.', width = 6, height = 3)
            btn[12].grid(row = 6, column = 0)
            btn[13] = Button(self.numpad, text = 'Backspace', width = 16, height = 3)
            btn[13].grid(row = 6, column = 1, columnspan = 2)
            btn[12].configure(command = lambda: button_click('.'))
            btn[13].configure(command = backspace)
            self.numpad.geometry('230x350')
        else:
            self.numpad.geometry('230x290')
            
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
        settings[13][1] = float(self.a_0.get())
        settings[14][1] = float(self.b_1.get())
        settings[15][1] = float(self.b_2.get())
        settings[16][1] = float(self.b_3.get())
        settings[17][1] = float(self.b_4.get())
        settings[18][1] = float(self.b_5.get())
        
                               
                               
        settings_open = open(settings_file, 'w')
        with settings_open:
           csv_writer = csv.writer(settings_open, delimiter = ',')
           csv_writer.writerows(settings)
        self.setting_window.destroy()
        
    def key_pad(self,number):
        self.keypad = Toplevel(root)
        path = '/home/pi/Desktop/Spectrometer/'
        key = StringVar()
        
        self.keypad.title('Input New FileName into entry box')
        #if full_screen == True:
        #self.key_pad.attributes('-fullscreen', True) # fullscreen on touchscreen
        
        self.keypad.geometry('600x300')
            
        keypad_frame = Frame(self.keypad)
        keypad_frame.grid(row = 1, column = 0, columnspan = 10)
        key_entry = Entry(keypad_frame, textvariable =key, justify = CENTER)
        key_entry.grid(row = 1, column = 0, columnspan = 10)
        
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
                try:
                    global filename
                    global reference_file
                    global save_file
                    global folder
                    global df
                    
                    folder = str(path + key.get())
                    if not os.path.exists(folder):
                        os.makedirs(folder)
                    save_file = str(folder+ '/' + key.get() +'_save.csv')
                    open(save_file, 'x')
                    
                    df = pd.DataFrame(wavelength)
                    df.columns = ['Wavelength (nm)']
                    save_csv = df.to_csv(save_file, mode = 'a', index=False)
                    self.keypad.destroy()
                    self.acquire_save_button.config(state = DISABLED)
                    self.save_reference_button.config(state = NORMAL)
                    self.save_spectra_button.config(state = NORMAL)
                except:
                    self.keypad.destroy()
                    messagebox.showerror("Error", "File Name already Exists! Please enter New Filename")
            else:
                newfilename = folder + '/' + key.get() + '.csv'
                open(newfilename, 'x')
                settings_open = open(settings_file, 'r')
                csv_reader = csv.reader(settings_open, delimiter=',')
                settings = list(csv_reader)
                integ_time = int(settings[3][1])
                integ = b"set_integ %0.6f\n" % integ_time
                ser.write(integ)
                sleep(1)
                ser.write(b"read\n")
                try:
                    #save to pseudo files
                    data = ser.readline()
                    data_array = np.array([int(d) for d in data.split(b",")])
                    pixel = np.arange(288).reshape(288,1)
                    data_saved = np.column_stack([wavelength, data_array])                
                    #create header string to add to final saved csv_file
                    name = "wavelength, Saved Spectra"
                    np.savetxt(newfilename, data_saved, fmt="%d", delimiter=",", header = name)
                
                    pixel = range(0,288,1)
                    plt.plot(pixel, data_array, '-.')
                    fig.canvas.draw()
                    self.keypad.destroy()
                except:
                    self.keypad.destroy()
                    messagebox.showerror("Error", "File Name already Exists! Please enter New Filename")
            
        btn_list = [
        '1', '2', '3', '4', '5', '6','7', '8', '9', '0',
        'Q', 'W', 'E','R', 'T', 'Y', 'U', 'I', 'O','P',
        'A', 'S', 'D','F', 'G', 'H', 'J', 'K', 'L','bkspce',
        'Z', 'X', 'C','V', 'B', 'N', 'M', '_', 'BACK','OK']
    
        r = 2
        c = 0
        n = 0
    
        btn = list(range(len(btn_list)))
        
        for label in btn_list:
            btn[n] = Button(self.keypad, text = label, width = 4, height = 3)
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
        btn[38].configure(command = back)
        btn[39].configure(command = lambda: key_pad_save(number))
        
    def add_remove_plots(self):
        self.add_remove = Toplevel(root)
        self.add_remove.title('Select plot(s) to view')
        self.add_remove.geometry('400x400')
        scrollbar = Scrollbar(self.add_remove)
        scrollbar.pack(side = RIGHT, fill = Y )
        
        #create function to save the selected plot names and plot them
        def save_selected():
            global data_headers
            global data_headers_idx
            data_headers = [lb.get(idx) for idx in lb.curselection()]
            #check if the data headers is empty to set to none for future plotting 
            if data_headers == []:
                data_headers = None
                self.plot_selected_button.config(state =DISABLED)
            else:
                data_headers_idx = lb.curselection()
                self.plot_selected_button.config(state =NORMAL)
            self.add_remove.destroy()
        def select_all():
            lb.select_set(0, END)
        def unselect_all():
            lb.select_clear(0, END)
            
            
        data = StringVar()
        lb = Listbox(self.add_remove, listvariable=data, selectmode = MULTIPLE, yscrollcommand = scrollbar.set)
        lb.configure(width = 30, height = 10, font=("Times New Roman", 16))
        data_pd = pd.read_csv(save_file)
        global data_headers
        global data_headers_idx
        data_headers_dummy = list(data_pd.columns.values)
        for col in range(1, len(data_headers_dummy),1):
            lb.insert('end', data_headers_dummy[col])
        
        lb.pack()
        #select previously selected 
        if data_headers_idx is not None:
            for i in data_headers_idx:
                lb.selection_set(i)
                
        save_selected_button = Button(self.add_remove, text = 'Save Selected', width = 30, height = 2, command = save_selected)
        save_selected_button.pack()
        select_all_button = Button(self.add_remove, text = 'Select_all', width = 30, height = 2, command = select_all)
        select_all_button.pack()
        Unselect_all_button = Button(self.add_remove, text = 'Un-Select_all', width = 30, height = 2, command = unselect_all)
        Unselect_all_button.pack()
        
        
        
        
        
        
        
    def help_window(self):
        print(acquisition_number)
        
    def on_off_led(self):
        ser.write(b"ON\n")
        sleep(2)
        ser.write(b"OFF\n")
        sleep(2)
        
        
        
        
    def quit_button(self):
        ser.reset_output_buffer()
        ser.reset_input_buffer()
        ser.close()
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