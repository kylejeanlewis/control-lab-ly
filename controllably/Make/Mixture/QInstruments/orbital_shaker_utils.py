# %% -*- coding: utf-8 -*-
"""
This module holds the class for shakers from QInstruments.

Classes:
    BioShakeD30 (Maker)
"""
# Standard library imports
from __future__ import annotations
import numpy as np
import time
from typing import Optional, Union

# Local application imports
from ...make_utils import Maker
from .qinstruments_api import QInstruments
print(f"Import: OK <{__name__}>")

class BioShake(Maker):
    _default_acceleration: int = 5
    _default_speed: int = 500
    _default_flags = {
        'elm_locked': True,
        'shake_counterclockwise': True,
        'speed_reached': False,
        'temperature_reached': False
    }
    def __init__(self, port: str, **kwargs):
        super().__init__(**kwargs)
        self.device: QInstruments = None
        self.model = ''
        
        self.acceleration = self._default_acceleration
        self.shake_time_left = None
        self.speed = self._default_speed
        self.temperature = None
        self.tolerance = 0.01
        
        self.limit_acceleration = None
        self.limit_speed = None
        self.limit_temperature = None
        self.range_speed = None
        self.range_temperature = None
        self.set_speed = None
        self.set_temperature = None
        
        self._verbose = kwargs.get('verbose', False)
        self._connect(port)
        return
    
    # Properties
    @property
    def acceleration(self) -> float:
        return self._acceleration
    
    @property
    def verbose(self) -> bool:
        return self._verbose
    @verbose.setter
    def verbose(self, value:bool):
        self._verbose = bool(value)
        try:
            self.device.verbose = self._verbose
        except AttributeError:
            pass
        return
    @verbose.deleter
    def verbose(self):
        del self._verbose
        return
    
    def __defaults__(self):
        """Retrieve the default and starting configuration of the device upon start up."""
        self.isCounterClockwise()
        self.isLocked()
        self.limit_acceleration = ( self.device.getShakeAccelerationMin(), self.device.getShakeAccelerationMax() )
        self.limit_speed = ( self.device.getShakeMinRpm(), self.device.getShakeMaxRpm() )
        self.limit_temperature = ( self.device.getTempMin(), self.device.getTempMax() )
        return
    
    def __info__(self):
        """Prints the boot screen text"""
        response = self._query("info", slow=True)
        print(response)
        return 
    
    def __model__(self) -> str:
        """
        Retrieve the model of the device

        Returns:
            str: model name
        """
        response = self.device.getDescription()
        print(f'Model: {response}')
        return response
    
    def __serial__(self) -> str:
        """
        Returns the device serial number
        
        Returns:
            str: device serial number
        """
        return self._query("getSerial", slow=True)
    
    def __version__(self) -> str:
        """
        Retrieve the software version on the device

        Returns:
            str: device version
        """
        return self.device.getVersion()
    
    def getAcceleration(self) -> float:
        """
        Returns the acceleration/deceleration value

        Returns:
            float: acceleration/deceleration value
        """
        response = self.device.getShakeAcceleration()
        self._acceleration = response if response is not None else self.acceleration
        return self.acceleration
    
    def getErrors(self) -> list[str]:
        """
        Returns a list with errors and warnings which can occur during processing
        
        Returns:
            list[str]: list of errors and warnings
        """
        return self.device.getErrorList()

    def getShakeTimeLeft(self) -> Optional[float]:
        """
        Returns the remaining shake time in seconds if device was started with the a defined duration

        Returns:
            Optional[float]: minimum target shake speed
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
        
        flag = (self.set_speed == self.speed)
        self.setFlag(speed_reached=flag)
        return self.set_speed, self.speed
    
    def getStatus(self, verbose:bool = True) -> tuple[Optional[int]]:
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
        response = self.device.getTempTarget()
        self.set_temperature = response if response is not None else self.set_temperature
        response = self.device.getTempActual()
        self.temperature = response if response is not None else self.temperature
        
        flag = (self.set_temperature == self.temperature)
        self.setFlag(temperature_reached=flag)
        return self.set_temperature, self.temperature
    
    def getUserLimits(self):
        """Retrieve the user defined limits for speed and temperature"""
        self.range_speed = ( self.device.getShakeSpeedLimitMin(), self.device.getShakeSpeedLimitMax() )
        self.range_temperature = ( self.device.getTempLimiterMin(), self.device.getTempLimiterMax() )
        return

    def holdTemperature(self, temperature:float, time_s:float):
        """
        Hold target temperature for desired duration

        Args:
            temperature (float): temperature in degree Celsius
            time_s (float): duration in seconds
        """
        self.setTemperature(temperature)
        print(f"Holding at {self.set_temperature}°C for {time_s} seconds")
        time.sleep(time_s)
        print(f"End of temperature hold")
        return
    
    def home(self, timeout:int = 5):
        """
        Move shaker to the home position and locks in place
        
        Note: Minimum response time is less than 4 sec (internal failure timeout)
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        return self.device.shakeGoHome(timeout=timeout)
    
    def isAtSpeed(self) -> bool:
        """
        Checks and returns whether target speed has been reached

        Returns:
            bool: whether target speed has been reached
        """
        return self.flags['speed_reached']
    
    def isAtTemperature(self) -> bool:
        """
        Checks and returns whether target temperature has been reached

        Returns:
            bool: whether target temperature has been reached
        """
        return self.flags['temperature_reached']
    
    def isCounterClockwise(self) -> bool:
        """
        Returns the current mixing direction

        Returns:
            bool: whether mixing direction is counterclockwise
        """
        response = self.device.getShakeDirection()
        response = response if response is not None else self.flags['shake_counterclockwise']
        self.setFlag(shake_counterclockwise=response)
        return self.flags['shake_counterclockwise']
    
    def isLocked(self) -> bool:
        """
        Returns the current ELM state

        Returns:
            bool: whether ELM is locked
        """
        response = self.device.getElmState()
        response = (response<2) if response in (1,3) else self.flags['elm_locked']
        self.setFlag(elm_locked=response)
        return self.flags['elm_locked']
    
    def reset(self, timeout:int = 30):
        """
        Restarts the controller
        
        Note: This takes about 30 seconds for BS units and 5 for the Q1, CP models
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 30.
        """
        self.device.resetDevice(timeout=timeout)
        return

    def setAcceleration(self, acceleration:int, default:bool = False):
        """
        Sets the acceleration/deceleration value in seconds

        Args:
            acceleration (int): acceleration value
            default (bool, optional): whether to change the default acceleration. Defaults to False.
        """
        lower_limit, upper_limit = self.limit_acceleration
        if lower_limit <= acceleration <= upper_limit:
            self._acceleration = acceleration
            if default:
                self._default_acceleration = acceleration
        return self.device.setShakeAcceleration(acceleration=self.acceleration)
    
    def setCounterClockwise(self, counterclockwise:bool):
        """
        Sets the mixing direction to counter clockwise

        Args:
            counterclockwise (bool): whether to set mixing direction to counter clockwise
        """
        self.device.setShakeDirection(counterclockwise=counterclockwise)
        response = self.device.getShakeDirection()
        response = response if response is not None else self.flags['shake_counterclockwise']
        self.setFlag(shake_counterclockwise=response)
        return 
    
    def setSpeed(self, speed:int, default:bool = False):
        """
        Set the target mixing speed
        
        Note: Speed values below 200 RPM are possible, but not recommended

        Args:
            speed (int): target mixing speed
            default (bool, optional): whether to change the default speed. Defaults to False.
        """
        lower_limit, upper_limit = self.range_speed
        if speed < 200:
            print("Speed values below 200 RPM are not recommended.")
            return
        if lower_limit <= speed <= upper_limit:
            self.set_speed = speed
            if default:
                self._default_speed = speed
        return self.device.setShakeTargetSpeed(speed=self.set_speed)
    
    def setTemperature(self, temperature:float, blocking:bool = True):
        """
        Sets target temperature between TempMin and TempMax in 1/10°C increments

        Args:
            temperature (float): target temperature (between TempMin and TempMax)
            blocking (bool, optional): whether to wait for temperature to reach set point. Defaults to True.
        """
        lower_limit, upper_limit = self.range_temperature
        if lower_limit <= temperature <= upper_limit:
            self.set_temperature = temperature
        self.device.setTempTarget(temperature=temperature)
        
        while self.set_temperature != self.device.getTempTarget():
            self.getTemperature()
        print(f"New set temperature at {self.set_temperature}°C")
        self.setFlag(temperature_reached=False)
        
        if blocking:
            print(f"Waiting for temperature to reach {self.set_temperature}°C")
        while not self.isAtTemperature():
            self.getTemperature()
            time.sleep(0.1)
            if not blocking:
                break
        return
    
    def shake(self,
            speed: Optional[int] = None, 
            duration: Optional[int] = None, 
            acceleration: Optional[int] = None
        ):
        """
        Shake the plate at target speed, for specified duration

        Args:
            speed (Optional[int], optional): shaking speed. Defaults to None.
            duration (Optional[int], optional): duration of shake. Defaults to None.
            acceleration (Optional[int], optional): acceleration value. Defaults to None.
        """
        acceleration = acceleration if acceleration else self._default_acceleration
        self.setAcceleration(acceleration=acceleration)
        speed = speed if speed else self._default_speed
        self.setSpeed(speed=speed)
        
        if not self.isLocked():
            self.toggleGrip(on=True)
        self.toggleShake(on=True, duration=duration)
        return
        
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.toggleTemperatureControl(on=False)
        self.stop(emergency=False)
        self.home()
        self.toggleGrip(on=False)
        time.sleep(2)
        self.device.disconnect()
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
    
    def toggleShake(self, on:bool, duration:Optional[int] = None, home:bool = True):
        """
        Starts/stops shaking with defined speed with defined acceleration/deceleration time.
        Shake runtime can be specified, as well as whether to return to home position after stopping.

        Args:
            on (bool): whether to start shaking
            duration (Optional[int], optional): shake runtime. Defaults to None.
            home (bool, optional): whether to return to home when shaking stops. Defaults to True.
        """
        if on:
            if duration is None:
                self.device.shakeOn()
            elif duration > 0:
                self.device.shakeOnWithRuntime(duration=duration)
        else:
            if home:
                self.device.shakeOff()
            else:
                self.device.shakeOffNonZeroPos()
        return
    
    def toggleTemperatureControl(self, on:bool):
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
            device = QInstruments(port, baudrate, timeout=timeout)
            self.device = device
        except Exception as e:
            print(f"Could not connect to {port}")
            if self.verbose:
                print(e)
        else:
            print(f"Connection opened to {port}")
            self.model = device.model
            self.setFlag(connected=True)
            self.__defaults__()
            self.getUserLimits()
        return
    
    def _query(self, 
            command: str, 
            numeric: bool = False, 
            slow: bool = False, 
            timeout_s: float = 0.3
        ) -> Union[str, float]:
        """
        Write command to and read response from device

        Args:
            command (str): command string
            numeric(bool, optional): whether to expect a numeric response. Defaults to False.
            slow (bool, optional): whether to expect a slow response. Defaults to False.
            timeout_s (float, optional): duration to wait before timeout. Defaults to 0.3.
        Returns:
            str: response string
        """
        return self.device.query(command=command, numeric=numeric, slow=slow, timeout_s=timeout_s)

    def _read(self) -> str:
        """
        Read response from device

        Returns:
            str: response string
        """
        return self.device.read()
    
    def _write(self, command:str) -> bool:
        """
        Write command to device

        Args:
            command (str): <command code><value>

        Returns:
            bool: whether command was sent successfully
        """
        return self.device.write(command=command)
