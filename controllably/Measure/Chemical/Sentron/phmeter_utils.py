# %% -*- coding: utf-8 -*-
"""
This module holds the class for pH meter probe from Sentron.

Classes:
    SentronProbe (Measurer)
"""
# Standard library imports
from __future__ import annotations
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
from ...measure_utils import Measurer
print(f"Import: OK <{__name__}>")

class SentronProbe(Measurer):
    def __init__(self, port:str, **kwargs):
        """
        Instantiate the class

        Args:
            port (str): COM port address
        """
        super().__init__(**kwargs)
        self._connect(port=port)
        return
    
    def clearCache(self):
        """Clear most recent data and configurations"""
        return super().clearCache()
    
    def disconnect(self):
        """Disconnect from device"""
        self.device.close()
        return
    
    def getReadings(self, wait:int = 10) -> tuple[float]:
        """
        Get pH and temperature readings from tool

        Args:
            wait (int, optional): duration to wait for the hardware to respond. Defaults to 10.

        Returns:
            tuple[float]: pH, temperature (°C)
        """
        self.device.write('ACT'.encode('utf-8'))    # Manual pp.36 sending the string 'ACT' queries the pH meter
        time.sleep(wait)                            # require a delay between writing to and reading from the pH meter 
        reading = self.device.read_until('\r\n')    # Reads data until the end of line; see pp. 36 of manual (or print whole string) to see data format
        pH = float(reading[26:33])
        temperature = float(reading[34:38])
        print(f"pH = {pH:.3f}, temperature = {temperature:.1f}°C")
        return pH, temperature
        
    # Protected method(s)
    def _connect(self, port:str, baudrate:int = 9600, timeout:int = 1):
        """
        Connection procedure for tool

        Args:
            port (str): COM port address
            baudrate (int, optional): baudrate. Defaults to 9600.
            timeout (int, optional): timeout in seconds. Defaults to 1.
        """
        self.connection_details = {
            'port': port,
            'baudrate': baudrate,
            'timeout': timeout
        }
        device = None
        try:
            device = serial.Serial(port, baudrate, timeout=timeout)
        except Exception as e:
            print(f"Could not connect to {port}")
            if self.verbose:
                print(e)
        else:
            print(f"Connection opened to {port}")
            self.setFlag(connected=True)
            time.sleep(1)
        self.device = device
        return
    