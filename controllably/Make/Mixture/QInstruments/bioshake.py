# -*- coding: utf-8 -*-
"""
This module provides a class to control the QInstruments BioShake device.

Attributes:
    MAX_LEN (int): maximum length of data buffer
    ACCELERATION_LIMIT (tuple): lower and upper limits for acceleration

## Classes:
    `BioShake`: BioShake provides methods to control the QInstruments BioShake device.

<i>Documentation last updated: 2025-02-22/i>
"""
# Standard library imports
from __future__ import annotations
from collections import deque
from datetime import datetime
import threading
import time
from types import SimpleNamespace
from typing import NamedTuple, Any

# Third party imports
import pandas as pd

# Local application imports
from ....core import datalogger
from ... import Maker
from ...Heat.heater_mixin import HeaterMixin
from .qinstruments_api import QInstrumentsDevice, FloatData

MAX_LEN = 100
ACCELERATION_LIMIT = (1,30)

class BioShake(HeaterMixin, Maker):
    """ 
    BioShake provides methods to control the QInstruments BioShake device.
    
    ### Constructor:
        `port` (str): serial port address
        `speed_tolerance` (float, optional): fractional tolerance to be considered on target for speed. Defaults to 10.
        `temp_tolerance` (float, optional): fractional tolerance to be considered on target for temperature. Defaults to 1.5.
        `stabilize_timeout` (float, optional): time in seconds to wait before considering temperature stabilized. Defaults to 10.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
        `simulation` (bool, optional): whether to simulate. Defaults to False.
        
    ### Attributes and properties:
        `buffer_df` (pd.DataFrame): buffer dataframe to store collected data
        `records_df` (pd.DataFrame): records dataframe to store collected data
        `limits` (dict[str, tuple]): hardware limits for device
        `ranges` (dict[str, tuple]): user-defined ranges for controls
        `model` (str): device model description
        `serial_number` (str): device serial number
        `acceleration` (float): acceleration / deceleration of the shaker in seconds
        `speed` (float): actual speed of shake in rpm
        `set_speed` (float): target speed
        `speed_tolerance` (float): fractional tolerance to be considered on target for speed
        `shake_time_left` (float): remaining time left on shaker
        `temperature` (float): actual temperature of the plate in °C
        `set_temperature` (float): target temperature
        `temp_tolerance` (float): fractional tolerance to be considered on target for temperature
        `stabilize_timeout` (float): time in seconds to wait before considering temperature stabilized
        `is_counterclockwise` (bool): returns the current mixing direction
        `is_locked` (bool): returns the current ELM state
        `connection_details` (dict): connection details for the device
        `device` (Device): device object that communicates with physical tool
        `flags` (SimpleNamespace[str, bool]): flags for the class
        `is_busy` (bool): whether the device is busy
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
        
    ### Methods:
        `clearCache`: clears and remove data in buffer
        `connect`: connect to the device
        `controlTemp`: switches on/off the temperature control feature and starts/stops heating/cooling
        `execute`: Set target temperature, then shake the plate at target speed and hold target temperature for desired duration
        `getAcceleration`: returns the acceleration/deceleration value
        `getDefaults`: retrieve the default and starting configuration of the device upon start up
        `getErrors`: returns a list with errors and warnings which can occur during processing
        `getShakeDirection`: returns the current mixing direction
        `getElmState`: returns the current ELM state
        `getErrors`: returns a list with errors and warnings which can occur during processing
        `getShakeTimeLeft`: returns the remaining shake time in seconds if device was started with the a defined duration
        `getSpeed`: returns the set speed and current mixing speed in rpm
        `getStatus`: retrieve the status of the device's ELM, shaker, and temperature control
        `getTemperature`: returns the set temperature and current temperature in °C
        `getUserLimits`: retrieve the user defined limits for speed and temperature
        `grip`: grip or release the object
        `holdTemperature`: hold target temperature for desired duration
        `home`: move shaker to the home position and locks in place
        `record`: start or stop data recording
        `reset`: restarts the controller
        `setAcceleration`: sets the acceleration/deceleration value in seconds
        `setCounterClockwise`: sets the mixing direction to counter clockwise
        `setSpeed`: set the target mixing speed
        `setTemperature`: sets target temperature between TempMin and TempMax in 1/10°C increments
        `shake`: shake the plate at target speed, for specified duration
        `shutdown`: shutdown procedure for tool
        `stop`: stop the shaker immediately at an undefined position, ignoring the defined deceleration time if in an emergency
        `toggleECO`: toggle the economical mode to save energy and decrease abrasion 
        `toggleRecord`: start or stop data recording
        `toggleShake`: starts/stops shaking with defined speed with defined acceleration/deceleration time
        `toggleTemperature`: switches on/off the temperature control feature and starts/st
    """
    
    _default_acceleration: int = 5
    _default_speed: int = 500
    _default_temperature: float = 25
    _default_flags = SimpleNamespace(busy=False,elm_locked=True, counterclockwise=True, verbose=False)
    def __init__(self, 
        port: str, 
        *, 
        speed_tolerance: float = 10,
        temp_tolerance: float = 1.5,
        stabilize_timeout: float = 10,
        verbose: bool = False, 
        simulation:bool = False, 
        **kwargs
    ):
        """
        Initialize the class

        Args:
            port (str): serial port address
            speed_tolerance (float, optional): fractional tolerance to be considered on target for speed. Defaults to 10.
            temp_tolerance (float, optional): fractional tolerance to be considered on target for temperature. Defaults to 1.5.
            stabilize_timeout (float, optional): time in seconds to wait before considering temperature stabilized. Defaults to 10.
            verbose (bool, optional): verbosity of class. Defaults to False.
            simulation (bool, optional): whether to simulate. Defaults to False.
        """
        super().__init__(device_type=QInstrumentsDevice, port=port, verbose=verbose, simulation=simulation, **kwargs)
        assert isinstance(self.device, QInstrumentsDevice), "Ensure device is of type `QInstrumentsDevice`"
        self.device: QInstrumentsDevice = self.device
        
        self.limits = {
            'acceleration': (0,9999),
            'speed': (0,9999),
            'temperature': (0,9999)
        }
        self.ranges = {
            'speed': (0,9999),
            'temperature': (0,9999)
        }
        self._threads = {}
        
        # Data logging attributes
        self.buffer: deque[tuple[NamedTuple, datetime]] = deque(maxlen=MAX_LEN)
        self.records: deque[tuple[NamedTuple, datetime]] = deque()
        self.record_event = threading.Event()
        
        # Shaking control attributes
        self.set_speed = self._default_speed
        self.speed = self._default_speed
        self.speed_tolerance = speed_tolerance
        self.shake_time_left = None
        self.acceleration = self._default_acceleration
        
        # Temperature control attributes
        self.set_temperature = self._default_temperature
        self.temperature = self._default_temperature
        self.temp_tolerance = temp_tolerance
        self.stabilize_timeout = stabilize_timeout
        self._stabilize_start_time = None
        
        self.connect()
        return
    
    # Properties
    @property
    def model(self) -> str:
        """Device model description"""
        return self.device.model
    
    @property
    def serial_number(self) -> str:
        """Device serial number"""
        return self.device.serial_number
    
    # Data logging properties
    @property
    def buffer_df(self) -> pd.DataFrame:
        """Buffer dataframe to store collected data"""
        return datalogger.get_dataframe(data_store=self.buffer, fields=self.device.data_type._fields)
    
    @property
    def records_df(self) -> pd.DataFrame:
        """Records dataframe to store collected data"""
        return datalogger.get_dataframe(data_store=self.records, fields=self.device.data_type._fields)
    
    @property
    def is_counterclockwise(self) -> bool:
        """Returns the current mixing direction"""
        return self.flags.counterclockwise
    
    # ELM control properties
    @property
    def is_locked(self) -> bool:
        """Returns the current ELM state"""
        return self.flags.elm_locked
    
    # General methods
    def connect(self):
        """Connect to the device"""
        self.device.connect()
        if self.is_connected:
            self.getDefaults()
            self.getUserLimits()
        return
    
    def execute(self, 
            shake: bool,
            temperature: float|None = None, 
            speed: int|None = None, 
            duration: int|None = None, 
            acceleration: int|None = None, 
            *args, **kwargs
        ):
        """
        Set target temperature, then shake the plate at target speed and hold target temperature for desired duration
        Alias for `holdTemperature()` and `shake()`
        
        Args:
            shake (bool): whether to shake
            temperature (float|None, optional): temperature in degree °C. Defaults to None.
            speed (int|None, optional): shaking speed. Defaults to None.
            duration (int|None, optional): duration of shake. Defaults to None.
            acceleration (int|None, optional): acceleration value. Defaults to None.
        """
        # setTemperature
        if temperature is not None:
            self.setTemperature(temperature)
        
        # shake
        if shake:
            self.shake(speed=speed, duration=duration, acceleration=acceleration)
        
        # holdTemperature
        if temperature is not None and duration:
            self.holdTemperature(temperature=temperature, duration=duration)
            self._logger.info(f"Holding at {self.set_temperature}°C for {duration} seconds")
            time.sleep(duration)
            self._logger.info("End of temperature hold")
            # self.setTemperature(25, False)
        return
    
    def reset(self, timeout:int = 30):
        """
        Restarts the controller
        
        Note: This takes about 30 seconds for BS units and 5 for the Q1, CP models
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 30.
        """
        self.toggleRecord(False)
        self.clearCache()
        self.device.resetDevice(timeout=timeout)
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.controlTemp(on=False)
        self.stop(emergency=False)
        self.home()
        self.grip(on=False)
        time.sleep(2)
        self.disconnect()
        self.resetFlags()
        return 
    
    # Data logging methods
    def clearCache(self):
        """Clears and remove data in buffer"""
        self.buffer.clear()
        self.records.clear()
        return
    
    def getData(self, query:Any|None = None, *args, **kwargs) -> FloatData|None:
        """
        Get data from device
        
        Args:
            query (Any, optional): query to device. Defaults to None.
            
        Returns:
            FloatData|None: data from device
        """
        if not self.device.stream_event.is_set():
            self._logger.debug(query)
            return self.device.query(query, multi_out=False, data_type=FloatData)
        
        data_store = self.records if self.record_event.is_set() else self.buffer
        out = data_store[-1] if len(data_store) else None
        data,_ = out if out is not None else (None,None)
        return data
    
    def record(self, on: bool, show: bool = False, clear_cache: bool = False):
        """
        Start or stop data recording
        
        Args:
            on (bool): whether to start recording
            show (bool, optional): whether to print out data. Defaults to False.
            clear_cache (bool, optional): whether to clear cache. Defaults to False.
        """
        return datalogger.record(
            on=on, show=show, clear_cache=clear_cache, data_store=self.records, 
            device=self.device, event=self.record_event
        )
    
    def stream(self, on: bool, show: bool = False):
        """
        Start or stop data streaming
        
        Args:
            on (bool): whether to start streaming
            show (bool, optional): whether to print out data. Defaults to False.
        """
        return datalogger.stream(
            on=on, show=show, data_store=self.buffer, 
            device=self.device, event=self.record_event
        )
        
    # Initialization methods
    def getDefaults(self):
        """Retrieve the default and starting configuration of the device upon start up"""
        assert self.is_connected, "Device is not connected"
        self.getShakeDirection()
        self.getElmState()
        self.limits['acceleration'] = ( self.device.getShakeAccelerationMin(), self.device.getShakeAccelerationMax() )
        self.limits['speed'] = ( self.device.getShakeMinRpm(), self.device.getShakeMaxRpm() )
        self.limits['temperature'] = ( self.device.getTempMin(), self.device.getTempMax() )
        return
    
    def getErrors(self) -> list[str]:
        """
        Returns a list with errors and warnings which can occur during processing
        
        Returns:
            list[str]: list of errors and warnings
        """
        return self.device.getErrorList()

    def getStatus(self) -> dict[str, int|None]:
        """
        Retrieve the status of the device's ELM, shaker, and temperature control

        Returns:
            dict[str, int|None]: dictionary of states
        """
        return dict(
            elm = self.device.getElmState(),
            shake = self.device.getShakeState(),
            temperature = int(self.device.getTempState())
        )
    
    def getUserLimits(self):
        """Retrieve the user defined limits for speed and temperature"""
        assert self.is_connected, "Device is not connected"
        try:
            self.ranges['temperature'] = ( self.device.getTempLimiterMin(), self.device.getTempLimiterMax() )
        except AttributeError:
            self.ranges['temperature'] = self.limits.get('temperature', (0,9999))
            
        try: 
            self.ranges['speed'] = ( self.device.getShakeSpeedLimitMin(), self.device.getShakeSpeedLimitMax() )
        except AttributeError:
            self.ranges['speed'] = self.limits.get('speed', (0,9999))
        return

    # ECO methods
    def toggleECO(self, on:bool, timeout:int = 5):
        """
        Toggle the economical mode to save energy and decrease abrasion 
        
        Args:
            on (bool): whether to enter eco mode
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        return self.device.setEcoMode(timeout=timeout) if on else self.device.leaveEcoMode(timeout=timeout)
    
    # Shaking methods
    def shake(self,
        speed: int|None = None, 
        duration: int|None = None, 
        blocking: bool = True,
        *,
        acceleration: int|None = None,
        release: threading.Event|None = None
    ):
        """
        Shake the plate at target speed, for specified duration

        Args:
            speed (int|None, optional): shaking speed. Defaults to None.
            duration (int|None, optional): duration of shake. Defaults to None.
            blocking (bool, optional): whether to block until shake is complete. Defaults to True.
            acceleration (int|None, optional): acceleration value. Defaults to None.
            release (threading.Event|None, optional): event to release thread. Defaults to None.
        """
        acceleration = acceleration or self.acceleration
        speed = speed if speed else self.speed
        
        def inner(speed: float, duration: float, release: threading.Event|None = None):
            self.setAcceleration(acceleration=acceleration)
            self.setSpeed(speed=speed)
            if not self.is_locked:
                self.grip(on=True)
            self.toggleShake(on=True, duration=duration)
            self._logger.info(f"Shaking at {speed}rpm for {duration} seconds")
            
            while self.device.getShakeState() == 5:
                time.sleep(0.1)
            if duration:
                time.sleep(duration)
                while self.device.getShakeState() == 7:
                    time.sleep(0.1)
            self._logger.info("End of shake")
            
            if isinstance(release, threading.Event):
                _ = release.clear() if release.is_set() else release.set()
            return
        
        if blocking:
            inner(speed, duration)
            return
        
        release = release if isinstance(release, threading.Event) else threading.Event()
        thread = threading.Thread(target=inner, args=(speed, duration, release))
        thread.start()
        self._threads['shake'] = thread
        return thread, release
      
    def atSpeed(self, 
        speed: float|None = None, 
        *, 
        tolerance: float|None = None
    ) -> bool:
        """
        Checks and returns whether target speed has been reached
        
        Args:
            speed (float|None, optional): target speed. Defaults to None.
            tolerance (float|None, optional): fractional tolerance to be considered on target. Defaults to None.
            
        Returns:
            bool: whether target speed has been reached
        """
        data: FloatData|None = self.getData(query='getShakeActualSpeed')
        if data is None:
            return False
        speed = speed if speed is not None else self.getTargetSpeed()
        tolerance = tolerance or self.speed_tolerance
        self._logger.debug(f"abs({data.data}-{speed}) = {tolerance*speed}")
        return (abs(data.data - speed) <= tolerance*speed) 
    
    def getTargetSpeed(self) -> float|None:
        """
        Returns the set temperature

        Returns:
            float: set temperature
        """
        return self.device.getShakeTargetSpeed()
    
    def getSpeed(self) -> float:
        """
        Returns current mixing speed in rpm

        Returns:
            float: current mixing speed
        """
        return self.device.getShakeActualSpeed()
    
    def setSpeed(self, speed:int, as_default:bool = False):
        """
        Set the target mixing speed
        
        Note: Speed values below 200 RPM are possible, but not recommended

        Args:
            speed (int): target mixing speed
            as_default (bool, optional): whether to change the default speed. Defaults to False.
        """
        limits = self.ranges.get('speed', self.limits['speed'])
        lower_limit, upper_limit = limits
        assert speed >= 200, "Speed values below 200 RPM are not recommended."
        if lower_limit <= speed <= upper_limit:
            self.set_speed = speed
            if as_default:
                self._default_speed = speed
        else:
            raise ValueError(f"Speed out of range {limits}: {speed}")
        return self.device.setShakeTargetSpeed(speed=self.set_speed)
    
    def getAcceleration(self) -> float|None:
        """
        Returns the acceleration/deceleration value

        Returns:
            float: acceleration/deceleration value
        """
        acceleration = self.device.getShakeAcceleration()
        self.acceleration = acceleration if acceleration is not None else self.acceleration
        return acceleration
    
    def setAcceleration(self, acceleration:int, as_default:bool = False):
        """
        Sets the acceleration/deceleration value in seconds

        Args:
            acceleration (int): acceleration value
            as_default (bool, optional): whether to change the default acceleration. Defaults to False.
        """
        limits = self.limits.get('acceleration', ACCELERATION_LIMIT)
        lower_limit, upper_limit = limits
        if lower_limit <= acceleration <= upper_limit:
            self.acceleration = acceleration
            if as_default:
                self._default_acceleration = acceleration
        else:
            raise ValueError(f"Acceleration out of range {limits}: {acceleration}")
        return self.device.setShakeAcceleration(acceleration=self.acceleration)
    
    def getShakeDirection(self) -> bool:
        """
        Returns the current mixing direction

        Returns:
            bool: whether mixing direction is counterclockwise
        """
        counterclockwise = self.device.getShakeDirection()
        self.flags.counterclockwise = counterclockwise if counterclockwise is not None else self.flags.counterclockwise
        return self.flags.counterclockwise
    
    def setCounterClockwise(self, counterclockwise:bool):
        """
        Sets the mixing direction to counter clockwise

        Args:
            counterclockwise (bool): whether to set mixing direction to counter clockwise
        """
        self.device.setShakeDirection(counterclockwise=counterclockwise)
        self.device.getShakeDirection()
        return 
    
    def getShakeTimeLeft(self) -> float|None:
        """
        Returns the remaining shake time in seconds if device was started with the a defined duration

        Returns:
            float|None: minimum target shake speed
        """
        response = self.device.getShakeRemainingTime()
        self.shake_time_left = response
        return self.shake_time_left
    
    def home(self, timeout:int = 5):
        """
        Move shaker to the home position and locks in place
        
        Note: Minimum response time is less than 4 sec (internal failure timeout)
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        gripping = self.is_locked
        if not gripping:
            self.grip(on=True)
        out = self.device.shakeGoHome(timeout=timeout)
        self.grip(on=gripping)
        return out
    
    def stop(self, emergency:bool = True):
        """
        Stop the shaker immediately at an undefined position, ignoring the defined deceleration time if in an emergency
        
        Args:
            emergency (bool, optional): whether to perform an emergency stop. Defaults to True.
        """
        return self.device.shakeEmergencyOff() if emergency else self.device.shakeOffNonZeroPos() 
    
    def toggleShake(self, on:bool, duration:int|None = None, home:bool = True):
        """
        Starts/stops shaking with defined speed with defined acceleration/deceleration time.
        Shake runtime can be specified, as well as whether to return to home position after stopping.

        Args:
            on (bool): whether to start shaking
            duration (int|None, optional): shake runtime. Defaults to None.
            home (bool, optional): whether to return to home when shaking stops. Defaults to True.
        """
        duration = duration if duration is not None else 0
        if not on:
            return self.device.shakeOff() if home else self.device.shakeOffNonZeroPos()
        if duration > 0:
            self.device.shakeOnWithRuntime(duration=duration)
        else:
            self.device.shakeOn()
        self._logger.debug(f"Speed: {self.set_speed} | Time : {duration} | Accel: {self.acceleration}")
        return
    
    # Temperature methods
    def controlTemp(self, on:bool):
        """
        Switches on/off the temperature control feature and starts/stops heating/cooling

        Args:
            on (bool): whether to start temperature control
        """
        return self.device.tempOn() if on else self.device.tempOff()
    
    def atTemperature(self, 
        temperature: float|None = None, 
        *, 
        tolerance: float|None = None,
        stabilize_timeout: float|None = None
    ) -> bool:
        """
        Checks and returns whether target temperature has been reached
        
        Args:
            temperature (float|None, optional): target temperature. Defaults to None.
            tolerance (float|None, optional): fractional tolerance to be considered on target. Defaults to None.
            stabilize_timeout (float|None, optional): time in seconds to wait before considering temperature stabilized. Defaults to None.
            
        Returns:
            bool: whether target temperature has been reached
        """
        data: FloatData|None = self.getData(query='getTempActual')
        if data is None:
            return False
        temperature = temperature if temperature is not None else self.getTargetTemp()
        tolerance = tolerance or self.temp_tolerance
        stabilize_timeout = stabilize_timeout if stabilize_timeout is not None else self.stabilize_timeout
        
        if abs(data.data - temperature) > tolerance*temperature:
            self._stabilize_start_time = None
            return False
        self._stabilize_start_time = self._stabilize_start_time or time.perf_counter()
        if ((time.perf_counter()-self._stabilize_start_time) < stabilize_timeout):
            return False
        return True
    
    def getTargetTemp(self) -> float|None:
        """
        Returns the set temperature

        Returns:
            float: set temperature
        """
        return self.device.getTempTarget()
    
    def getTemperature(self) -> float|None:
        """
        Get temperature
        
        Returns:
            float: actual temperature
        """
        return self.device.getTempActual() 
    
    def setTemperature(self, 
        temperature: float, 
        blocking: bool = True, 
        *, 
        tolerance: float = None, 
        release: threading.Event = None
    ) -> tuple[threading.Thread, threading.Event]|None:
        """
        Set target temperature between TempMin and TempMax in 1/10°C increments
        
        Args:
            temperature (float): target temperature
            blocking (bool, optional): whether to block until temperature is reached. Defaults to True.
            tolerance (float, optional): fractional tolerance to be considered on target. Defaults to None.
            release (threading.Event, optional): event to release thread. Defaults to None.
            
        Returns:
            tuple[threading.Thread, threading.Event]|None: thread and event
        """
        ret = super().setTemperature(temperature, blocking, tolerance=tolerance, release=release)
        if not blocking:
            return
        thread, event = ret
        self._threads['temperature'] = thread
        return thread, event
    
    def _set_temperature(self, temperature: float):
        limits = self.ranges.get('temperature', self.limits['temperature'])
        lower_limit, upper_limit = limits
        assert lower_limit <= temperature <= upper_limit, f"Temperature out of range {limits}: {temperature}"
        self.controlTemp(on=True)
        self.device.setTempTarget(temperature=temperature)
        return
    
    # ELM (i.e. grip) methods
    def getElmState(self) -> int:
        """
        Returns the current ELM state

        Returns:
            int: ELM state
        """
        state = self.device.getElmState()
        self.flags.elm_locked = (state<2) if state in (1,3) else self.flags.elm_locked
        return state
    
    def grip(self, on:bool):
        """
        Grip or release the object

        Args:
            on (bool): whether to grip the object
        """
        _ = self.device.setElmLockPos() if on else self.device.setElmUnlockPos()
        self.flags.elm_locked = on
        return
    
    # Dunder method(s)
    def __info__(self):
        """Prints the boot screen text"""
        response = self.device.info()
        self._logger.info(response)
        return 
    
    def __serial__(self) -> str:
        """
        Returns the device serial number
        
        Returns:
            str: device serial number
        """
        return self.device.getSerial()
    
    def __version__(self) -> str:
        """
        Retrieve the software version on the device

        Returns:
            str: device version
        """
        return self.device.getVersion()
 
