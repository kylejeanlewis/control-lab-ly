# -*- coding: utf-8 -*-
"""
This module holds the class for shakers from QInstruments.

## Classes:
    BioShake (Maker)
"""
# Standard library imports
from __future__ import annotations
from datetime import datetime
import logging
from threading import Thread
import time
from types import SimpleNamespace
from typing import final

# Third party imports
import pandas as pd

# Local application imports
from ... import Maker
from .qinstruments_api import QInstrumentsDevice

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

ACCELERATION_LIMIT = (1,30)
COLUMNS = ('Time', 'Set', 'Actual')
"""Headers for output data from BioShake device"""
FLAGS = SimpleNamespace(
    busy=False, elm_locked=True, get_feedback=False, pause_feedback=False, record=False, 
    shake_counterclockwise=True, speed_reached=False, temperature_reached=False, verbose=False
)
"""Default flags for BioShake"""

@final
class BioShake(Maker):
    """
    BioShake provides methods to control the QInstruments BioShake device.
    
    ### Constructor
    Args:
        `port` (str): COM port address
    
    ### Attributes
    - `buffer_df` (pd.DataFrame): buffer dataframe to store collected data
    - `device` (Callable): device object that communicates with physical tool
    - `limits` (dict[str, tuple]): hardware limits for device
    - `model` (str): device model description
    - `ranges` (dict[str, tuple]): user-defined ranges for controls
    - `set_speed` (float): target speed
    - `set_temperature` (float): target temperature
    - `shake_time_left` (float): remaining time left on shaker
    - `speed` (float): actual speed of shake in rpm
    - `temperature` (float): actual temperature of the plate in °C 
    - `tolerance` (float): fractional tolerance to be considered on target for speed and temperature
    
    ### Properties
    - `acceleration` (float): acceleration / deceleration of the shaker in seconds
    - `port` (str): COM port address
    - `verbose` (bool): verbosity of class
    
    ### Methods
    - `clearCache`: clears and remove data in buffer
    - `execute`: alias for `holdTemperature()` and `shake()`
    - `getAcceleration`: returns the acceleration/deceleration value
    - `getErrors`: returns a list with errors and warnings which can occur during processing
    - `getShakeTimeLeft`: returns the remaining shake time in seconds if device was started with the a defined duration
    - `getSpeed`: returns the set speed and current mixing speed in rpm
    - `getStatus`: retrieve the status of the device's ELM, shaker, and temperature control
    - `getTemperature`: returns the set temperature and current temperature in °C
    - `getUserLimits`: retrieve the user defined limits for speed and temperature
    - `holdTemperature`: hold target temperature for desired duration
    - `home`: move shaker to the home position and locks in place
    - `isAtSpeed`: checks and returns whether target speed has been reached
    - `isAtTemperature`: checks and returns whether target temperature has been reached
    - `isCounterClockwise`: returns the current mixing direction
    - `isLocked`: returns the current ELM state
    - `reset`: restarts the controller
    - `setAcceleration`: sets the acceleration/deceleration value in seconds
    - `setCounterClockwise`: sets the mixing direction to counter clockwise
    - `setSpeed`: set the target mixing speed
    - `setTemperature`: sets target temperature between TempMin and TempMax in 1/10°C increments
    - `shake`: shake the plate at target speed, for specified duration
    - `shutdown`: shutdown procedure for tool
    - `stop`: stop the shaker immediately at an undefined position, ignoring the defined deceleration time if in an emergency
    - `toggleECO`: toggle the economical mode to save energy and decrease abrasion 
    - `toggleFeedbackLoop`: start or stop feedback loop
    - `toggleGrip`: grip or release the object
    - `toggleRecord`: start or stop data recording
    - `toggleShake`: starts/stops shaking with defined speed with defined acceleration/deceleration time
    - `toggleTemperature`: switches on/off the temperature control feature and starts/stops heating/cooling
    """
    
    _default_acceleration: int = 5
    _default_speed: int = 500
    _default_temperature: float = 25
    _default_flags = FLAGS
    def __init__(self, port: str, *, verbose: bool = False, **kwargs):
        """
        Instantiate the class

        Args:
            port (str): COM port address
        """
        super().__init__(device_type=QInstrumentsDevice, port=port, verbose=verbose, **kwargs)
        assert isinstance(self.device, QInstrumentsDevice), f"Device ({self.device}) not supported for {self.__class__.__name__}"
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
    
    @property
    def port(self) -> str:
        return self.device.connection_details.get('port', '')
    
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
    
    def getStatus(self, verbose:bool = True) -> tuple[int|None]:
        """
        Retrieve the status of the device's ELM, shaker, and temperature control

        Args:
            verbose (bool, optional): whether to print out state. Defaults to True.

        Returns:
            tuple[int]: ELM status, shaker status, temperature control status
        """
        state_elm = self.device.getElmState(verbose=verbose)
        state_shake = self.device.getShakeState(verbose=verbose)
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
        out = f"Holding at {self.set_temperature}°C for {time_s} seconds"
        logger.info(out)
        print(out)
        time.sleep(time_s)
        out = f"End of temperature hold ({time_s}s)"
        logger.info(out)
        print(out)
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
            logger.warning("Speed values below 200 RPM are not recommended.")
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
        out = f"New set temperature at {self.set_temperature}°C"
        logger.info(out)
        print(out)
        self.flags.temperature_reached = False
        
        if blocking:
            out = f"Waiting for temperature to reach {self.set_temperature}°C"
            logger.info(out)
            print(out)
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
                out = f"End of shake ({duration}s)"
                logger.info(out)
                print(out)
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
        if emergency:
            return self.device.shakeEmergencyOff()
        return self.device.shakeOffNonZeroPos()

    def toggleECO(self, on:bool, timeout:int = 5):
        """
        Toggle the economical mode to save energy and decrease abrasion 
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        if on:
            self.device.setEcoMode(timeout=timeout)
        else:
            self.device.leaveEcoMode(timeout=timeout)
        return
    
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
        if on:
            self.device.setElmLockPos()
        else:
            self.device.setElmUnlockPos()
        return
    
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
            logger.info(f"Speed: {self.set_speed}")
            logger.info(f"Accel: {self.acceleration}")
            logger.info(f"Time : {duration}")
        else:
            if home:
                self.device.shakeOff()
            else:
                self.device.shakeOffNonZeroPos()
        return
    
    def toggleTemperature(self, on:bool):
        """
        Switches on/off the temperature control feature and starts/stops heating/cooling

        Args:
            on (bool): whether to start temperature control
        """
        if on:
            self.device.tempOn()
        else:
            self.device.tempOff()
        return
    
    # Overwritten method(s)
    def connect(self):
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
        Alias for `holdTemperature()` and `shake()`
        
        Set target temperature, then shake the plate at target speed and hold target temperature for desired duration

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
            out = f"Holding at {self.set_temperature}°C for {duration} seconds"
            logger.info(out)
            print(out)
            time.sleep(duration)
            out = f"End of temperature hold"
            logger.info(out)
            print(out)
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
        print(response)
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
        logger.warning("This method is deprecated. Use `at_speed` instead.")
        return self.at_speed
    
    def isAtTemperature(self) -> bool:
        """
        Checks and returns whether target temperature has been reached

        Returns:
            bool: whether target temperature has been reached
        """
        logger.warning("This method is deprecated. Use `at_temperature` instead.")
        return self.at_temperature
    
    def isCounterClockwise(self) -> bool:
        """
        Returns the current mixing direction

        Returns:
            bool: whether mixing direction is counterclockwise
        """
        logger.warning("This method is deprecated. Use `is_counterclockwise` instead.")
        return self.is_counterclockwise
    
    def isLocked(self) -> bool:
        """
        Returns the current ELM state

        Returns:
            bool: whether ELM is locked
        """
        logger.warning("This method is deprecated. Use `is_locked` instead.")
        return self.is_locked
    