# %% -*- coding: utf-8 -*-
"""
This module holds the class for shakers from QInstruments.

Classes:
    BioShakeD30 (Maker)
"""
# Standard library imports
from __future__ import annotations
import numpy as np
from threading import Thread
import time
from typing import Optional

# Third party imports
import serial   # pip install pyserial

# Local application imports
from ....misc import Helper
from ...make_utils import Maker
from .orbital_shaker_lib import ELMStateCode, ELMStateString, ShakeStateCode, ShakeStateString
print(f"Import: OK <{__name__}>")

class BioShake(Maker):
    def __init__(self, port: str, **kwargs):
        super().__init__(**kwargs)
        self._connect(port)
        return
        
    # Initialization methods
    def disableBootScreen(self):
        """Permanent deactivation of the boot screen startup text"""
        self._query("disableBootScreen")
        return
    
    def disableCLED(self):
        """Permanent deactivation of the LED indication lights. The instrument will reset after this command."""
        self._query("disableCLED")
        return
    
    def enableBootScreen(self):
        """Permanent activation of the boot screen startup text"""
        self._query("enableBootScreen")
        return
    
    def enableCLED(self):
        """Permanent activation of the LED indication lights. The instrument will reset after this command."""
        self._query("enableCLED")
        return
    
    def flashLed(self):
        """User device LED flashes five times"""
        self._query("flashLed")
        return

    def getCLED(self) -> Optional[bool]:    # TODO
        """
        Returns the status LED state
        
        Returns:
            Optional[bool]: whether the LED is enabled
        """
        response = self._query_numeric("getCLED")
        if response is np.nan:
            return None
        state = bool(int(response)%2)
        # TODO: add flags
        return state
        
    def getDescription(self) -> str:
        """
        Returns model type
        
        Returns:
            str: model type
        """
        return self._query("getDescription")
        
    def getErrorList(self) -> list[str]:
        """
        Returns a list with errors and warnings which can occur during processing
        
        Returns:
            list[str]: list of errors and warnings
        """
        response = self._query("getErrorList")
        error_list = response[1:-1].split("; ")
        return error_list
        
    def getSerial(self) -> str:
        """
        Returns the device serial number
        
        Returns:
            str: device serial number
        """
        return self._query("getSerial")
        
    def getVersion(self) -> str:
        """
        Returns the firmware version number

        Returns:
            str: firmware version number
        """
        return self._query("getVersion")
        
    def info(self) -> str:
        """
        Returns the boot screen text

        Returns:
            str: boot screen text
        """
        return self._query("info")
        
    def resetDevice(self):  # TODO
        """
        Restarts the controller
        
        Note: This takes about 30 seconds for BS units and 5 for the Q1, CP models
        """
        # TODO: add time.sleep for different models
        self._query("resetDevice")
        return
        
    def setBuzzer(self, duration:int):
        """
        Ring the buzzer for duration in milliseconds

        Args:
            duration (int): duration in milliseconds, from 50 to 999
        """
        if 50 <= duration <= 999:
            self._query(f"setBuzzer{int(duration)}")
        else:
            print("Please input duration of between 50 and 999 milliseconds.")
        return
        
    def version(self) -> str:
        """
        Returns the model type and firmware version number

        Returns:
            str: model type and firmware version number
        """
        return self._query("version")
    
    # ECO methods
    def leaveEcoMode(self):
        """Leaves the economical mode and switches into the normal operating state"""
        self._query("leaveEcoMode")
        return
    
    def setEcoMode(self):
        """
        Switches the shaker into economical mode and reduces electricity consumption.
        
        Note: all commands other than leaveEcoMode will return `e`
        """
        self._query("setEcoMode")
        return
        
    # Shaking methods
    def getShakeAcceleration(self) -> Optional[float]:
        """
        Returns the acceleration/deceleration value

        Returns:
            Optional[float]: acceleration/deceleration value
        """
        response = self._query_numeric("getShakeAcceleration")
        if response is np.nan:
            return None
        return response
        
    def getShakeAccelerationMax(self) -> Optional[int]:
        """
        Get the maximum acceleration/deceleration time in seconds

        Returns:
            Optional[int]: acceleration/deceleration time in seconds
        """
        response = self._query_numeric("getShakeAccelerationMax")
        if response is np.nan:
            return None
        return int(response)
    
    def getShakeAccelerationMin(self) -> Optional[int]:
        """
        Get the minimum acceleration/deceleration time in seconds

        Returns:
            Optional[int]: acceleration/deceleration time in seconds
        """
        response = self._query_numeric("getShakeAccelerationMin")
        if response is np.nan:
            return None
        return int(response)
    
    def getShakeActualSpeed(self) -> Optional[float]:
        """
        Returns the current mixing speed

        Returns:
            Optional[float]: current mixing speed
        """
        response = self._query_numeric("getShakeActualSpeed")
        if response is np.nan:
            return None
        return response
    
    def getShakeDefaultDirection(self) -> Optional[bool]:   # TODO
        """
        Returns the mixing direction when the device starts up

        Returns:
            Optional[bool]: whether mixing direction is counterclockwise
        """
        response = self._query_numeric("getShakeDefaultDirection")
        if response is np.nan:
            return None
        state = bool(int(response)%2)
        # TODO: add flags
        return state
        
    def getShakeDirection(self) -> Optional[bool]:  # TODO
        """
        Returns the current mixing direction

        Returns:
            Optional[bool]: whether mixing direction is counterclockwise
        """
        response = self._query_numeric("getShakeDirection")
        if response is np.nan:
            return None
        state = bool(int(response)%2)
        # TODO: add flags
        return state
        
    def getShakeMaxRpm(self) -> Optional[int]:
        """
        Returns the device specific maximum target speed (i.e. hardware limits)

        Returns:
            Optional[int]: maximum target shake speed
        """
        response = self._query_numeric("getShakeMaxRpm")
        if response is np.nan:
            return None
        return int(response)
    
    def getShakeMinRpm(self) -> Optional[int]:
        """
        Returns the device specific minimum target speed (i.e. hardware limits)

        Returns:
            Optional[int]: minimum target shake speed
        """
        response = self._query_numeric("getShakeMinRpm")
        if response is np.nan:
            return None
        return int(response)
    
    def getShakeRemainingTime(self) -> Optional[int]:
        """
        Returns the remaining time in seconds if device was started with the command `shakeOnWithRuntime`

        Returns:
            Optional[int]: minimum target shake speed
        """
        response = self._query_numeric("getShakeRemainingTime")
        if response is np.nan:
            return None
        return int(response)
    
    def getShakeSpeedLimitMax(self) -> Optional[int]:
        """
        Returns the upper limit for the target speed

        Returns:
            Optional[int]: upper limit for the target speed
        """
        response = self._query_numeric("getShakeSpeedLimitMax")
        if response is np.nan:
            return None
        return int(response)
    
    def getShakeSpeedLimitMin(self) -> Optional[int]:
        """
        Returns the lower limit for the target speed

        Returns:
            Optional[int]: lower limit for the target speed
        """
        response = self._query_numeric("getShakeSpeedLimitMin")
        if response is np.nan:
            return None
        return int(response)
    
    def getShakeState(self) -> Optional[int]:
        """
        Returns shaker state as an integer
        
        Returns:
            Optional[int]: shaker state as integer
        """
        response = self._query_numeric("getShakeState")
        if response is np.nan:
            return None
        code = f"ss{response}"
        if code in ShakeStateCode._member_names_:
            print(ShakeStateCode[code].value)
        return int(response)
        
    def getShakeStateAsString(self) -> str:
        """
        Returns shaker state as a string
        
        Returns:
            Optional[str]: shaker state as string
        """
        response = self._query("getShakeStateAsString")
        code = response.replace("+","t").replace("-","_")
        if code in ShakeStateString._member_names_:
            print(ShakeStateString[code].value)
        return response
        
    def getShakeTargetSpeed(self) -> Optional[float]:
        """
        Returns the target mixing speed

        Returns:
            Optional[float]: target mixing speed
        """
        response = self._query_numeric("getShakeTargetSpeed")
        if response is np.nan:
            return None
        return response
    
    def setShakeAcceleration(self, acceleration:int):
        """
        Sets the acceleration/deceleration value in seconds

        Args:
            value (int): acceleration value
        """
        self._query(f"setShakeAcceleration{int(acceleration)}")
        return
    
    def setShakeDefaultDirection(self, counterclockwise:bool):
        """
        Sets the default mixing direction after device start up

        Args:
            counterclockwise (bool): whether to set default mixing direction to counter clockwise
        """
        self._query(f"setShakeDefaultDirection{int(counterclockwise)}")
        return
    
    def setShakeDirection(self, counterclockwise:bool): # TODO
        """
        Sets the mixing direction

        Args:
            counterclockwise (bool): whether to set mixing direction to counter clockwise
        """
        # TODO: set shake direction
        self._query(f"setShakeDirection{int(counterclockwise)}")
        return
    
    def setShakeSpeedLimitMax(self, speed:int): # TODO
        """
        Set upper limit for the target speed (between 0 to 3000)

        Args:
            speed (int): upper limit for the target speed
        """
        # TODO: set max speed range
        self._query(f"setShakeSpeedLimitMax{int(speed)}")
        return
    
    def setShakeSpeedLimitMin(self, speed:int): # TODO
        """
        Set lower limit for the target speed (between 0 to 3000)
        
        Note: Speed values below 200 RPM are possible, but not recommended

        Args:
            speed (int): lower limit for the target speed
        """
        # TODO: set min speed range
        self._query(f"setShakeSpeedLimitMin{int(speed)}")
        return
        
    def setShakeTargetSpeed(self, speed:int):   #TODO
        """
        Set the target mixing speed
        
        Note: Speed values below 200 RPM are possible, but not recommended

        Args:
            speed (int): target mixing speed
        """
        # TODO: Set speed
        self._query(f"setShakeTargetSpeed{int(speed)}")
        return
        
    def shakeEmergencyOff(self):
        """Stop the shaker immediately at an undefined position ignoring the defined deceleration time"""
        self._query("shakeEmergencyOff")
        return
        
    def shakeGoHome(self):
        """
        Move shaker to the home position and locks in place
        
        Note: Minimum response time is less than 4 sec (internal failure timeout)
        """
        self._query("shakeGoHome")
        return
        
    def shakeOff(self):
        """Stops shaking within the defined deceleration time, go to the home position and locks in place"""
        self._query("shakeOff")
        return
        
    def shakeOffNonZeroPos(self):
        """Stops shaking within the defined deceleration time, do not go to home position and do not lock in home position"""
        self._query("shakeOffNonZeroPos")
        return
        
    def shakeOffWithDeenergizeSoleonid(self):   # FIXME: misspelling of Solenoid
        """
        Stops shaking within the defined deceleration time, go to the home position and locks in place for 1 second, 
        then unlock home position
        """
        self._query("shakeOffWithDeenergizeSoleonid")
        return
        
    def shakeOn(self):
        """Stops shaking within the defined deceleration time, go to the home position and locks in place"""
        self._query("shakeOn")
        return
    
    def shakeOnWithRuntime(self, duration:int):
        """
        Starts shaking with defined speed within defined acceleration time for given time value in seconds

        Args:
            duration (int): shake duration in seconds (from 0 to 999,999)
        """
        self._query(f"shakeOnWithRuntime{int(duration)}")
        return
    
    # Temperature methods
    def getTemp40Calibr(self) -> Optional[float]:
        """
        Returns the offset value at the 40°C calibration point

        Returns:
            Optional[float]: offset value at the 40°C calibration point
        """
        response = self._query_numeric("getTemp40Calibr")
        if response is np.nan:
            return None
        return response
    
    def getTemp90Calibr(self) -> Optional[float]:
        """
        Returns the offset value at the 90°C calibration point

        Returns:
            Optional[float]: offset value at the 90°C calibration point
        """
        response = self._query_numeric("getTemp90Calibr")
        if response is np.nan:
            return None
        return response
    
    def getTempActual(self) -> Optional[float]:
        """
        Returns the current temperature in celsius

        Returns:
            Optional[float]: current temperature in celsius
        """
        response = self._query_numeric("getTempActual")
        if response is np.nan:
            return None
        return response
        
    def getTempLimiterMax(self) -> Optional[float]: # TODO
        """
        Returns the upper limit for the target temperature in celsius

        Returns:
            Optional[float]: upper limit for the target temperature in celsius
        """
        # TODO: set max temp range
        response = self._query_numeric("getTempLimiterMax")
        if response is np.nan:
            return None
        return response
    
    def getTempLimiterMin(self) -> Optional[float]: # TODO
        """
        Returns the lower limit for the target temperature in celsius

        Returns:
            Optional[float]: lower limit for the target temperature in celsius
        """
        # TODO: set min temp range
        response = self._query_numeric("getTempLimiterMin")
        if response is np.nan:
            return None
        return response
    
    def getTempMax(self) -> Optional[float]: # TODO
        """
        Returns the device specific maximum target temperature in celsius (i.e. hardware limits)

        Returns:
            Optional[float]: device specific maximum target temperature in celsius
        """
        # TODO: set max temp range
        response = self._query_numeric("getTempMax")
        if response is np.nan:
            return None
        return response
    
    def getTempMin(self) -> Optional[float]: # TODO
        """
        Returns the device specific minimum target temperature in celsius (i.e. hardware limits)

        Returns:
            Optional[float]: device specific minimum target temperature in celsius
        """
        # TODO: set min temp range
        response = self._query_numeric("getTempMin")
        if response is np.nan:
            return None
        return response
    
    def getTempState(self) -> bool:
        """
        Returns the state of the temperature control feature

        Returns:
            bool: whether temperature control is enabled
        """
        response = self._query_numeric("getTempState")
        if response is np.nan:
            return None
        state = bool(int(response)%2)
        # TODO: add flags
        return state
    
    def getTempTarget(self) -> Optional[float]: # TODO
        """
        Returns the target temperature

        Returns:
            Optional[float]: target temperature
        """
        # TODO: set temp target
        response = self._query_numeric("getTempTarget")
        if response is np.nan:
            return None
        return response
        
    def setTemp40Calibr(self, value:float):
        """
        Sets the offset value at the 40°C calibration point in 1/10°C increments

        Args:
            value (float): offset value (between 0°C and 99°C)
        """
        value = int(value*10)
        self._query(f"setTemp40Calibr{value}")
        return
    
    def setTemp90Calibr(self, value:float):
        """
        Sets the offset value at the 90°C calibration point in 1/10°C increments

        Args:
            value (float): offset value (between 0°C and 99°C)
        """
        value = int(value*10)
        self._query(f"setTemp90Calibr{value}")
        return
    
    def setTempLimiterMax(self, value:float):
        """
        Sets the upper limit for the target temperature in 1/10°C increments

        Args:
            value (float): upper limit for the target temperature (between -20.0°C and 99.9°C)
        """
        value = int(value*10)
        self._query(f"setTempLimiterMax{value}")
        return
    
    def setTempLimiterMin(self, value:float):
        """
        Sets the lower limit for the target temperature in 1/10°C increments

        Args:
            value (float): lower limit for the target temperature (between -20.0°C and 99.9°C)
        """
        value = int(value*10)
        self._query(f"setTempLimiterMin{value}")
        return
    
    def setTempTarget(self, value:float):
        """
        Sets target temperature between TempMin and TempMax in 1/10°C increments

        Args:
            value (float): target temperature (between TempMin and TempMax)
        """
        value = int(value*10)
        self._query(f"setTempTarget{value}")
        return
    
    def tempOff(self):
        """Switches off the temperature control feature and stops heating/cooling"""
        self._query("tempOff")
        return
    
    def tempOn(self):
        """Switches on the temperature control feature and stops heating/cooling"""
        self._query("tempOn")
        return
    
    # ELM (i.e. grip) methods
    def getElmSelftest(self) -> bool:
        """
        Returns whether the ELM self-test is enabled or disabled at device startup

        Returns:
            bool: whether ELM self-test is enabled at device startup
        """
        response = self._query_numeric("getElmSelftest")
        if response is np.nan:
            return None
        state = bool(int(response)%2)
        # TODO: add flags
        return state
        
    def getElmStartupPosition(self) -> bool:
        """
        Returns whether ELM is unlocked after device startup

        Returns:
            bool: whether ELM is unlocked after device startup
        """
        response = self._query_numeric("getElmStartupPosition")
        if response is np.nan:
            return None
        state = bool(int(response)%2)
        # TODO: add flags
        return state
    
    def getElmState(self) -> Optional[int]:
        """
        Returns the ELM status
        
        Returns:
            Optional[int]: ELM status as integer
        """
        response = self._query_numeric("getElmState")
        if response is np.nan:
            return None
        code = f"es{response}"
        if code in ELMStateCode._member_names_:
            print(ELMStateCode[code].value)
        return int(response)
    
    def getElmStateAsString(self) -> str:
        """
        Returns the ELM status as a string
        
        Returns:
            Optional[str]: ELM status as string
        """
        response = self._query("getShakeStateAsString")
        if response in ELMStateString._member_names_:
            print(ELMStateString[response].value)
        return response
    
    def setElmLockPos(self):
        """Close the ELM"""
        self._query("setElmLockPos")
        return
    
    def setElmSelftest(self, value:bool):
        """
        Set whether the ELM self-test is enabled at device startup

        Args:
            value (bool): whether the ELM self-test is enabled at device startup
        """
        self._query(f"setElmSelftest{int(value)}")
        return
        
    def setElmStartupPosition(self, value:bool):
        """
        Set whether the ELM is unlocked after device startup

        Args:
            value (bool): whether the ELM is unlocked after device startup
        """
        self._query(f"setElmStartupPosition{int(value)}")
        return
    
    def setElmUnlockPos(self):
        """
        Open the ELM
        
        Note: The ELM should only be opened when the tablar is in the home position.
        """
        self._query("setElmUnlockPos")
        return
    
    # General methods
    def shutdown(self):
        return super().shutdown()

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
            time.sleep(5)
        self.device = device
        return
    
    def _query(self, command: str, timeout_s: float = 0.3) -> str:
        """
        Write command to and read response from device

        Args:
            command (str): command string
            timeout_s (float, optional): duration to wait before timeout. Defaults to 0.3.
        Returns:
            str: response string
        """
        # command_code = command[:2]
        # if command_code not in STATUS_QUERIES:
        #     if self.flags['get_feedback'] and not self.flags['pause_feedback']:
        #         self.setFlag(pause_feedback=True)
        #         time.sleep(timeout_s)
        #     # self.getStatus()
        #     # while self.isBusy():
        #     #     self.getStatus()
        #     if self.isBusy():
        #         time.sleep(timeout_s)
        
        # start_time = time.perf_counter()
        # self._write(command)
        # response = ''
        # while not self._is_expected_reply(response, command_code):
        #     if time.perf_counter() - start_time > timeout_s:
        #         break
        #     response = self._read()
        # # print(time.perf_counter() - start_time)
        # if command_code in QUERIES:
        #     response = response[2:]
        # if command_code not in STATUS_QUERIES:
        #     if get_position:
        #         self.getPosition()
        #     if resume_feedback:
        #         self.setFlag(pause_feedback=False)
        # return response
        return

    def _query_numeric(self, command: str, timeout_s: float = 0.3) -> float:
        """
        Write command to and read response from device

        Args:
            command (str): command string
            timeout_s (float, optional): duration to wait before timeout. Defaults to 0.3.
        Returns:
            float: numeric response
        """
        response = self._query(command=command, timeout_s=timeout_s)
        if response.isnumeric():
            value = float(response)
            return value
        print("Response value is non-numeric.")
        return np.nan

    def _read(self) -> str:
        """
        Read response from device

        Returns:
            str: response string
        """
        response = ''
        try:
            response = self.device.readline()   # response template: <long_form><\r><\n>
        except Exception as e:
            if self.verbose:
                print(e)
        else:
            response = response.decode('utf-8').strip()
            if self.verbose:
                print(response)
        return response
    
    def _write(self, command:str) -> bool:
        """
        Write command to device

        Args:
            command (str): <command code><value>

        Returns:
            bool: whether command was sent successfully
        """
        if self.verbose:
            print(command)
        fstring = f'{command}\r' # command template: <long_form><\r> | <short_form><\r>
        # bstring = bytearray.fromhex(fstring.encode('utf-8').hex())
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
