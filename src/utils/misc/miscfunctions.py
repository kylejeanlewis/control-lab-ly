# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/03/18 09:00:00

@author: Chang Jie
"""
import serial.tools.list_ports

print(f"Import: OK <{__name__}>")

def display_ports():
    """
    Displays available ports.
    """
    com_ports = []
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in sorted(ports):
        com_ports.append(str(port))
        print(f"{port}: {desc} [{hwid}]")
    if len(ports) == 0:
        print("No ports detected!")
        return ['']
    return com_ports


class Debugger(object):
    """
    Debugger class to turn on and off debug output.
    """
    def __init__(self, show_logs=True):
        self.output = show_logs
    
    def show_print(self, value):
        """Show debug output"""
        if self.output:
            print(value)
            return
        return value
