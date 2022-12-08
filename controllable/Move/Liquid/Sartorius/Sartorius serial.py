# -*- coding: utf-8 -*-
"""
Created on Fri Nov 18 10:40:56 2022

@author: chengjw
"""

from threading import Thread
from time import sleep
import serial

global running 
global message_from
global message_to

pipette = serial.Serial("COM23", 9600, timeout = 1) 

#%% Commands

message = '1RZ30º\r'.encode('utf-8').hex()
message = '1RI46º\r'.encode('utf-8').hex()
message = '1RBº\r'.encode('utf-8').hex()
message = '1REº\r'.encode('utf-8').hex()
message = '1DSº\r'.encode('utf-8').hex()

1RI50
1RB
1RE
1RZ30

1RI20 aspirate
1RO20 dispense
1RP20 move
1RB blowout
1RE eject tip

#%%

def readserial():
    global is_running
    while(1):
        pipette.write(bytearray.fromhex('1DSº\r'.encode('utf-8').hex()))
        response = pipette.readline()
        print(response)
        pipette.write(bytearray.fromhex('1DNº\r'.encode('utf-8').hex()))
        response = pipette.readline()
        print(response)

        # sleep(0.05)
        if is_running == False:
            print('Exiting')
            break

def writeserial(message_to):
    print('Writing {}'.format(message_to))
    pipette.write(bytearray.fromhex(message_to.encode('utf-8').hex()))
    
def shutdown():
    global is_running
    is_running = False
    t1.join()
    pipette.close()
    
t1 = Thread(target=readserial)

t1.start()
is_running = True


