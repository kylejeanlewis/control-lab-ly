# -*- coding: utf-8 -*-
"""
This module holds the base class for cartesian mover tools.

Attributes:
    ACCELERATION_LIMIT (tuple): lower and upper limits for acceleration
    COLUMNS (tuple): headers for output data from BioShake device
    FLAGS (SimpleNamespace): default flags for BioShake

## Classes:
    `BioShake`: BioShake provides methods to control the QInstruments BioShake device.

<i>Documentation last updated: 2024-11-16/i>
"""
# Standard library imports
from __future__ import annotations
from collections import deque
from datetime import datetime
import logging
import threading
from threading import Thread
import time
from types import SimpleNamespace
from typing import NamedTuple, Any

# Third party imports
import pandas as pd

# Local application imports
from ....core.device import DataLoggerUtils
from ... import Maker
from ...Heat.heater_mixin import HeaterMixin
from .qinstruments_api import QInstrumentsDevice
from .qinstruments_api.qinstruments_api import _QInstrumentsDevice, FloatData

logger = logging.getLogger("controllably.Make")
logger.debug(f"Import: OK <{__name__}>")

MAX_LEN = 100

ACCELERATION_LIMIT = (1,30)
COLUMNS = ('Time', 'Set', 'Actual')
"""Headers for output data from BioShake device"""
FLAGS = SimpleNamespace(
    busy=False, elm_locked=True, get_feedback=False, pause_feedback=False, record=False, 
    shake_counterclockwise=True, speed_reached=False, temperature_reached=False, verbose=False
)
"""Default flags for BioShake"""
_FLAGS = SimpleNamespace(
    busy=False, #at_speed=False, at_temperature=False, 
    elm_locked=True, counterclockwise=True, verbose=False
)

