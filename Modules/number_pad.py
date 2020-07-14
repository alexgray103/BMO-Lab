from settings import Settings as _Settings
import csv
from tkinter import *

########## Global Variables ##################
settings_file = '/home/pi/Desktop/Spectrometer/settings/settings.csv'



class Num_Pad:
    def __init__(self, parent, button_number):
        global settings_file
        self.settings_file = settings_file
        self.numpad = parent
        #number pad attributes
        num = StringVar()  # variable for extracting entry number
        
        self.numpad.title('Input pad')
        numpad_size = '330x450'
        self.numpad.geometry(numpad_size)

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
                self.numpad.destroy()
                settings_open = open(self.settings_file, 'r')
                csv_reader = csv.reader(settings_open, delimiter=',')
                settings = list(csv_reader)
                
                # read in settings to particular button ID on settings page
                # arbitrary number depending on location in CSV file
                if button_number<15 or button_number>21:
                    if button_number == 1 and int(num.get()) == 0:
                        settings[3][1] = 100
                    elif button_number == 1 and int(num.get()) != 0:
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
                
                

            # if value or type of returned value isnt an int or float then raise error
            except ValueError or TypeError:
                messagebox.showerror("Error", "Input must be a valid integer or float")
                self.numpad.destroy()

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
        else:
            pass
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

        
