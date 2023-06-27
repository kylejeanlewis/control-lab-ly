# %% -*- coding: utf-8 -*-
"""
This module surfaces the actions available for the devices from QInstruments.

Classes:
    QInstruments
"""
# Standard library imports
from __future__ import annotations
import numpy as np
import time
from typing import Optional, Union

# Third party imports
import serial   # pip install pyserial

# Local application imports
from .qinstruments_lib import ELMStateCode, ELMStateString, ShakeStateCode, ShakeStateString
print(f"Import: OK <{__name__}>")

class QInstruments:
    """
    QInstruments surfaces available actions to control devices from QInstruments, including orbital shakers,
    heat plates, and cold plates.
    
    ### Constructor
    Args:
        `port` (str): COM port address
        `baudrate` (int, optional): baudrate. Defaults to 9600.
        `timeout` (int, optional): timeout in seconds. Defaults to 1.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes
    - `connection_details` (dict): dictionary of connection details (e.g. COM port / IP address)
    - `device` (Callable): device object that communicates with physical tool
    - `flags` (dict[str, bool]): keywords paired with boolean flags
    - `model` (str): device model
    - `verbose` (bool): verbosity of class
    
    ### Methods
    #### Initialization
    - `disableBootScreen`: permanent deactivation of the boot screen startup text
    - `disableCLED`: permanent deactivation of the LED indication lights
    - `enableBootScreen`: permanent activation of the boot screen startup text
    - `enableCLED`: permanent activation of the LED indication lights
    - `flashLed`: user device LED flashes five times
    - `getCLED`: returns the status LED state
    - `getDescription`: returns model type
    - `getErrorList`: returns a list with errors and warnings which can occur during processing
    - `getSerial`: returns the device serial number
    - `getVersion`: returns the firmware version number
    - `info`: prints the boot screen text
    - `resetDevice`: restarts the controller
    - `setBuzzer`: ring the buzzer for duration in milliseconds
    - `version`: returns the model type and firmware version number
    #### ECO
    - `leaveEcoMode`: leaves the economical mode and switches into the normal operating state
    - `setEcoMode`: witches the shaker into economical mode and reduces electricity consumption
    #### Shaking
    - `getShakeAcceleration`: returns the acceleration/deceleration value
    - `getShakeAccelerationMax`: get the maximum acceleration/deceleration time in seconds
    - `getShakeAccelerationMin`: get the minimum acceleration/deceleration time in seconds
    - `getShakeActualSpeed`: returns the current mixing speed
    - `getShakeDefaultDirection`: returns the mixing direction when the device starts up
    - `getShakeDirection`: returns the current mixing direction
    - `getShakeMaxRpm`: returns the device specific maximum target speed (i.e. hardware limits)
    - `getShakeMinRpm`: returns the device specific minimum target speed (i.e. hardware limits)
    - `getShakeRemainingTime`: returns the remaining time in seconds if device was started with the command `shakeOnWithRuntime`
    - `getShakeSpeedLimitMax`: returns the upper limit for the target speed
    - `getShakeSpeedLimitMin`: returns the lower limit for the target speed
    - `getShakeState`: returns shaker state as an integer
    - `getShakeStateAsString`: returns shaker state as a string
    - `getShakeTargetSpeed`: returns the target mixing speed
    - `setShakeAcceleration`: sets the acceleration/deceleration value in seconds
    - `setShakeDefaultDirection`: permanently sets the default mixing direction after device start up
    - `setShakeDirection`: sets the mixing direction
    - `setShakeSpeedLimitMax`: permanently set upper limit for the target speed (between 0 to 3000)
    - `setShakeSpeedLimitMin`: permanently set lower limit for the target speed (between 0 to 3000)
    - `setShakeTargetSpeed`: set the target mixing speed
    - `shakeEmergencyOff`: stop the shaker immediately at an undefined position ignoring the defined deceleration time
    - `shakeGoHome`: move shaker to the home position and locks in place
    - `shakeOff`: stops shaking within the defined deceleration time, go to the home position and locks in place
    - `shakeOffNonZeroPos`: tops shaking within the defined deceleration time, do not go to home position and do not lock in home position
    - `shakeOffWithDeEnergizeSolenoid`: tops shaking within the defined deceleration time, go to the home position and locks in place for 1 second, then unlock home position
    - `shakeOn`: tarts shaking with defined speed with defined acceleration time
    - `shakeOnWithRuntime`: starts shaking with defined speed within defined acceleration time for given time value in seconds
    #### Temperature
    - `getTemp40Calibr`: returns the offset value at the 40°C calibration point
    - `getTemp90Calibr`: returns the offset value at the 90°C calibration point
    - `getTempActual`: returns the current temperature in celsius
    - `getTempLimiterMax`: returns the upper limit for the target temperature in celsius
    - `getTempLimiterMin`: returns the lower limit for the target temperature in celsius
    - `getTempMax`: returns the device specific maximum target temperature in celsius (i.e. hardware limits)
    - `getTempMin`: returns the device specific minimum target temperature in celsius (i.e. hardware limits)
    - `getTempState`: returns the state of the temperature control feature
    - `getTempTarget`: returns the target temperature
    - `setTemp40Calibr`: permanently sets the offset value at the 40°C calibration point in 1/10°C increments
    - `setTemp90Calibr`: permanently sets the offset value at the 90°C calibration point in 1/10°C increments
    - `setTempLimiterMax`: permanently sets the upper limit for the target temperature in 1/10°C increments
    - `setTempLimiterMin`: permanently sets the lower limit for the target temperature in 1/10°C increments
    - `setTempTarget`: sets target temperature between TempMin and TempMax in 1/10°C increments
    - `tempOff`: switches off the temperature control feature and stops heating/cooling
    - `tempOn`: switches on the temperature control feature and starts heating/cooling
    #### ELM
    - `getElmSelftest`: returns whether the ELM self-test is enabled or disabled at device startup
    - `getElmStartupPosition`: returns whether ELM is unlocked after device startup
    - `getElmState`: returns the ELM status
    - `getElmStateAsString`: returns the ELM status as a string
    - `setElmLockPos`: close the ELM
    - `setElmSelftest`: permanently set whether the ELM self-test is enabled at device startup
    - `setElmStartupPosition`: permanently set whether the ELM is unlocked after device startup
    - `setElmUnlockPos`: open the ELM
    #### General
    - `connect`: reconnect to device using existing connection details
    - `disconnect`: disconnect from device
    - `query`: write command to and read response from device
    - `read`: read response from device
    - `setFlag`: set flags by using keyword arguments
    - `write`: write command to device
    """
    
    _default_flags: dict[str, bool] = {'busy': False, 'connected': False}
    def __init__(self, 
        port: str, 
        baudrate:int = 9600, 
        timeout:int = 1, 
        verbose:bool = False, 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            port (str): COM port address
            baudrate (int, optional): baudrate. Defaults to 9600.
            timeout (int, optional): timeout in seconds. Defaults to 1.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.connection_details = {}
        self.device = None
        self.flags = self._default_flags.copy()
        self.model = ''
        self.verbose = verbose
        self._connect(port=port, baudrate=baudrate, timeout=timeout)
        return
        
    # Initialization methods
    def disableBootScreen(self):
        """Permanent deactivation of the boot screen startup text"""
        self.query("disableBootScreen")
        return
    
    def disableCLED(self):
        """Permanent deactivation of the LED indication lights. The instrument will reset after this command."""
        self.query("disableCLED")
        return
    
    def enableBootScreen(self):
        """Permanent activation of the boot screen startup text"""
        self.query("enableBootScreen")
        return
    
    def enableCLED(self):
        """Permanent activation of the LED indication lights. The instrument will reset after this command."""
        self.query("enableCLED")
        return
    
    def flashLed(self):
        """User device LED flashes five times"""
        self.query("flashLed")
        return

    def getCLED(self) -> Optional[bool]:
        """
        Returns the status LED state
        
        Returns:
            Optional[bool]: whether the LED is enabled
        """
        response = self.query("getCLED", numeric=True)
        if response is np.nan:
            return None
        state = bool(int(response)%2)
        return state
        
    def getDescription(self) -> str:
        """
        Returns model type
        
        Returns:
            str: model type
        """
        return self.query("getDescription", slow=True)
        
    def getErrorList(self) -> list[str]:
        """
        Returns a list with errors and warnings which can occur during processing
        
        Returns:
            list[str]: list of errors and warnings
        """
        response = self.query("getErrorList", slow=True)
        error_list = response[1:-1].split("; ")
        return error_list
        
    def getSerial(self) -> str:
        """
        Returns the device serial number
        
        Returns:
            str: device serial number
        """
        return self.query("getSerial", slow=True)
        
    def getVersion(self) -> str:
        """
        Returns the firmware version number

        Returns:
            str: firmware version number
        """
        return self.query("getVersion", slow=True)
        
    def info(self):
        """Prints the boot screen text"""
        response = self.query("info", slow=True)
        print(response)
        return 
        
    def resetDevice(self, timeout:int = 30):
        """
        Restarts the controller
        
        Note: This takes about 30 seconds for BS units and 5 for the Q1, CP models
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 30.
        """
        self.query("resetDevice")
        start_time = time.perf_counter()
        while self.getShakeState(verbose=False) != 3:
            time.sleep(0.1)
            if time.perf_counter() - start_time > timeout:
                break
        self.getShakeState()
        return
        
    def setBuzzer(self, duration:int):
        """
        Ring the buzzer for duration in milliseconds

        Args:
            duration (int): duration in milliseconds, from 50 to 999
        """
        if 50 <= duration <= 999:
            self.query(f"setBuzzer{int(duration)}")
        else:
            print("Please input duration of between 50 and 999 milliseconds.")
        return
        
    def version(self) -> str:
        """
        Returns the model type and firmware version number

        Returns:
            str: model type and firmware version number
        """
        return self.query("version", slow=True)
    
    # ECO methods
    def leaveEcoMode(self, timeout:int = 5):
        """
        Leaves the economical mode and switches into the normal operating state
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        self.query("leaveEcoMode")
        start_time = time.perf_counter()
        while self.getShakeState(verbose=False) != 3:
            time.sleep(0.1)
            if time.perf_counter() - start_time > timeout:
                break
        self.getShakeState()
        return
    
    def setEcoMode(self, timeout:int = 5):
        """
        Switches the shaker into economical mode and reduces electricity consumption.
        
        Note: all commands after this, other than leaveEcoMode, will return `e`
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        response = self.query("setEcoMode")
        start_time = time.perf_counter()
        while not response:
            if time.perf_counter() - start_time > timeout:
                break
            response = self.read()
        return
        
    # Shaking methods
    def getShakeAcceleration(self) -> Optional[float]:
        """
        Returns the acceleration/deceleration value

        Returns:
            Optional[float]: acceleration/deceleration value
        """
        response = self.query("getShakeAcceleration", numeric=True)
        if response is np.nan:
            return None
        return response
        
    def getShakeAccelerationMax(self) -> Optional[float]:
        """
        Get the maximum acceleration/deceleration time in seconds

        Returns:
            Optional[float]: acceleration/deceleration time in seconds
        """
        response = self.query("getShakeAccelerationMax", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def getShakeAccelerationMin(self) -> Optional[float]:
        """
        Get the minimum acceleration/deceleration time in seconds

        Returns:
            Optional[float]: acceleration/deceleration time in seconds
        """
        response = self.query("getShakeAccelerationMin", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def getShakeActualSpeed(self) -> Optional[float]:
        """
        Returns the current mixing speed

        Returns:
            Optional[float]: current mixing speed
        """
        response = self.query("getShakeActualSpeed", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def getShakeDefaultDirection(self) -> Optional[bool]:
        """
        Returns the mixing direction when the device starts up

        Returns:
            Optional[bool]: whether mixing direction is counterclockwise
        """
        response = self.query("getShakeDefaultDirection", numeric=True)
        if response is np.nan:
            return None
        state = bool(int(response)%2)
        return state
        
    def getShakeDirection(self) -> Optional[bool]:
        """
        Returns the current mixing direction

        Returns:
            Optional[bool]: whether mixing direction is counterclockwise
        """
        response = self.query("getShakeDirection", numeric=True)
        if response is np.nan:
            return None
        state = bool(int(response)%2)
        return state
        
    def getShakeMaxRpm(self) -> Optional[float]:
        """
        Returns the device specific maximum target speed (i.e. hardware limits)

        Returns:
            Optional[float]: maximum target shake speed
        """
        response = self.query("getShakeMaxRpm", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def getShakeMinRpm(self) -> Optional[float]:
        """
        Returns the device specific minimum target speed (i.e. hardware limits)

        Returns:
            Optional[float]: minimum target shake speed
        """
        response = self.query("getShakeMinRpm", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def getShakeRemainingTime(self) -> Optional[float]:
        """
        Returns the remaining time in seconds if device was started with the command `shakeOnWithRuntime`

        Returns:
            Optional[float]: minimum target shake speed
        """
        response = self.query("getShakeRemainingTime", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def getShakeSpeedLimitMax(self) -> Optional[float]:
        """
        Returns the upper limit for the target speed

        Returns:
            Optional[float]: upper limit for the target speed
        """
        response = self.query("getShakeSpeedLimitMax", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def getShakeSpeedLimitMin(self) -> Optional[float]:
        """
        Returns the lower limit for the target speed

        Returns:
            Optional[float]: lower limit for the target speed
        """
        response = self.query("getShakeSpeedLimitMin", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def getShakeState(self, verbose:bool = True) -> Optional[int]:
        """
        Returns shaker state as an integer
        
        Args:
            verbose (bool, optional): whether to print out state. Defaults to True.
        
        Returns:
            Optional[int]: shaker state as integer
        """
        response = self.query("getShakeState", numeric=True)
        if response is np.nan:
            return None
        code = f"ss{int(response)}"
        if verbose and code in ShakeStateCode._member_names_:
            print(ShakeStateCode[code].value)
        return int(response)
        
    def getShakeStateAsString(self, verbose:bool = True) -> str:
        """
        Returns shaker state as a string
        
        Args:
            verbose (bool, optional): whether to print out state. Defaults to True.
        
        Returns:
            Optional[str]: shaker state as string
        """
        response = self.query("getShakeStateAsString")
        code = response.replace("+","t").replace("-","_")
        if verbose and code in ShakeStateString._member_names_:
            print(ShakeStateString[code].value)
        return response
        
    def getShakeTargetSpeed(self) -> Optional[float]:
        """
        Returns the target mixing speed

        Returns:
            Optional[float]: target mixing speed
        """
        response = self.query("getShakeTargetSpeed", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def setShakeAcceleration(self, acceleration:int):
        """
        Sets the acceleration/deceleration value in seconds

        Args:
            value (int): acceleration value
        """
        self.query(f"setShakeAcceleration{int(acceleration)}")
        return
    
    def setShakeDefaultDirection(self, counterclockwise:bool):
        """
        Permanently sets the default mixing direction after device start up

        Args:
            counterclockwise (bool): whether to set default mixing direction to counter clockwise
        """
        self.query(f"setShakeDefaultDirection{int(counterclockwise)}")
        return
    
    def setShakeDirection(self, counterclockwise:bool):
        """
        Sets the mixing direction

        Args:
            counterclockwise (bool): whether to set mixing direction to counter clockwise
        """
        self.query(f"setShakeDirection{int(counterclockwise)}")
        return
    
    def setShakeSpeedLimitMax(self, speed:int):
        """
        Permanently set upper limit for the target speed (between 0 to 3000)

        Args:
            speed (int): upper limit for the target speed
        """
        self.query(f"setShakeSpeedLimitMax{int(speed)}")
        return
    
    def setShakeSpeedLimitMin(self, speed:int):
        """
        Permanently set lower limit for the target speed (between 0 to 3000)
        
        Note: Speed values below 200 RPM are possible, but not recommended

        Args:
            speed (int): lower limit for the target speed
        """
        self.query(f"setShakeSpeedLimitMin{int(speed)}")
        return
        
    def setShakeTargetSpeed(self, speed:int):
        """
        Set the target mixing speed
        
        Note: Speed values below 200 RPM are possible, but not recommended

        Args:
            speed (int): target mixing speed
        """
        self.query(f"setShakeTargetSpeed{int(speed)}")
        return
        
    def shakeEmergencyOff(self):
        """Stop the shaker immediately at an undefined position ignoring the defined deceleration time"""
        self.query("shakeEmergencyOff")
        return
        
    def shakeGoHome(self, timeout:int = 5):
        """
        Move shaker to the home position and locks in place
        
        Note: Minimum response time is less than 4 sec (internal failure timeout)
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        self.query("shakeGoHome")
        start_time = time.perf_counter()
        while self.getShakeState(verbose=False) != 3:
            time.sleep(0.1)
            if time.perf_counter() - start_time > timeout:
                break
        self.getShakeState()
        return
        
    def shakeOff(self):
        """Stops shaking within the defined deceleration time, go to the home position and locks in place"""
        self.query("shakeOff")
        return
        
    def shakeOffNonZeroPos(self):
        """Stops shaking within the defined deceleration time, do not go to home position and do not lock in home position"""
        self.query("shakeOffNonZeroPos")
        return
        
    def shakeOffWithDeEnergizeSolenoid(self):
        """
        Stops shaking within the defined deceleration time, go to the home position and locks in place for 1 second, 
        then unlock home position
        """
        self.query("shakeOffWithDeenergizeSoleonid")
        return
        
    def shakeOn(self):
        """Starts shaking with defined speed with defined acceleration time"""
        self.query("shakeOn")
        return
    
    def shakeOnWithRuntime(self, duration:int):
        """
        Starts shaking with defined speed within defined acceleration time for given time value in seconds

        Args:
            duration (int): shake duration in seconds (from 0 to 999,999)
        """
        self.query(f"shakeOnWithRuntime{int(duration)}")
        return
    
    # Temperature methods
    def getTemp40Calibr(self) -> Optional[float]:
        """
        Returns the offset value at the 40°C calibration point

        Returns:
            Optional[float]: offset value at the 40°C calibration point
        """
        response = self.query("getTemp40Calibr", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def getTemp90Calibr(self) -> Optional[float]:
        """
        Returns the offset value at the 90°C calibration point

        Returns:
            Optional[float]: offset value at the 90°C calibration point
        """
        response = self.query("getTemp90Calibr", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def getTempActual(self) -> Optional[float]:
        """
        Returns the current temperature in celsius

        Returns:
            Optional[float]: current temperature in celsius
        """
        response = self.query("getTempActual", numeric=True)
        if response is np.nan:
            return None
        return response
        
    def getTempLimiterMax(self) -> Optional[float]:
        """
        Returns the upper limit for the target temperature in celsius

        Returns:
            Optional[float]: upper limit for the target temperature in celsius
        """
        response = self.query("getTempLimiterMax", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def getTempLimiterMin(self) -> Optional[float]:
        """
        Returns the lower limit for the target temperature in celsius

        Returns:
            Optional[float]: lower limit for the target temperature in celsius
        """
        response = self.query("getTempLimiterMin", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def getTempMax(self) -> Optional[float]:
        """
        Returns the device specific maximum target temperature in celsius (i.e. hardware limits)

        Returns:
            Optional[float]: device specific maximum target temperature in celsius
        """
        response = self.query("getTempMax", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def getTempMin(self) -> Optional[float]:
        """
        Returns the device specific minimum target temperature in celsius (i.e. hardware limits)

        Returns:
            Optional[float]: device specific minimum target temperature in celsius
        """
        response = self.query("getTempMin", numeric=True)
        if response is np.nan:
            return None
        return response
    
    def getTempState(self) -> bool:
        """
        Returns the state of the temperature control feature

        Returns:
            bool: whether temperature control is enabled
        """
        response = self.query("getTempState", numeric=True)
        if response is np.nan:
            return None
        state = bool(int(response)%2)
        return state
    
    def getTempTarget(self) -> Optional[float]:
        """
        Returns the target temperature

        Returns:
            Optional[float]: target temperature
        """
        response = self.query("getTempTarget", numeric=True)
        if response is np.nan:
            return None
        return response
        
    def setTemp40Calibr(self, temperature_calibration_40:float):
        """
        Permanently sets the offset value at the 40°C calibration point in 1/10°C increments

        Args:
            temperature_calibration_40 (float): offset value (between 0°C and 99°C)
        """
        value = int(temperature_calibration_40*10)
        self.query(f"setTemp40Calibr{value}")
        return
    
    def setTemp90Calibr(self, temperature_calibration_90:float):
        """
        Permanently sets the offset value at the 90°C calibration point in 1/10°C increments

        Args:
            temperature_calibration_90 (float): offset value (between 0°C and 99°C)
        """
        value = int(temperature_calibration_90*10)
        self.query(f"setTemp90Calibr{value}")
        return
    
    def setTempLimiterMax(self, temperature_max:float):
        """
        Permanently sets the upper limit for the target temperature in 1/10°C increments

        Args:
            temperature_max (float): upper limit for the target temperature (between -20.0°C and 99.9°C)
        """
        value = int(temperature_max*10)
        self.query(f"setTempLimiterMax{value}")
        return
    
    def setTempLimiterMin(self, temperature_min:float):
        """
        Permanently sets the lower limit for the target temperature in 1/10°C increments

        Args:
            temperature_min (float): lower limit for the target temperature (between -20.0°C and 99.9°C)
        """
        value = int(temperature_min*10)
        self.query(f"setTempLimiterMin{value}")
        return
    
    def setTempTarget(self, temperature:float):
        """
        Sets target temperature between TempMin and TempMax in 1/10°C increments

        Args:
            value (float): target temperature (between TempMin and TempMax)
        """
        value = int(temperature*10)
        self.query(f"setTempTarget{value}")
        return
    
    def tempOff(self):
        """Switches off the temperature control feature and stops heating/cooling"""
        self.query("tempOff")
        return
    
    def tempOn(self):
        """Switches on the temperature control feature and starts heating/cooling"""
        self.query("tempOn")
        return
    
    # ELM (i.e. grip) methods
    def getElmSelftest(self) -> bool:
        """
        Returns whether the ELM self-test is enabled or disabled at device startup

        Returns:
            bool: whether ELM self-test is enabled at device startup
        """
        response = self.query("getElmSelftest", numeric=True)
        if response is np.nan:
            return None
        state = bool(int(response)%2)
        return state
        
    def getElmStartupPosition(self) -> bool:
        """
        Returns whether ELM is unlocked after device startup

        Returns:
            bool: whether ELM is unlocked after device startup
        """
        response = self.query("getElmStartupPosition", numeric=True)
        if response is np.nan:
            return None
        state = bool(int(response)%2)
        return state
    
    def getElmState(self, verbose:bool = True) -> Optional[int]:
        """
        Returns the ELM status
        
        Args:
            verbose (bool, optional): whether to print out state. Defaults to True.
        
        Returns:
            Optional[int]: ELM status as integer
        """
        response = self.query("getElmState", numeric=True)
        if response is np.nan:
            return None
        code = f"es{int(response)}"
        if verbose and code in ELMStateCode._member_names_:
            print(ELMStateCode[code].value)
        return int(response)
    
    def getElmStateAsString(self, verbose:bool = True) -> str:
        """
        Returns the ELM status as a string
        
        Args:
            verbose (bool, optional): whether to print out state. Defaults to True.
        
        Returns:
            Optional[str]: ELM status as string
        """
        response = self.query("getElmStateAsString")
        if verbose and response in ELMStateString._member_names_:
            print(ELMStateString[response].value)
        return response
    
    def setElmLockPos(self, timeout:int = 5):
        """
        Close the ELM
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        response = self.query("setElmLockPos")
        start_time = time.perf_counter()
        while not response:
            if time.perf_counter() - start_time > timeout:
                break
            response = self.read()
        return
    
    def setElmSelftest(self, enable:bool):
        """
        Permanently set whether the ELM self-test is enabled at device startup

        Args:
            enable (bool): whether the ELM self-test is enabled at device startup
        """
        self.query(f"setElmSelftest{int(enable)}")
        return
        
    def setElmStartupPosition(self, unlock:bool):
        """
        Permanently set whether the ELM is unlocked after device startup

        Args:
            unlock (bool): whether the ELM is unlocked after device startup
        """
        self.query(f"setElmStartupPosition{int(unlock)}")
        return
    
    def setElmUnlockPos(self, timeout:int = 5):
        """
        Open the ELM
        
        Note: The ELM should only be opened when the tablar is in the home position.
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        response = self.query("setElmUnlockPos")
        start_time = time.perf_counter()
        while not response:
            if time.perf_counter() - start_time > timeout:
                break
            response = self.read()
        return
    
    # General methods
    def connect(self):
        """Reconnect to device using existing connection details"""
        return self._connect(**self.connection_details)
    
    def disconnect(self):
        """Disconnect from device"""
        try:
            self.device.close()
        except Exception as e:
            if self.verbose:
                print(e)
        self.setFlag(connected=False)
        return
    
    def query(self, 
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
            Union[str, float]: response (string / float)
        """
        start_time = time.perf_counter()
        self.write(command)
        response = ''
        while not response:
            if time.perf_counter() - start_time > timeout_s:
                break
            time.sleep(timeout_s)
            if slow:
                time.sleep(1)
            response = self.read(slow=slow)
        # print(time.perf_counter() - start_time)
        if response.startswith('u ->'):
            raise AttributeError(f'{self.model} does not have the method: {command}')
            print(f'{self.model} does not have the method: {command}')
            if numeric:
                return np.nan
            return ''
        if not numeric:
            return response
        if response.replace('.','',1).replace('-','',1).isdigit():
            value = float(response)
            return value
        print(f"Response value is non-numeric: {repr(response)}")
        return np.nan

    def read(self, slow:bool = False) -> str:
        """
        Read response from device
        
        Args:
            slow (bool, optional): whether to expect a slow response. Defaults to False. 

        Returns:
            str: response string
        """
        response = ''
        try:
            if slow:
                response = self.device.read_all()   # response template: <response><\r><\n>
            else:
                response = self.device.readline()
        except Exception as e:
            if self.verbose:
                print(e)
        else:
            response = response.decode('utf-8').strip()
            if self.verbose and len(response):
                print(response)
        return response
    
    def setFlag(self, **kwargs):
        """
        Set flags by using keyword arguments

        Kwargs:
            key, value: (flag name, boolean) pairs
        """
        if not all([type(v)==bool for v in kwargs.values()]):
            raise ValueError("Ensure all assigned flag values are boolean.")
        self.flags.update(kwargs)
        # for key, value in kwargs.items():
        #     self.flags[key] = value
        return
    
    def write(self, command:str) -> bool:
        """
        Write command to device

        Args:
            command (str): <command code><value>

        Returns:
            bool: whether command was sent successfully
        """
        fstring = f'{command}\r' # command template: <long_form><\r> | <short_form><\r>
        # bstring = bytearray.fromhex(fstring.encode('utf-8').hex())
        if self.verbose:
            print(fstring)
        try:
            # Typical timeout wait is 400ms
            self.device.write(fstring.encode('utf-8'))
        except AttributeError:
            pass
        except Exception as e:
            if self.verbose:
                print(e)
            return False
        return True

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
            self.device = device
        except Exception as e:
            print(f"Could not connect to {port}")
            if self.verbose:
                print(e)
        else:
            print(f"Connection opened to {port}")
            time.sleep(5)
            self.model = self.getDescription()
        return
    