# -*- coding: utf-8 -*-
"""
Created on Tue Oct 19 17:05:17 2021

@author: chengjw
"""
        
import spinutils

macros = spinutils.macros()
actuate = spinutils.actuate()

#%%

com_ports = macros.list_serial()

spin = macros.open_serial("COM12", 9600)
pump = macros.open_serial("COM14", 9600)
cnc = macros.open_serial("COM10", 115200)

current_x = actuate.home_dispense(cnc)

#%%

#Spincoater controls
actuate.run_speed(spin, 0)
actuate.run_spin_step(spin, 2000, 10)

#Pump and solenoid valve controls
actuate.run_pump(pump, 10)
actuate.run_pump(pump, 200)
actuate.run_pump(pump, 2000)
actuate.run_solenoid(pump,-3)
actuate.run_solenoid(pump, 9)


#Dispense head movement controls
current_x = actuate.home_dispense(cnc)
current_x = actuate.move_dispense_rel(cnc, current_x, -50)
current_x = actuate.move_dispense_abs(cnc, current_x, 0)

#%% Dispense and spin

current_x = actuate.home_dispense(cnc)

#Spincoater position
position = -50
spin_speed = 2000
spin_time = 20

current_x = actuate.move_dispense_abs(cnc, current_x, -50)

actuate.dispense(pump, 300, 1, 1.4, 7)
    
current_x = actuate.home_dispense(cnc)
actuate.run_spin_step(spin, spin_speed, spin_time)
