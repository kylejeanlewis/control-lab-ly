# -*- coding: utf-8 -*-
"""
This module contains the HeaterMixin class.

Attributes:
    TOLERANCE (float): tolerance for temperature
    
## Classes:
    `HeaterMixin`: Mixin class for heater control
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import logging
import threading
import time

TOLERANCE = 0.1

class HeaterMixin:
    """
    Mixin class for heater control
    
    ### Methods:
        `atTemperature`: Check if temperature is reached
        `getTemperature`: Get temperature
        `holdTemperature`: Hold temperature
        `setTemperature`: Set temperature
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass
    
    def atTemperature(self, temperature: float, *, tolerance: float|None = None, **kwargs) -> bool:
        """
        Check if at temperature
        
        Args:
            temperature (float): target temperature
            tolerance (float, optional): tolerance. Defaults to None.
            
        Returns:
            bool: at temperature
        """
        tolerance = tolerance or 0.1
        return (abs(self.getTemperature() - temperature) < tolerance)
        
    def getTemperature(self) -> float:
        """
        Get temperature
        
        Returns:
            float: temperature
        """
        temperature = None # Replace with implementation
        return temperature 
    
    def holdTemperature(self, 
        temperature: float, 
        duration: float, 
        blocking: bool = True, 
        *, 
        tolerance: float|None = None, 
        release: threading.Event|None = None
    ) -> threading.Event|None:
        """ 
        Hold temperature
        
        Args:
            temperature (float): target temperature
            duration (float): duration to hold temperature
            blocking (bool, optional): blocking call. Defaults to True.
            tolerance (float, optional): tolerance. Defaults to None.
            release (threading.Event, optional): release event. Defaults to None.
            
        Returns:
            threading.Event: release event
        """
        def inner(temperature: float, duration: float, tolerance: float|None, release: threading.Event|None = None):
            logger: logging.Logger = getattr(self, '_logger', logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}.{id(self)}"))
            self.setTemperature(temperature, tolerance=tolerance)
            logger.info(f"Holding temperature at {temperature}°C for {duration} seconds")
            time.sleep(duration)
            logger.info("End of temperature of hold")
            if isinstance(release, threading.Event):
                _ = release.clear() if release.is_set() else release.set()
            return
        
        if blocking:
            inner(temperature, duration, tolerance)
            return
        
        release = release if isinstance(release, threading.Event) else threading.Event()
        thread = threading.Thread(target=inner, args=(temperature, duration, tolerance, release))
        thread.start()
        return thread, release
    
    def setTemperature(self, 
        temperature: float, 
        blocking: bool = True, 
        *, 
        tolerance: float|None = None, 
        release: threading.Event|None = None
    ) -> tuple[threading.Thread, threading.Event]|None:
        """
        Set temperature
        
        Args:
            temperature (float): target temperature
            blocking (bool, optional): blocking call. Defaults to True.
            tolerance (float, optional): tolerance. Defaults to None.
            release (threading.Event, optional): release event. Defaults to None.
            
        Returns:
            tuple[threading.Thread, threading.Event]: thread and release event
        """
        def inner(temperature: float, tolerance: float|None, release: threading.Event|None = None):
            logger: logging.Logger = getattr(self, '_logger', logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}.{id(self)}"))
            self._set_temperature(temperature)
            logger.info(f"New set temperature at {temperature}°C")
            logger.info(f"Waiting for temperature ot reach {temperature}°C")
            while not self.atTemperature(temperature, tolerance=tolerance):
                time.sleep(0.1)
            logger.info(f"Temperature of {temperature}°C reached")
            if isinstance(release, threading.Event):
                _ = release.clear() if release.is_set() else release.set()
            return
        
        if blocking:
            inner(temperature, tolerance)
            return
        
        release = release if isinstance(release, threading.Event) else threading.Event()
        thread = threading.Thread(target=inner, args=(temperature, tolerance, release))
        thread.start()
        return thread, release
        
    def _set_temperature(self, temperature: float):
        """
        Set temperature
        
        Args:
            temperature (float): target temperature
        """
        ... # Replace with implementation
        return