class _BioShake(Maker, HeaterMixin):
    """
    BioShake provides methods to control the QInstruments BioShake device.
    
    ### Constructor
        `port` (str): serial port address
        `verbose` (bool, optional): verbosity of class. Defaults to False.
        `simulation` (bool, optional): whether to simulate. Defaults to False.
    
    ### Attributes and properties
        `buffer_df` (pd.DataFrame): buffer dataframe to store collected data
        `limits` (dict[str, tuple]): hardware limits for device
        `model` (str): device model description
        `ranges` (dict[str, tuple]): user-defined ranges for controls
        `acceleration` (float): acceleration / deceleration of the shaker in seconds
        `speed` (float): actual speed of shake in rpm
        `set_speed` (float): target speed
        `at_speed` (bool): checks and returns whether target speed has been reached
        `temperature` (float): actual temperature of the plate in °C 
        `set_temperature` (float): target temperature
        `tolerance` (float): fractional tolerance to be considered on target for speed and temperature
        `at_temperature` (bool): checks and returns whether target temperature has been reached
        `shake_time_left` (float): remaining time left on shaker
        `is_counterclockwise` (bool): returns the current mixing direction
        `is_locked` (bool): returns the current ELM state
        `connection_details` (dict): connection details for the device
        `device` (Device): device object that communicates with physical tool
        `flags` (SimpleNamespace[str, bool]): flags for the class
        `is_busy` (bool): whether the device is busy
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
    
    ### Methods
        `clearCache`: clears and remove data in buffer
        `getAcceleration`: returns the acceleration/deceleration value
        `getErrors`: returns a list with errors and warnings which can occur during processing
        `getShakeTimeLeft`: returns the remaining shake time in seconds if device was started with the a defined duration
        `getSpeed`: returns the set speed and current mixing speed in rpm
        `getStatus`: retrieve the status of the device's ELM, shaker, and temperature control
        `getTemperature`: returns the set temperature and current temperature in °C
        `getUserLimits`: retrieve the user defined limits for speed and temperature
        `holdTemperature`: hold target temperature for desired duration
        `home`: move shaker to the home position and locks in place
        `reset`: restarts the controller
        `setAcceleration`: sets the acceleration/deceleration value in seconds
        `setCounterClockwise`: sets the mixing direction to counter clockwise
        `setSpeed`: set the target mixing speed
        `setTemperature`: sets target temperature between TempMin and TempMax in 1/10°C increments
        `shake`: shake the plate at target speed, for specified duration
        `stop`: stop the shaker immediately at an undefined position, ignoring the defined deceleration time if in an emergency
        `toggleECO`: toggle the economical mode to save energy and decrease abrasion 
        `toggleFeedbackLoop`: start or stop feedback loop
        `toggleGrip`: grip or release the object
        `toggleRecord`: start or stop data recording
        `toggleShake`: starts/stops shaking with defined speed with defined acceleration/deceleration time
        `toggleTemperature`: switches on/off the temperature control feature and starts/stops heating/cooling
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `execute`: Set target temperature, then shake the plate at target speed and hold target temperature for desired duration
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `run`: alias for `execute()`
        `shutdown`: shutdown procedure for tool
    """
    
    _default_acceleration: int = 5
    _default_speed: int = 500
    _default_temperature: float = 25
    _default_flags = _FLAGS
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
        Instantiate the class

        Args:
            port (str): serial port address
            verbose (bool, optional): verbosity of class. Defaults to False.
            simulation (bool, optional): whether to simulate. Defaults to False.
        """
        super().__init__(device_type=_QInstrumentsDevice, port=port, verbose=verbose, simulation=simulation, **kwargs)
        assert isinstance(self.device, _QInstrumentsDevice), "Ensure device is of type `QInstrumentsDevice`"
        self.device: _QInstrumentsDevice = self.device
        
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
        return self.device.model
    
    @property
    def serial_number(self) -> str:
        return self.device.serial_number
    
    # Data logging properties
    @property
    def buffer_df(self) -> pd.DataFrame:
        return DataLoggerUtils.getDataframe(data_store=self.buffer, fields=self.device.data_type._fields)
    
    @property
    def records_df(self) -> pd.DataFrame:
        return DataLoggerUtils.getDataframe(data_store=self.records, fields=self.device.data_type._fields)
    
    # Temperature control properties
    # @property
    # def at_temperature(self) -> bool:
    #     return self.atTemperature(None)
    
    # Shaking control properties
    # @property
    # def at_speed(self) -> bool:
    #     return self.atSpeed(None)
    
    @property
    def is_counterclockwise(self) -> bool:
        return self.flags.counterclockwise
    
    # ELM control properties
    @property
    def is_locked(self) -> bool:
        return self.flags.elm_locked
    
    # General methods
    def connect(self):
        """Connect to the device"""
        self.device.connect()
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
            self._logger.info(f"End of temperature hold")
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
        self.buffer = deque(maxlen=MAX_LEN)
        self.records = deque()
        return
    
    def getData(self, query:Any|None = None, *args, **kwargs) -> FloatData|None:
        """
        Get data from device
        """
        if not self.device.stream_event.is_set():
            return self.device.query(query, multi_out=False, data_type=FloatData)
        
        data_store = self.records if self.record_event.is_set() else self.buffer
        out = data_store[-1] if len(data_store) else None
        data,_ = out if out is not None else (None,None)
        return data
    
    def record(self, on: bool, show: bool = False, clear_cache: bool = False):
        return DataLoggerUtils.record(
            on=on, show=show, clear_cache=clear_cache, data_store=self.records, 
            device=self.device, event=self.record_event
        )
    
    def stream(self, on: bool, show: bool = False):
        return DataLoggerUtils.stream(
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

        Args:
            verbose (bool, optional): whether to print out state. Defaults to True.

        Returns:
            tuple[int]: ELM status, shaker status, temperature control status
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
        except:
            self.ranges['speed'] = self.limits.get('speed', (0,9999))
        return

    # ECO methods
    def toggleECO(self, on:bool, timeout:int = 5):
        """
        Toggle the economical mode to save energy and decrease abrasion 
        
        Args:
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
            acceleration (int|None, optional): acceleration value. Defaults to None.
        """
        acceleration = acceleration or self.acceleration
        speed = speed if speed else self.speed
        
        def inner(speed: float, duration: float, release: threading.Event|None = None):
            logger = logging.getLogger(f"{self.__class__}.{self.__class__.__name__}_{id(self)}")
            self.setAcceleration(acceleration=acceleration)
            self.setSpeed(speed=speed)
            if not self.is_locked:
                self.grip(on=True)
            self.toggleShake(on=True, duration=duration)
            logger.info(f"Shaking at {speed}rpm for {duration} seconds")
            
            start_time = time.perf_counter()
            shake_time = time.perf_counter() - start_time
            while not self.atSpeed(speed):
                shake_time = time.perf_counter() - start_time
                if shake_time > self.acceleration:
                    break
                time.sleep(0.1)
            time.sleep(abs(duration - shake_time))
            logger.info("End of shake")
            
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
        data: FloatData|None = self.getData(data='getShakeActualSpeed')
        if data is None:
            return False
        speed = speed if speed is not None else self.getTargetSpeed()
        tolerance = tolerance or self.speed_tolerance
        
        return (abs(data.data - speed) <= tolerance) 
    
    def getTargetSpeed(self) -> float|None:
        """
        Returns the set temperature

        Returns:
            float: set temperature
        """
        return self.device.getShakeTargetSpeed()
    
    def getSpeed(self) -> tuple[float]:
        """
        Returns the set speed and current mixing speed in rpm

        Returns:
            tuple[float]: set speed, current mixing speed
        """
        return self.device.getShakeActualSpeed()
    
    def setSpeed(self, speed:int, as_default:bool = False):
        """
        Set the target mixing speed
        
        Note: Speed values below 200 RPM are possible, but not recommended

        Args:
            speed (int): target mixing speed
            default (bool, optional): whether to change the default speed. Defaults to False.
        """
        limits = self.ranges.get('speed', (200,201))
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
            default (bool, optional): whether to change the default acceleration. Defaults to False.
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
        return self.device.shakeGoHome(timeout=timeout)
    
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
        data: FloatData|None = self.getData(data='getTempActual')
        if data is None:
            return False
        temperature = temperature if temperature is not None else self.getTargetTemp()
        tolerance = tolerance or self.temp_tolerance
        stabilize_timeout = stabilize_timeout if stabilize_timeout is not None else self.stabilize_timeout
        
        if abs(data.data - temperature) > tolerance:
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
        """
        return self.device.getTempActual() 
    
    def setTemperature(self, temperature, blocking = True, *, tolerance = None, release = None):
        thread, event = super().setTemperature(temperature, blocking, tolerance=tolerance, release=release)
        self._threads['temperature'] = thread
        return thread, event
    
    def _set_temperature(self, temperature: float):
        limits = self.ranges.get('temperature', (0,99))
        lower_limit, upper_limit = limits
        assert lower_limit <= temperature <= upper_limit, f"Temperature out of range {limits}: {temperature}"
        self.controlTemp(on=True)
        self.device.setTempTarget(temperature=temperature)
        
        buffer = self.records if self.record_event.is_set() else self.buffer
        if not self.device.stream_event.is_set():
            self.device.startStream(
                data=self.device.processInput('getTempActual'), 
                buffer=buffer, data_type=FloatData
            )
            time.sleep(0.1)
        
        while self.device.getTempTarget() != temperature:
            time.sleep(0.1)
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
 

