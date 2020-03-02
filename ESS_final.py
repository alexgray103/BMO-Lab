from tkinter import *

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
import matplotlib.pyplot as plt

from time import sleep
import time
import RPi.GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

import csv

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

 
# Intitial variables
full_screen = False


# Settings full screen popup window to change all input variables 

    
# Create main window with all neccassary buttons and plot
class Main_GUI:
    def __init__(self, master):
        self.master = root
        root.title("ESS System Interface")
        if full_screen == True:
            root.attributes('-fullscreen', True) # fullscreen on touchscreen
        else:
            root.geometry('800x480') # PC window size 
        root.configure(bg= "sky blue")
        right_corner = 690
        left_corner = 0
        
        ### read in default settings
        settings_open = open('/home/pi/Desktop/BMO Lab/settings.csv', 'r')
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
        
        
        self.quit_button = Button(root, text = "Quit", fg = 'Red', command = root.destroy, width = 10, height = 3)
        self.quit_button.place(x = right_corner, y = 2)
        
        self.help_button = Button(root, text = "Help", fg = 'black', command = self.help_window, width = 10, height = 3)
        self.help_button.place(x = right_corner- 110, y = 2)
        
        self.settings_button = Button(root, text = "Settings", fg = 'black', command = self.settings_window, width = 10, height = 3)
        self.settings_button.place(x = right_corner - 220, y = 2)
        
        self.save_spectra_button = Button(root, text = "Save as Spectra", wraplength = 80, fg = 'black', command = self.save_spectra, width = 10, height = 3)
        self.save_spectra_button.place(x = right_corner - 345, y = 2)
        
        self.save_reference_button = Button(root, text = "Save as Reference", wraplength = 80, fg = 'black', command = self.save_reference, width = 10, height = 3)
        self.save_reference_button.place(x = right_corner - 455, y = 2)
        
        self.open_new_button = Button(root, text = "Open/New Experiment", wraplength = 80, fg = 'black', command = self.open_new, width = 10, height = 3)
        self.open_new_button.place(x = right_corner- 580, y = 2)
        
        self.open_loop_button = Button(root, text = "Open Loop", fg = 'black', command = self.open_loop, width = 10, height = 3)
        self.open_loop_button.place(x = right_corner - right_corner, y = 2)
        
        self.acquire_button = Button(root, text = "Acquire", wraplength = 80, fg = 'black', command = self.acquire, width = 10, height = 3)
        self.acquire_button.place(x = left_corner, y = 105)
        
        self.acquire_save_button = Button(root, text = "Acquire and Save", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 3)
        self.acquire_save_button.place(x = left_corner, y = 170)
        
        self.autorange_button = Button(root, text = "Auto-Range", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 3)
        self.autorange_button.place(x = left_corner, y = 235)
        
        self.sequence_button = Button(root, text = "Sequence", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 3)
        self.sequence_button.place(x = left_corner, y = 340)
        
        self.sequence_button = Button(root, text = "Sequence and Save", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 3)
        self.sequence_button.place(x = left_corner, y = 405)
        
        self.smoothing_button = Button(root, text = "Smoothing", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 2)
        self.smoothing_button.place(x = left_corner + 110, y = 430)
        
        self.ratio_view_button = Button(root, text = "Ratio View", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 2)
        self.ratio_view_button.place(x = left_corner + 220, y = 430)
        
        self.zoom_button = Button(root, text = "Zoom", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 2)
        self.zoom_button.place(x = left_corner + 345, y = 430)
        
        self.auto_scale_button = Button(root, text = "Auto-Scale", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 2)
        self.auto_scale_button.place(x = left_corner + 455, y = 430)
        
        self.reset_button = Button(root, text = "Reset", fg = 'black', wraplength = 80, command = self.acquire, width = 10, height = 2)
        self.reset_button.place(x = left_corner + 565, y = 430)
        
        self.add_remove_button = Button(root, text = "Add/Remove Plots", fg = 'black', wraplength = 85, command = self.acquire, width = 10, height = 2)
        self.add_remove_button.place(x = left_corner + 690, y = 430)
        
        ## Graphing Frame and fake plot
        self.graph_frame = Frame(root, width = 675, height =355, background = "white")
        self.graph_frame.place(x = 115, y = 70)
    
        fig = Figure(figsize=(6.75, 3.2), dpi=100)
        wavelength = np.arange(300, 900, .01)
        fig.add_subplot(111).plot(wavelength,2 * np.sin(2* np.pi / wavelength))

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)  # A tk.DrawingArea.
        canvas.draw()
        canvas.get_tk_widget().pack()

        toolbar = NavigationToolbar2Tk(canvas, self.graph_frame)
        toolbar.update()
        canvas.get_tk_widget().pack()
              
             
              
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
        settings_open = open('/home/pi/Desktop/BMO Lab/settings.csv', 'r')
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
        self.integ_time.set('60')
        self.dark_subtract.set('1')
        self.lamp_voltage.set('1000')
        self.threshold.set('52000')
        self.smoothing.set('2')
        self.min_wavelength.set('300')
        self.max_wavelength.set('900')
        settings_open = open('/home/pi/Desktop/BMO Lab/settings.csv', 'r')
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
        
        settings_open = open('/home/pi/Desktop/BMO Lab/settings.csv', 'w')
        with settings_open:
           csv_writer = csv.writer(settings_open, delimiter = ',')
           csv_writer.writerows(settings)
        print(settings)
        
        
    def Num_Pad(self, button_number):
        
        num = StringVar()
        self.numpad = Toplevel(self.setting_window)
        self.numpad.title('Input pad')
        self.numpad.geometry('230x300')
        self.numpad_frame = Frame(self.numpad, width = 230, height = 15).grid(row = 1, column = 0, columnspan = 3)
        number_entry = Entry(self.numpad, textvariable = num, justify = CENTER).grid(row = 1, column = 0, columnspan = 3)
        
        def button_click(number):
            current = num.get()
            num.set('')
            num.set(str(current) + str(number))
    
        def num_pad_delete():
            num.set('')
        
        def num_pad_save(button_number):
            self.setting_window.destroy()
            settings_open = open('/home/pi/Desktop/BMO Lab/settings.csv', 'r')
            csv_reader = csv.reader(settings_open, delimiter=',')
            settings = list(csv_reader)
            settings[button_number][1]  = int(num.get())
            
            settings_open = open('/home/pi/Desktop/BMO Lab/settings.csv', 'w')
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
        settings_open = open('/home/pi/Desktop/BMO Lab/settings.csv', 'r')
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
        
        settings_open = open('/home/pi/Desktop/BMO Lab/settings.csv', 'w')
        with settings_open:
           csv_writer = csv.writer(settings_open, delimiter = ',')
           csv_writer.writerows(settings)
        print(settings)
        self.setting_window.destroy()
       
    def help_window(self):
        print(acquisition_number)
    def save_spectra(self):
        print("saving spectra needed to be added later")
    def save_reference(self):
        print("saving reference needed to be added")
    def open_new(self):
        print("open new needs to be added")
    def open_loop(self):
        print("open loop needs to be added")
        
    def acquire(self):
        
        settings_open = open('/home/pi/Desktop/BMO Lab/settings.csv', 'r')
        csv_reader = csv.reader(settings_open, delimiter=',')
        settings = list(csv_reader)
        integ_micros = int(settings[3][1])/1000000
        
        delay_time_clock = 0.0000001
        GPIO.output(Spec_Clk, GPIO.HIGH)
        sleep(delay_time_clock)
        GPIO.output(Spec_Clk, GPIO.LOW)
        GPIO.output(Spec_ST, GPIO.HIGH)
        sleep(delay_time_clock)
        
        for x in range(0, 3, 1):
            GPIO.output(Spec_Clk, GPIO.HIGH)
            sleep(delay_time_clock)
            GPIO.output(Spec_Clk, GPIO.LOW)
            sleep(delay_time_clock)
        start = 0
        start = time.time()
        elapsed = 0
        while (elapsed <= integ_micros):
            elapsed = time.time() - start
            GPIO.output(Spec_Clk, GPIO.HIGH)
            sleep(delay_time_clock)
            GPIO.output(Spec_Clk, GPIO.LOW)
            sleep(delay_time_clock)
        
        GPIO.output(Spec_ST, GPIO.LOW)
    
        for x in range(0,88,1):
            GPIO.output(Spec_Clk, GPIO.HIGH)
            sleep(delay_time_clock)
            GPIO.output(Spec_Clk, GPIO.LOW)
            sleep(delay_time_clock)
    
    

        for x in range(0,Spec_channels,1):
            start1 = time.time()
            data[x] = mcp.read_adc(2)
            end1 = time.time()
            GPIO.output(Spec_Clk, GPIO.HIGH)
            sleep(delay_time_clock)
            GPIO.output(Spec_Clk, GPIO.LOW)
            sleep(delay_time_clock)
            
        pixel = range(0,288,1)
        plt.plot(pixel, data)
        plt.show()
        sleep(0.001)
    
        print('ADC read takes:', end1-start1, 'Seconds')
    
    
    def acquire_save(self):
        print("Acquire and save needs to be added")
    def auto_range(self):
        print("autorange needs to be added")
    def sequence(self):
        print("Sequence needs to be added")
        
 

# Actually create window with all the above functionality
root = Tk()
my_gui = Main_GUI(root)
root.mainloop()

    
