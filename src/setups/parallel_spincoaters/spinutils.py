# -*- coding: utf-8 -*-
"""
Created on Fri Oct 22 13:03:37 2021

@author: chengjw
"""


import serial
import serial.tools.list_ports
import time

class Macros:
    def __init__(self):  
        super().__init__()

    def list_serial(self):
        """
        List the serial connections available.

        Returns: set of port addresses
        """
        global com_ports
        
        com_ports = []
        
        ports = serial.tools.list_ports.comports()
        
        for port, desc, hwid in sorted(ports):
            com_ports.append(str(port))
            print("{}: {} [{}]".format(port, desc, hwid))
            
        return(com_ports)
            
    def open_serial(self, address, baud):
        """
        Makes connection to hardware.
        - address: address to serial port
        - baud:

        Returns: connections to serial port
        """
        print("Opening serial connection to {}".format(address))
        
        try:
            connection = serial.Serial(address, baud, timeout = 1) 
            time.sleep(2)   # Wait for grbl to initialize
            connection.flushInput()
            print("Connection opened to {}".format(address))
            return (connection)
        
        except:
            print("Could not connect to {}".format(address))
            return None

class Actuate:
    def __init__(self, mute_debug=False):  
        self.mute_debug = mute_debug
        
    def run_speed(self, mcu, speed):
        """
        Relay instructions to spincoater.
        - mcu: serial connection to spincoater
        - speed: spin speed
        """
        try:
            mcu.write(bytes("{}\n".format(speed), 'utf-8'))
        except AttributeError:
            pass
        print("Spin speed: {}".format(speed))
        
    def run_spin_step(self, mcu, speed, run_time):
        """
        Perform timed spin step
        - mcu: serial connection to spincoater
        - speed: spin speed
        - run_time: spin time
        """
        starttime = time.time()
        
        interval = 1
        self.run_speed(mcu, speed)
        
        while(True):
            time.sleep(0.1)
            if (interval <= time.time() - starttime):
                self.printer(run_time - interval)
                interval += 1
            if (run_time <= time.time() - starttime):
                self.printer(time.time() - starttime)
                self.run_speed(mcu, 0)
                break
    
    def run_pump(self, mcu, speed):
        """
        Relay instructions to pump.
        - mcu: serial connection to pump
        - speed: speed of pump of rotation
        """
        try:
            mcu.write(bytes("{}\n".format(speed), 'utf-8'))
        except AttributeError:
            pass
        
    def run_solenoid(self, mcu, state):
        """
        Relay instructions to valve.
        - mcu: serial connection to pump
        - state: valve channel
            - -1 to -8   : open specific valve
            - 1 to 8     : close specific valve
            - 9          : close all valves
        """
        try:
            mcu.write(bytes("{}\n".format(state), 'utf-8'))
        except AttributeError:
            pass
    
    def dispense(self, mcu, pump_speed, prime_time, drop_time, channel):
        """
        Dispense (aspirate) liquid from (into) syringe.
        - mcu: serial connection to pump
        - pump_speed: speed of pump of rotation
            - <0    : aspirate
            - >0    : dispense
        - prime_time: time to prime the peristaltic pump
        - drop_time: time to achieve desired volume
        - channel: valve channel
        """
        
        run_time = prime_time + drop_time
        interval = 0.1
        
        starttime = time.time()
        self.run_solenoid(mcu, -channel)
        self.run_pump(mcu, pump_speed)
        
        while(True):
            time.sleep(0.001)
            if (interval <= time.time() - starttime):
                self.printer(run_time - interval)
                interval += 0.1
            if (run_time <= time.time() - starttime):
                self.printer(time.time() - starttime)
                break
        
        starttime = time.time()
        interval = 0.1
        self.run_solenoid(mcu, -channel)
        self.run_pump(mcu, -abs(pump_speed))

        while(True):
            time.sleep(0.001)
            if (interval <= time.time() - starttime):
                self.printer(prime_time - interval)
                interval += 0.1
            if (prime_time <= time.time() - starttime):
                self.printer(time.time() - starttime)
                self.run_pump(mcu, 10)
                self.run_solenoid(mcu, channel)
                break
    
    def home_dispense(self, mcu):
        """
        Move cnc arm back home.
        - mcu: serial connection to cnc arm

        Returns: home position
        """
        try:
            mcu.write(bytes("$H\n", 'utf-8'))
            self.printer(mcu.readline())
        except AttributeError:
            pass   
        return(0)
    
    def move_dispense_rel(self, mcu, current_x, distance):
        """
        Move cnc arm by desired distance.
        - mcu: serial connection to cnc arm
        - current_x: current position
        - distance: distance to move by (in mm)

        Returns: new position
        """
        try:            
            mcu.write(bytes("G91\n", 'utf-8'))
            self.printer(mcu.readline())
            mcu.write(bytes("G0 X{}\n".format(distance), 'utf-8'))
            self.printer(mcu.readline())
            mcu.write(bytes("G90\n", 'utf-8'))
            self.printer(mcu.readline())
        except AttributeError:
            pass
        
        current_x = current_x + distance
        current_x = round(current_x, 2)
        print(current_x)
        
        return(current_x)
            
    def move_dispense_abs(self, mcu, current_x, position):
        """
        Move cnc arm back home.
        - mcu: serial connection to cnc arm
        - current_x: current position
        - position: position to move to

        Returns: new position
        """
        try:
            mcu.write(bytes("G90\n", 'utf-8'))
            self.printer(mcu.readline())
            mcu.write(bytes("G0 X{}\n".format(position), 'utf-8'))
            self.printer(mcu.readline())
            mcu.write(bytes("G90\n", 'utf-8'))
            self.printer(mcu.readline())
        except AttributeError:
            pass
        
        current_x = position
        current_x = round(current_x, 2)
        print(current_x)
        
        return(current_x)

    def printer(self, value):
        if self.mute_debug:
            return
        print(value)
        return