class BioShake(Maker):
    """
    BioShake provides methods to control the QInstruments BioShake device.
    
    ### Constructor
        `port` (str): serial port address
        `verbose` (bool, optional): verbosity of class. Defaults to False.
        `simulation` (bool, optional): whether to simulate. Defaults to False.
    
    ### Attributes and properties
        `buffer_df` (pd.DataFrame): buffer dataframe to store collected data
        `limits` (dict[str, tuple]): hardware limits for device
        `model` (str): device model description
        `ranges` (dict[str, tuple]): user-defined ranges for controls
        `acceleration` (float): acceleration / deceleration of the shaker in seconds
        `speed` (float): actual speed of shake in rpm
        `set_speed` (float): target speed
        `at_speed` (bool): checks and returns whether target speed has been reached
        `temperature` (float): actual temperature of the plate in °C 
        `set_temperature` (float): target temperature
        `tolerance` (float): fractional tolerance to be considered on target for speed and temperature
        `at_temperature` (bool): checks and returns whether target temperature has been reached
        `shake_time_left` (float): remaining time left on shaker
        `is_counterclockwise` (bool): returns the current mixing direction
        `is_locked` (bool): returns the current ELM state
        `connection_details` (dict): connection details for the device
        `device` (Device): device object that communicates with physical tool
        `flags` (SimpleNamespace[str, bool]): flags for the class
        `is_busy` (bool): whether the device is busy
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
    
    ### Methods
        `clearCache`: clears and remove data in buffer
        `getAcceleration`: returns the acceleration/deceleration value
        `getErrors`: returns a list with errors and warnings which can occur during processing
        `getShakeTimeLeft`: returns the remaining shake time in seconds if device was started with the a defined duration
        `getSpeed`: returns the set speed and current mixing speed in rpm
        `getStatus`: retrieve the status of the device's ELM, shaker, and temperature control
        `getTemperature`: returns the set temperature and current temperature in °C
        `getUserLimits`: retrieve the user defined limits for speed and temperature
        `holdTemperature`: hold target temperature for desired duration
        `home`: move shaker to the home position and locks in place
        `reset`: restarts the controller
        `setAcceleration`: sets the acceleration/deceleration value in seconds
        `setCounterClockwise`: sets the mixing direction to counter clockwise
        `setSpeed`: set the target mixing speed
        `setTemperature`: sets target temperature between TempMin and TempMax in 1/10°C increments
        `shake`: shake the plate at target speed, for specified duration
        `stop`: stop the shaker immediately at an undefined position, ignoring the defined deceleration time if in an emergency
        `toggleECO`: toggle the economical mode to save energy and decrease abrasion 
        `toggleFeedbackLoop`: start or stop feedback loop
        `toggleGrip`: grip or release the object
        `toggleRecord`: start or stop data recording
        `toggleShake`: starts/stops shaking with defined speed with defined acceleration/deceleration time
        `toggleTemperature`: switches on/off the temperature control feature and starts/stops heating/cooling
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `execute`: Set target temperature, then shake the plate at target speed and hold target temperature for desired duration
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `run`: alias for `execute()`
        `shutdown`: shutdown procedure for tool
    """
    
    _default_acceleration: int = 5
    _default_speed: int = 500
    _default_temperature: float = 25
    _default_flags = FLAGS
    def __init__(self, port: str, *, verbose: bool = False, simulation:bool = False, **kwargs):
        """
        Instantiate the class

        Args:
            port (str): serial port address
            verbose (bool, optional): verbosity of class. Defaults to False.
            simulation (bool, optional): whether to simulate. Defaults to False.
        """
        super().__init__(device_type=QInstrumentsDevice, port=port, verbose=verbose, simulation=simulation, **kwargs)
        assert isinstance(self.device, QInstrumentsDevice), "Ensure device is of type `QInstrumentsDevice`"
        self.device: QInstrumentsDevice = self.device
        self.buffer_df = pd.DataFrame(columns=list(COLUMNS))
        
        self.set_speed = self._default_speed
        self.set_temperature = self._default_temperature
        self.speed = self._default_speed
        self.temperature = self._default_temperature
        
        self.shake_time_left = None
        self.tolerance = 0.05
        
        self.limits = {
            'acceleration': (0,9999),
            'speed': (0,9999),
            'temperature': (0,9999)
        }
        self.ranges = {
            'speed': (0,9999),
            'temperature': (0,9999)
        }
        self._acceleration = self._default_acceleration
        self._columns = list(COLUMNS)
        self._threads = {}
        
        self.connect()
        return
    
    # Properties
    @property
    def acceleration(self) -> float:
        return self._acceleration
    
    @property
    def at_speed(self) -> bool:
        """
        Checks and returns whether target speed has been reached

        Returns:
            bool: whether target speed has been reached
        """
        self.getSpeed()
        return self.flags.speed_reached
    
    @property
    def at_temperature(self) -> bool:
        """
        Checks and returns whether target temperature has been reached

        Returns:
            bool: whether target temperature has been reached
        """
        return self.flags.temperature_reached
    
    @property
    def is_counterclockwise(self) -> bool:
        """
        Returns the current mixing direction

        Returns:
            bool: whether mixing direction is counterclockwise
        """
        response = self.device.getShakeDirection()
        response = response if response is not None else self.flags.shake_counterclockwise
        self.flags.shake_counterclockwise = response
        return self.flags.shake_counterclockwise
    
    @property
    def is_locked(self) -> bool:
        """
        Returns the current ELM state

        Returns:
            bool: whether ELM is locked
        """
        response = self.device.getElmState()
        response = (response<2) if response in (1,3) else self.flags.elm_locked
        self.flags.elm_locked = response
        return self.flags.elm_locked
    
    @property
    def model(self) -> str:
        return self.device.model
    
    def clearCache(self):
        """Clears and remove data in buffer"""
        self.flags.pause_feedback = True
        time.sleep(0.1)
        self.buffer_df = pd.DataFrame(columns=self._columns)
        self.flags.pause_feedback = False
        return
    
    def getAcceleration(self) -> float:
        """
        Returns the acceleration/deceleration value

        Returns:
            float: acceleration/deceleration value
        """
        response = self.device.getShakeAcceleration()
        self._acceleration = response if response is not None else self.acceleration
        return self.acceleration
    
    def getDefaults(self):
        """Retrieve the default and starting configuration of the device upon start up"""
        self.is_counterclockwise
        self.is_locked
        if not self.is_connected:
            return
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

    def getShakeTimeLeft(self) -> float|None:
        """
        Returns the remaining shake time in seconds if device was started with the a defined duration

        Returns:
            float|None: minimum target shake speed
        """
        response = self.device.getShakeRemainingTime()
        self.shake_time_left = response
        return self.shake_time_left
    
    def getSpeed(self) -> tuple[float]:
        """
        Returns the set speed and current mixing speed in rpm

        Returns:
            tuple[float]: set speed, current mixing speed
        """
        response = self.device.getShakeTargetSpeed()
        self.set_speed = response if response is not None else self.set_speed
        response = self.device.getShakeActualSpeed()
        self.speed = response if response is not None else self.speed
        
        flag = (abs(self.speed - self.set_speed) <= self.tolerance*self.set_speed) if self.set_speed else False
        self.flags.speed_reached = flag
        return self.set_speed, self.speed
    
    def getStatus(self) -> tuple[int|None]:
        """
        Retrieve the status of the device's ELM, shaker, and temperature control

        Args:
            verbose (bool, optional): whether to print out state. Defaults to True.

        Returns:
            tuple[int]: ELM status, shaker status, temperature control status
        """
        state_elm = self.device.getElmState()
        state_shake = self.device.getShakeState()
        state_temperature = int(self.device.getTempState())
        return state_elm, state_shake, state_temperature
    
    def getTemperature(self) -> tuple[float]:
        """
        Returns the set temperature and current temperature in °C

        Returns:
            tuple[float]: set temperature, current temperature
        """
        now = datetime.now()
        response = self.device.getTempTarget()
        self.set_temperature = response if response is not None else self.set_temperature
        response = self.device.getTempActual()
        self.temperature = response if response is not None else self.temperature
        
        flag = (abs(self.temperature - self.set_temperature) <= self.tolerance*self.set_temperature) if self.set_temperature else False
        self.flags.temperature_reached = flag
        
        if self.flags.record:
            values = [now, self.set_temperature, self.temperature]
            row = {k:v for k,v in zip(self._columns, values)}
            new_row_df = pd.DataFrame(row, index=[0])
            dfs = [_df for _df in [self.buffer_df, new_row_df] if len(_df)]
            self.buffer_df = pd.concat(dfs, ignore_index=True)
        return self.set_temperature, self.temperature
    
    def getUserLimits(self):
        """Retrieve the user defined limits for speed and temperature"""
        if not self.is_connected:
            return
        try:
            self.ranges['temperature'] = ( self.device.getTempLimiterMin(), self.device.getTempLimiterMax() )
            self.ranges['speed'] = ( self.device.getShakeSpeedLimitMin(), self.device.getShakeSpeedLimitMax() )
        except AttributeError:
            self.ranges['temperature'] = self.limits.get('temperature', (0,9999))
            self.ranges['speed'] = self.limits.get('speed', (0,9999))
        return

    def holdTemperature(self, temperature:float, time_s:float):
        """
        Hold target temperature for desired duration

        Args:
            temperature (float): temperature in degree °C
            time_s (float): duration in seconds
        """
        self.setTemperature(temperature)
        self._logger.info(f"Holding at {self.set_temperature}°C for {time_s} seconds")
        time.sleep(time_s)
        self._logger.info(f"End of temperature hold ({time_s}s)")
        return
    
    def home(self, timeout:int = 5):
        """
        Move shaker to the home position and locks in place
        
        Note: Minimum response time is less than 4 sec (internal failure timeout)
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        return self.device.shakeGoHome(timeout=timeout)
    
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

    def setAcceleration(self, acceleration:int, default:bool = False):
        """
        Sets the acceleration/deceleration value in seconds

        Args:
            acceleration (int): acceleration value
            default (bool, optional): whether to change the default acceleration. Defaults to False.
        """
        limits = self.limits.get('acceleration', ACCELERATION_LIMIT)
        lower_limit, upper_limit = limits
        if lower_limit <= acceleration <= upper_limit:
            self._acceleration = acceleration
            if default:
                self._default_acceleration = acceleration
        # else:
        #     raise ValueError(f"Acceleration out of range {limits}: {acceleration}")
        return self.device.setShakeAcceleration(acceleration=self.acceleration)
    
    def setCounterClockwise(self, counterclockwise:bool):
        """
        Sets the mixing direction to counter clockwise

        Args:
            counterclockwise (bool): whether to set mixing direction to counter clockwise
        """
        self.device.setShakeDirection(counterclockwise=counterclockwise)
        response = self.device.getShakeDirection()
        response = response if response is not None else counterclockwise
        self.flags.shake_counterclockwise = response
        return 
    
    def setSpeed(self, speed:int, default:bool = False):
        """
        Set the target mixing speed
        
        Note: Speed values below 200 RPM are possible, but not recommended

        Args:
            speed (int): target mixing speed
            default (bool, optional): whether to change the default speed. Defaults to False.
        """
        limits = self.ranges.get('speed', (200,201))
        lower_limit, upper_limit = limits
        if speed < 200:
            self._logger.warning("Speed values below 200 RPM are not recommended.")
            return
        if lower_limit <= speed <= upper_limit:
            self.set_speed = speed
            if default:
                self._default_speed = speed
        else:
            raise ValueError(f"Speed out of range {limits}: {speed}")
        return self.device.setShakeTargetSpeed(speed=self.set_speed)
    
    def setTemperature(self, temperature:float, blocking:bool = True):
        """
        Sets target temperature between TempMin and TempMax in 1/10°C increments

        Args:
            temperature (float): target temperature (between TempMin and TempMax)
            blocking (bool, optional): whether to wait for temperature to reach set point. Defaults to True.
        """
        self.toggleTemperature(on=True)
        limits = self.ranges.get('temperature', (0,99))
        lower_limit, upper_limit = limits
        if lower_limit <= temperature <= upper_limit:
            self.set_temperature = float(temperature)
            self.device.setTempTarget(temperature=temperature)
        else:
            raise ValueError(f"Temperature out of range {limits}: {temperature}")
        
        while self.set_temperature != float(temperature):
            self.getTemperature()
        self._logger.info(f"New set temperature at {self.set_temperature}°C")
        self.flags.temperature_reached = False
        
        if blocking:
            self._logger.info(f"Waiting for temperature to reach {self.set_temperature}°C")
        while not self.at_temperature:
            self.getTemperature()
            time.sleep(0.1)
            if not blocking:
                break
        return
    
    def shake(self,
            speed: int|None = None, 
            duration: int|None = None, 
            acceleration: int|None = None
        ):
        """
        Shake the plate at target speed, for specified duration

        Args:
            speed (int|None, optional): shaking speed. Defaults to None.
            duration (int|None, optional): duration of shake. Defaults to None.
            acceleration (int|None, optional): acceleration value. Defaults to None.
        """
        acceleration = acceleration if acceleration else self._default_acceleration
        self.setAcceleration(acceleration=acceleration)
        speed = speed if speed else self._default_speed
        self.setSpeed(speed=speed)
        
        if not self.is_locked:
            self.toggleGrip(on=True)
        self.toggleShake(on=True, duration=duration)
        
        def checkSpeed():
            start_time = time.perf_counter()
            shake_time = time.perf_counter() - start_time
            while not self.at_speed:
                shake_time = time.perf_counter() - start_time
                if shake_time > self.acceleration:
                    break
                time.sleep(1)
            if duration:
                time.sleep(abs(duration - shake_time))
                self._logger.info(f"End of shake ({duration}s)")
            return self.at_speed
        thread = Thread(target=checkSpeed)
        thread.start()
        self._threads['check_speed'] = thread
        return
        
    def stop(self, emergency:bool = True):
        """
        Stop the shaker immediately at an undefined position, ignoring the defined deceleration time if in an emergency
        
        Args:
            emergency (bool, optional): whether to perform an emergency stop. Defaults to True.
        """
        return self.device.shakeEmergencyOff() if emergency else self.device.shakeOffNonZeroPos() 

    def toggleECO(self, on:bool, timeout:int = 5):
        """
        Toggle the economical mode to save energy and decrease abrasion 
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        return self.device.setEcoMode(timeout=timeout) if on else self.device.leaveEcoMode(timeout=timeout)
    
    def toggleFeedbackLoop(self, on:bool):
        """
        Start or stop feedback loop

        Args:
            on (bool): whether to start loop to continuously read from device
        """
        self.flags.get_feedback = on
        if on:
            if 'feedback_loop' in self._threads:
                self._threads['feedback_loop'].join()
            thread = Thread(target=self._loop_feedback)
            thread.start()
            self._threads['feedback_loop'] = thread
        else:
            self._threads['feedback_loop'].join()
        return
     
    def toggleGrip(self, on:bool):
        """
        Grip or release the object

        Args:
            on (bool): whether to grip the object
        """
        return self.device.setElmLockPos() if on else self.device.setElmUnlockPos()
    
    def toggleRecord(self, on:bool):
        """
        Start or stop data recording

        Args:
            on (bool): whether to start recording temperature
        """
        self.flags.record = on
        self.flags.get_feedback = on
        self.flags.pause_feedback = False
        self.toggleFeedbackLoop(on=on)
        return
    
    def toggleShake(self, on:bool, duration:int|None = None, home:bool = True):
        """
        Starts/stops shaking with defined speed with defined acceleration/deceleration time.
        Shake runtime can be specified, as well as whether to return to home position after stopping.

        Args:
            on (bool): whether to start shaking
            duration (int|None, optional): shake runtime. Defaults to None.
            home (bool, optional): whether to return to home when shaking stops. Defaults to True.
        """
        if on:
            if duration is None:
                self.device.shakeOn()
            elif duration > 0:
                self.device.shakeOnWithRuntime(duration=duration)
            self._logger.debug(f"Speed: {self.set_speed} | Accel: {self.acceleration} | Time : {duration}")
        else:
            _ = self.device.shakeOff() if home else self.device.shakeOffNonZeroPos()
        return
    
    def toggleTemperature(self, on:bool):
        """
        Switches on/off the temperature control feature and starts/stops heating/cooling

        Args:
            on (bool): whether to start temperature control
        """
        return self.device.tempOn() if on else self.device.tempOff()
    
    # Overwritten method(s)
    def connect(self):
        """Connect to the device"""
        self.device.connect()
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
            self._logger.info(f"Holding at {self.set_temperature}°C for {duration} seconds")
            time.sleep(duration)
            self._logger.info(f"End of temperature hold")
            # self.setTemperature(25, False)
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.toggleTemperature(on=False)
        self.stop(emergency=False)
        self.home()
        self.toggleGrip(on=False)
        time.sleep(2)
        self.disconnect()
        self.resetFlags()
        return 

    # Protected method(s)
    def _loop_feedback(self):
        """Loop to constantly read from device"""
        print('Listening...')
        while self.flags.get_feedback:
            if self.flags.pause_feedback:
                continue
            self.getTemperature()
            time.sleep(0.1)
        print('Stop listening...')
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
    
    # Deprecated method(s)
    def isAtSpeed(self) -> bool:
        """
        Checks and returns whether target speed has been reached

        Returns:
            bool: whether target speed has been reached
        """
        self._logger.warning("This method is deprecated. Use `at_speed` instead.")
        return self.at_speed
    
    def isAtTemperature(self) -> bool:
        """
        Checks and returns whether target temperature has been reached

        Returns:
            bool: whether target temperature has been reached
        """
        self._logger.warning("This method is deprecated. Use `at_temperature` instead.")
        return self.at_temperature
    
    def isCounterClockwise(self) -> bool:
        """
        Returns the current mixing direction

        Returns:
            bool: whether mixing direction is counterclockwise
        """
        self._logger.warning("This method is deprecated. Use `is_counterclockwise` instead.")
        return self.is_counterclockwise
    
    def isLocked(self) -> bool:
        """
        Returns the current ELM state

        Returns:
            bool: whether ELM is locked
        """
        self._logger.warning("This method is deprecated. Use `is_locked` instead.")
        return self.is_locked
    