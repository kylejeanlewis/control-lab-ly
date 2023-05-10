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
    _default_flags = {
        'elm_startup_unlocked': True,
        'shake_counterclockwise': False
    }
    def __init__(self, port: str, **kwargs):
        super().__init__(**kwargs)
        self.device: QInstruments = None
        
        self.acceleration = self._default_acceleration
        self.shake_time_left = 0
        self.speed = None
        self.temperature = None
        
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
       
    def getErrors(self) -> list[str]:
        """
        Returns a list with errors and warnings which can occur during processing
        
        Returns:
            list[str]: list of errors and warnings
        """
        return self.device.getErrorList()

    def getHardwareDefaults(self):  # TODO: docs
        flag_elm = self.device.getElmStartupPosition()
        flag_shake = self.device.getShakeDefaultDirection()
        self._default_flags['elm_startup_unlocked'] = flag_elm
        self._default_flags['shake_counterclockwise'] = flag_shake
        self.setFlag(elm_startup_unlocked=flag_elm, shake_counterclockwise=flag_shake)
        
        self.limit_acceleration = ( self.device.getShakeAccelerationMin(), self.device.getShakeAccelerationMax() )
        self.limit_speed = ( self.device.getShakeMinRpm(), self.device.getShakeMaxRpm() )
        self.limit_temperature = ( self.device.getTempMin(), self.device.getTempMax() )
        return
    
    def getStatus(self, verbose:bool = True) -> tuple:  # TODO: docs
        state_elm = self.device.getElmState(verbose=verbose)
        state_shake = self.device.getShakeState(verbose=verbose)
        state_temperature = self.device.getTempState()
        return state_elm, state_shake, state_temperature
    
    def getUserLimits(self):    # TODO: docs
        self.range_speed = ( self.device.getShakeSpeedLimitMin(), self.device.getShakeSpeedLimitMax() )
        self.range_temperature = ( self.device.getTempLimiterMin(), self.device.getTempLimiterMax() )
        return

    def home(self, timeout:int = 5):
        """
        Move shaker to the home position and locks in place
        
        Note: Minimum response time is less than 4 sec (internal failure timeout)
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        return self.device.shakeGoHome(timeout=timeout)
    
    def isCounterClockwise(self) -> Optional[bool]:
        """
        Returns the current mixing direction

        Returns:
            Optional[bool]: whether mixing direction is counterclockwise
        """
        response = self.device.getShakeDirection()
        self.setFlag(shake_counterclockwise=response)
        return self.flags['shake_counterclockwise']
    
    def reset(self, timeout:int = 30):
        """
        Restarts the controller
        
        Note: This takes about 30 seconds for BS units and 5 for the Q1, CP models
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 30.
        """
        self.device.resetDevice(timeout=timeout)
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.device.disconnect()
        return 

    # Shaking methods
    def getAcceleration(self) -> Optional[float]:
        """
        Returns the acceleration/deceleration value

        Returns:
            Optional[float]: acceleration/deceleration value
        """
        self.acceleration = self.device.getShakeAcceleration()
        return self.acceleration
    
    def getShakeTimeLeft(self) -> Optional[float]:  # TODO
        """
        Returns the remaining time in seconds if device was started with the command `shakeOnWithRuntime`

        Returns:
            Optional[float]: minimum target shake speed
        """
        return self.device.getShakeRemainingTime()
    
    def getSpeed(self) -> Optional[float]:  # TODO: docs
        """
        Returns the current mixing speed

        Returns:
            Optional[float]: current mixing speed
        """
        self.set_speed = self.device.getShakeTargetSpeed()
        self.speed = self.device.getShakeActualSpeed()
        return self.speed
    
    def getTemperature(self) -> Optional[float]:    # TODO: docs
        """
        Returns the current temperature in °C

        Returns:
            Optional[float]: current temperature in °C
        """
        self.set_temperature = self.device.getTempTarget()
        self.temperature = self.device.getTempActual()
        return self.temperature
    
    def setAcceleration(self, acceleration:int):
        """
        Sets the acceleration/deceleration value in seconds

        Args:
            value (int): acceleration value
        """
        return self.device.setShakeAcceleration(acceleration=acceleration)
    
    def setDirection(self, counterclockwise:bool):
        """
        Sets the mixing direction

        Args:
            counterclockwise (bool): whether to set mixing direction to counter clockwise
        """
        return self.device.setShakeDirection(counterclockwise=counterclockwise)
    
    def setSpeed(self, speed:int):
        """
        Set the target mixing speed
        
        Note: Speed values below 200 RPM are possible, but not recommended

        Args:
            speed (int): target mixing speed
        """
        return self.device.setShakeTargetSpeed(speed=speed)
    
    def setTemperature(self, temperature:float):
        """
        Sets target temperature between TempMin and TempMax in 1/10°C increments

        Args:
            temperature (float): target temperature (between TempMin and TempMax)
        """
        self.device.setTempTarget(temperature=temperature)
        return
    
    def shake(self, speed:int, duration:Optional[int] = None):    # TODO
        self.setSpeed(speed=speed)
        self.toggleShake(on=True, duration=duration)
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
        except Exception as e:
            print(f"Could not connect to {port}")
            if self.verbose:
                print(e)
        else:
            print(f"Connection opened to {port}")
            self.setFlag(connected=True)
            self.getHardwareDefaults()
        self.device = device
        return
    
    def _query(self, 
            command:str, 
            numeric:bool = False, 
            slow:bool = False, 
            timeout_s:float = 0.3
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
