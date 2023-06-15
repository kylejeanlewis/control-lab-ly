"""
Class object to query the pH and temperature readings from Sentron's SI 600 pH meter

Author: Aniket Chitre
Date: July 2022

Necessary package installations: pyserial == 3.5
"""

import serial   # https://pyserial.readthedocs.io/en/latest/pyserial.html
import time


class SI600_pH:

    baud_rate  = 9600   # Communication rates from SI-meter-manual_v3.pdf pp.36: 9600 8 N 1 to receive data from the USB port
    to         = 1      # timeout
    pause_time = 10      # delay between transmitting to the pH meter and reading data back; too soon and nothing to read

    def __init__(self, port):
        self.port = port    # Edit port according to listed port in 'Device Manager'

    def reading(self):
        self.ser = serial.Serial(port=self.port, baudrate=self.baud_rate, timeout=1)    # open serial object, ensure not open elsewhere
        self.ser.write('ACT'.encode('utf-8'))   # Manual pp.36 sending the string 'ACT' queries the pH meter
        time.sleep(self.pause_time)     # require a delay between writing to and reading from the pH meter
        reading = self.ser.read_until('\r\n')   # Reads data until the end of line
        pH = reading[26:33]     # see pp. 36 of manual (or print whole string) to see data format
        pH = "{:.3f}".format(float(pH))     # format sliced string to obtain pH
        temp = reading[34:38]
        temp = "{:.1f}".format(float(temp))     # format sliced string to obtain temperature
        self.ser.close()    # ensure the serial object is closed, it can be re-opened when this method is called.
        x = f"pH = {pH}, temp = {temp} deg C"
        print(x)
        return x
        