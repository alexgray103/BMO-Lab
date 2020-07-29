import serial
from time import sleep
from ESS_GUI_module_0 import *
import matplotlib.pyplot as plt


# open up a serial to allow for reading in of module attachment
port = "/dev/ttyUSB0"
port2 = "/dev/ttyUSB1"
try:
    ser = serial.Serial(port, baudrate = 115200, timeout = 3)
except:
    ser = serial.Serial(port2, baudrate = 115200, timeout =3)

sleep(2.5) # wait for a little to initialize serial connection

ser.write(b'module\n')
module = int(ser.readline().decode()) # read in the module number
print(module)

if module == 0:
    root = Tk()
    app = Module_0(root)
    root.mainloop()
    
elif module == 1:
    root = Tk()
    app = Module_0(root)
    root.mainloop()

