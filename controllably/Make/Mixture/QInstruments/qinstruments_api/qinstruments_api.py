# -*- coding: utf-8 -*-
"""
QInstruments API for controlling hardware from QInstruments.
Refer to manual for more information on the GRBL firmware.
    
## Classes:
    `QInstrumentsDevice`: provides an interface for available actions to control devices from QInstruments
    
<i>Documentation last updated: 2024-11-16</i>
"""
# Standard library imports
from __future__ import annotations
from copy import deepcopy
import logging
import time
from types import SimpleNamespace
from typing import Any, NamedTuple

# Third party imports
import serial       # pip install pyserial

# Local application imports
from .....core.device import SerialDevice
from .qinstruments_lib import ELMStateCode, ELMStateString, ShakeStateCode, ShakeStateString

logger = logging.getLogger("controllably.Make")
logger.debug(f"Import: OK <{__name__}>")

READ_FORMAT = "{data}\r\n"
WRITE_FORMAT = "{data}\r"
Data = NamedTuple("Data", [("data", str)])
BoolData = NamedTuple("BoolData", [("data", bool)])
FloatData = NamedTuple("FloatData", [("data", float)])
IntData = NamedTuple("IntData", [("data", int)])

class _QInstrumentsDevice(SerialDevice):
    """
    QInstrumentsDevice provides an interface for available actions to control devices from QInstruments, including orbital shakers,
    heat plates, and cold plates.
    
    ### Constructor
        `port` (str|None, optional): serial port for the device. Defaults to None.
        `baudrate` (int, optional): baudrate for the device. Defaults to 9600.
        `timeout` (int, optional): timeout for the device. Defaults to 1.
        `init_timeout` (int, optional): timeout for initialization. Defaults to 5.
        `message_end` (str, optional): message end character. Defaults to '\\r'.
        `simulation` (bool, optional): whether to simulate the device. Defaults to False.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes and properties
        `port` (str): device serial port
        `baudrate` (int): device baudrate
        `timeout` (int): device timeout
        `connection_details` (dict): connection details for the device
        `serial` (serial.Serial): serial object for the device
        `init_timeout` (int): timeout for initialization
        `message_end` (str): message end character
        `model` (str): device model
        `flags` (SimpleNamespace[str, bool]): flags for the device
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
    
    ### Methods

    #### General
        `clear`: clear the input and output buffers
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `query`: query the device (i.e. write and read data)
        `read`: read data from the device
        `write`: write data to the device
    
    #### Initialization
        `disableBootScreen`: permanent deactivation of the boot screen startup text
        `disableCLED`: permanent deactivation of the LED indication lights
        `enableBootScreen`: permanent activation of the boot screen startup text
        `enableCLED`: permanent activation of the LED indication lights
        `flashLed`: user device LED flashes five times
        `getCLED`: returns the status LED state
        `getDescription`: returns model type
        `getErrorList`: returns a list with errors and warnings which can occur during processing
        `getSerial`: returns the device serial number
        `getVersion`: returns the firmware version number
        `info`: retrieve the boot screen text
        `resetDevice`: restarts the controller
        `setBuzzer`: ring the buzzer for duration in milliseconds
        `version`: returns the model type and firmware version number
    
    #### ECO
        `leaveEcoMode`: leaves the economical mode and switches into the normal operating state
        `setEcoMode`: witches the shaker into economical mode and reduces electricity consumption
    
    #### Shaking
        `getShakeAcceleration`: returns the acceleration/deceleration value
        `getShakeAccelerationMax`: get the maximum acceleration/deceleration time in seconds
        `getShakeAccelerationMin`: get the minimum acceleration/deceleration time in seconds
        `getShakeActualSpeed`: returns the current mixing speed
        `getShakeDefaultDirection`: returns the mixing direction when the device starts up
        `getShakeDirection`: returns the current mixing direction
        `getShakeMaxRpm`: returns the device specific maximum target speed (i.e. hardware limits)
        `getShakeMinRpm`: returns the device specific minimum target speed (i.e. hardware limits)
        `getShakeRemainingTime`: returns the remaining time in seconds if device was started with the command `shakeOnWithRuntime`
        `getShakeSpeedLimitMax`: returns the upper limit for the target speed
        `getShakeSpeedLimitMin`: returns the lower limit for the target speed
        `getShakeState`: returns shaker state as an integer
        `getShakeStateAsString`: returns shaker state as a string
        `getShakeTargetSpeed`: returns the target mixing speed
        `setShakeAcceleration`: sets the acceleration/deceleration value in seconds
        `setShakeDefaultDirection`: permanently sets the default mixing direction after device start up
        `setShakeDirection`: sets the mixing direction
        `setShakeSpeedLimitMax`: permanently set upper limit for the target speed (between 0 to 3000)
        `setShakeSpeedLimitMin`: permanently set lower limit for the target speed (between 0 to 3000)
        `setShakeTargetSpeed`: set the target mixing speed
        `shakeEmergencyOff`: stop the shaker immediately at an undefined position ignoring the defined deceleration time
        `shakeGoHome`: move shaker to the home position and locks in place
        `shakeOff`: stops shaking within the defined deceleration time, go to the home position and locks in place
        `shakeOffNonZeroPos`: tops shaking within the defined deceleration time, do not go to home position and do not lock in home position
        `shakeOffWithDeEnergizeSolenoid`: tops shaking within the defined deceleration time, go to the home position and locks in place for 1 second, then unlock home position
        `shakeOn`: tarts shaking with defined speed with defined acceleration time
        `shakeOnWithRuntime`: starts shaking with defined speed within defined acceleration time for given time value in seconds
    
    #### Temperature
        `getTemp40Calibr`: returns the offset value at the 40°C calibration point
        `getTemp90Calibr`: returns the offset value at the 90°C calibration point
        `getTempActual`: returns the current temperature in celsius
        `getTempLimiterMax`: returns the upper limit for the target temperature in celsius
        `getTempLimiterMin`: returns the lower limit for the target temperature in celsius
        `getTempMax`: returns the device specific maximum target temperature in celsius (i.e. hardware limits)
        `getTempMin`: returns the device specific minimum target temperature in celsius (i.e. hardware limits)
        `getTempState`: returns the state of the temperature control feature
        `getTempTarget`: returns the target temperature
        `setTemp40Calibr`: permanently sets the offset value at the 40°C calibration point in 1/10°C increments
        `setTemp90Calibr`: permanently sets the offset value at the 90°C calibration point in 1/10°C increments
        `setTempLimiterMax`: permanently sets the upper limit for the target temperature in 1/10°C increments
        `setTempLimiterMin`: permanently sets the lower limit for the target temperature in 1/10°C increments
        `setTempTarget`: sets target temperature between TempMin and TempMax in 1/10°C increments
        `tempOff`: switches off the temperature control feature and stops heating/cooling
        `tempOn`: switches on the temperature control feature and starts heating/cooling
    
    #### ELM
        `getElmSelftest`: returns whether the ELM self-test is enabled or disabled at device startup
        `getElmStartupPosition`: returns whether ELM is unlocked after device startup
        `getElmState`: returns the ELM status
        `getElmStateAsString`: returns the ELM status as a string
        `setElmLockPos`: close the ELM
        `setElmSelftest`: permanently set whether the ELM self-test is enabled at device startup
        `setElmStartupPosition`: permanently set whether the ELM is unlocked after device startup
        `setElmUnlockPos`: open the ELM
    """
    
    _default_flags: SimpleNamespace = SimpleNamespace(verbose=False, connected=False, simulation=False)
    def __init__(self,
        port: str|None = None, 
        baudrate: int = 9600, 
        timeout: int = 1, 
        *,
        init_timeout:int = 5, 
        data_type: NamedTuple = NamedTuple("Data", [("data", str)]),
        read_format:str = "{data}\r\n",
        write_format:str = "{data}\r",
        simulation:bool = False, 
        verbose:bool = False,
        **kwargs
    ):
        """
        Initialize QInstrumentsDevice class

        Args:
            port (str|None, optional): serial port for the device. Defaults to None.
            baudrate (int, optional): baudrate for the device. Defaults to 9600.
            timeout (int, optional): timeout for the device. Defaults to 1.
            init_timeout (int, optional): timeout for initialization. Defaults to 5.
            message_end (str, optional): message end character. Defaults to '\\r'.
            simulation (bool, optional): whether to simulate the device. Defaults to False.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        super().__init__(
            port=port, baudrate=baudrate, timeout=timeout,
            init_timeout=init_timeout, simulation=simulation, verbose=verbose, 
            data_type=data_type, read_format=read_format, write_format=write_format, **kwargs
        )
        self._logger = logger.getChild(f"{self.__class__.__name__}_{id(self)}")
        self._logger.addHandler(logging.StreamHandler())
        self.verbose = verbose
        
        self.model = ''
        self.serial_number = ''
        return
    
    # General methods
    def connect(self):
        super().connect()
        self.model = self.getDescription()
        self.serial_number = self.getSerial()
        return
    
    def query(self, 
            data: Any, 
            multi_out: bool = True,
            *,
            timeout: int|float = 0.3,
            format_in: str|None = None, 
            format_out: str|None = None,
            data_type: NamedTuple|None = None,
            timestamp: bool = False
        ) -> Any:
        """
        Query the device (i.e. write and read data)

        Args:
            data (Any): data to query
            lines (bool, optional): whether to read multiple lines. Defaults to False.
            numeric(bool, optional): whether to expect a numeric response. Defaults to False.
            timeout_s (float, optional): duration to wait before timeout. Defaults to 0.3.
        
        Returns:
            str|float|None: response (string / float)
        """
        data_type: NamedTuple = data_type or Data
        out = super().query(
            data, multi_out=multi_out, timeout=timeout,
            format_in=format_in, timestamp=timestamp
        )
        if timestamp:
            out,now = out
        out: Data|None = out
        response = out.data
        if response.startswith('u ->'):
            error_message = f"{self.model} received an invalid command: {data!r}"
            self._logger.error(error_message)
            raise AttributeError(error_message)
        
        if self.flags.simulation:
            data_out = data_type('') if data_type.__annotations__['data'] == str else data_type(0)
        else:
            data_out = self.processOutput(out.data, format=format_out, data_type=data_type)
        return (data_out, now) if timestamp else data_out

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

    def getCLED(self) -> bool|None:
        """
        Returns the status LED state
        
        Returns:
            bool|None: whether the LED is enabled
        """
        out: BoolData = self.query("getCLED", data_type=BoolData)
        return out.data
        
    def getDescription(self) -> str:
        """
        Returns model type
        
        Returns:
            str: model type
        """
        return self.query("getDescription", multi_out=True)
        
    def getErrorList(self) -> list[str]:
        """
        Returns a list with errors and warnings which can occur during processing
        
        Returns:
            list[str]: list of errors and warnings
        """
        response = self.query("getErrorList", multi_out=True)
        error_list = response[1:-1].split("; ")
        return error_list
        
    def getSerial(self) -> str:
        """
        Returns the device serial number
        
        Returns:
            str: device serial number
        """
        return self.query("getSerial", multi_out=True)
        
    def getVersion(self) -> str:
        """
        Returns the firmware version number

        Returns:
            str: firmware version number
        """
        return self.query("getVersion", multi_out=True)
        
    def info(self):
        """Retrieve the boot screen text"""
        return self.query("info", multi_out=True)
        
    def resetDevice(self, timeout:int = 30):
        """
        Restarts the controller
        
        Note: This takes about 30 seconds for BS units and 5 for the Q1, CP models
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 30.
        """
        self.query("resetDevice")
        start_time = time.perf_counter()
        while self.getShakeState() != 3:
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
            self._logger.warning("Please input duration of between 50 and 999 milliseconds.")
        return
        
    def version(self) -> str:
        """
        Returns the model type and firmware version number

        Returns:
            str: model type and firmware version number
        """
        return self.query("version", multi_out=True)
    
    # ECO methods
    def leaveEcoMode(self, timeout:int = 5):
        """
        Leaves the economical mode and switches into the normal operating state
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        self.query("leaveEcoMode")
        start_time = time.perf_counter()
        while self.getShakeState() != 3:
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
        self.query("setEcoMode", timeout=timeout)
        return
        
    # Shaking methods
    def getShakeAcceleration(self) -> float|None:
        """
        Returns the acceleration/deceleration value

        Returns:
            float|None: acceleration/deceleration value
        """
        out: FloatData = self.query("getShakeAcceleration", data_type=FloatData)
        return out.data
        
    def getShakeAccelerationMax(self) -> float|None:
        """
        Get the maximum acceleration/deceleration time in seconds

        Returns:
            float|None: acceleration/deceleration time in seconds
        """
        out: FloatData = self.query("getShakeAccelerationMax", data_type=FloatData)
        return out.data
    
    def getShakeAccelerationMin(self) -> float|None:
        """
        Get the minimum acceleration/deceleration time in seconds

        Returns:
            float|None: acceleration/deceleration time in seconds
        """
        out: FloatData = self.query("getShakeAccelerationMin", data_type=FloatData)
        return out.data
    
    def getShakeActualSpeed(self) -> float|None:
        """
        Returns the current mixing speed

        Returns:
            float|None: current mixing speed
        """
        out: FloatData = self.query("getShakeActualSpeed", data_type=FloatData)
        return out.data
    
    def getShakeDefaultDirection(self) -> bool|None:
        """
        Returns the mixing direction when the device starts up

        Returns:
            bool|None: whether mixing direction is counterclockwise
        """
        out: BoolData = self.query("getShakeDefaultDirection", data_type=BoolData)
        return out.data
        
    def getShakeDirection(self) -> bool|None:
        """
        Returns the current mixing direction

        Returns:
            bool|None: whether mixing direction is counterclockwise
        """
        out: BoolData = self.query("getShakeDirection", data_type=BoolData)
        return out.data
        
    def getShakeMaxRpm(self) -> float|None:
        """
        Returns the device specific maximum target speed (i.e. hardware limits)

        Returns:
            float|None: maximum target shake speed
        """
        out: FloatData = self.query("getShakeMaxRpm", data_type=FloatData)
        return out.data
    
    def getShakeMinRpm(self) -> float|None:
        """
        Returns the device specific minimum target speed (i.e. hardware limits)

        Returns:
            float|None: minimum target shake speed
        """
        out: FloatData = self.query("getShakeMinRpm", data_type=FloatData)
        return out.data
    
    def getShakeRemainingTime(self) -> float|None:
        """
        Returns the remaining time in seconds if device was started with the command `shakeOnWithRuntime`

        Returns:
            float|None: minimum target shake speed
        """
        out: FloatData = self.query("getShakeRemainingTime", data_type=FloatData)
        return out.data
    
    def getShakeSpeedLimitMax(self) -> float|None:
        """
        Returns the upper limit for the target speed

        Returns:
            float|None: upper limit for the target speed
        """
        out: FloatData = self.query("getShakeSpeedLimitMax", data_type=FloatData)
        return out.data
    
    def getShakeSpeedLimitMin(self) -> float|None:
        """
        Returns the lower limit for the target speed

        Returns:
            float|None: lower limit for the target speed
        """
        out: FloatData = self.query("getShakeSpeedLimitMin", data_type=FloatData)
        return out.data
    
    def getShakeState(self) -> int|None:
        """
        Returns shaker state as an integer
        
        Returns:
            int|None: shaker state as integer
        """
        out: IntData = self.query("getShakeState", data_type=IntData)
        code = f"ss{out.data}"
        if code in ShakeStateCode._member_names_:
            self._logger.info(ShakeStateCode[code].value)
        return out.data
        
    def getShakeStateAsString(self) -> str|None:
        """
        Returns shaker state as a string
        
        Returns:
            str|None: shaker state as string
        """
        out: Data = self.query("getShakeStateAsString")
        code = out.data.replace("+","t").replace("-","_")
        if code in ShakeStateString._member_names_:
            self._logger.info(ShakeStateString[code].value)
        return out.data
        
    def getShakeTargetSpeed(self) -> float|None:
        """
        Returns the target mixing speed

        Returns:
            float|None: target mixing speed
        """
        out: FloatData = self.query("getShakeTargetSpeed", data_type=FloatData)
        return out.data
    
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
        while self.getShakeState() != 3:
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
    def getTemp40Calibr(self) -> float|None:
        """
        Returns the offset value at the 40°C calibration point

        Returns:
            float|None: offset value at the 40°C calibration point
        """
        out: FloatData = self.query("getTemp40Calibr", data_type=FloatData)
        return out.data
    
    def getTemp90Calibr(self) -> float|None:
        """
        Returns the offset value at the 90°C calibration point

        Returns:
            float|None: offset value at the 90°C calibration point
        """
        out: FloatData = self.query("getTemp90Calibr", data_type=FloatData)
        return out.data
    
    def getTempActual(self) -> float|None:
        """
        Returns the current temperature in celsius

        Returns:
            float|None: current temperature in celsius
        """
        out: FloatData = self.query("getTempActual", data_type=FloatData)
        return out.data
        
    def getTempLimiterMax(self) -> float|None:
        """
        Returns the upper limit for the target temperature in celsius

        Returns:
            float|None: upper limit for the target temperature in celsius
        """
        out: FloatData = self.query("getTempLimiterMax", data_type=FloatData)
        return out.data
    
    def getTempLimiterMin(self) -> float|None:
        """
        Returns the lower limit for the target temperature in celsius

        Returns:
            float|None: lower limit for the target temperature in celsius
        """
        out: FloatData = self.query("getTempLimiterMin", data_type=FloatData)
        return out.data
    
    def getTempMax(self) -> float|None:
        """
        Returns the device specific maximum target temperature in celsius (i.e. hardware limits)

        Returns:
            float|None: device specific maximum target temperature in celsius
        """
        out: FloatData = self.query("getTempMax", data_type=FloatData)
        return out.data
    
    def getTempMin(self) -> float|None:
        """
        Returns the device specific minimum target temperature in celsius (i.e. hardware limits)

        Returns:
            float|None: device specific minimum target temperature in celsius
        """
        out: FloatData = self.query("getTempMin", data_type=FloatData)
        return out.data
    
    def getTempState(self) -> bool:
        """
        Returns the state of the temperature control feature

        Returns:
            bool: whether temperature control is enabled
        """
        out: BoolData = self.query("getTempState", data_type=BoolData)
        return out.data
    
    def getTempTarget(self) -> float|None:
        """
        Returns the target temperature

        Returns:
            float|None: target temperature
        """
        out: FloatData = self.query("getTempTarget", data_type=FloatData)
        return out.data
        
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
        out: BoolData = self.query("getElmSelftest", data_type=BoolData)
        return out.data
        
    def getElmStartupPosition(self) -> bool:
        """
        Returns whether ELM is unlocked after device startup

        Returns:
            bool: whether ELM is unlocked after device startup
        """
        out: BoolData = self.query("getElmStartupPosition", data_type=BoolData)
        return out.data
    
    def getElmState(self) -> int|None:
        """
        Returns the ELM status
        
        Returns:
            int|None: ELM status as integer
        """
        out: IntData = self.query("getElmState", data_type=IntData)
        code = f"es{out.data}"
        if code in ELMStateCode._member_names_:
            self._logger.info(ELMStateCode[code].value)
        return out.data
    
    def getElmStateAsString(self) -> str|None:
        """
        Returns the ELM status as a string
        
        Returns:
            str|None: ELM status as string
        """
        out: Data = self.query("getElmStateAsString")
        if out.data in ELMStateString._member_names_:
            self._logger.info(ELMStateString[out.data].value)
        return out.data
    
    def setElmLockPos(self, timeout:int = 5):
        """
        Close the ELM
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        self.query("setElmLockPos", timeout=timeout)
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
        self.query("setElmUnlockPos", timeout=timeout)
        return
 

class QInstrumentsDevice:
    """
    QInstrumentsDevice provides an interface for available actions to control devices from QInstruments, including orbital shakers,
    heat plates, and cold plates.
    
    ### Constructor
        `port` (str|None, optional): serial port for the device. Defaults to None.
        `baudrate` (int, optional): baudrate for the device. Defaults to 9600.
        `timeout` (int, optional): timeout for the device. Defaults to 1.
        `init_timeout` (int, optional): timeout for initialization. Defaults to 5.
        `message_end` (str, optional): message end character. Defaults to '\\r'.
        `simulation` (bool, optional): whether to simulate the device. Defaults to False.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes and properties
        `port` (str): device serial port
        `baudrate` (int): device baudrate
        `timeout` (int): device timeout
        `connection_details` (dict): connection details for the device
        `serial` (serial.Serial): serial object for the device
        `init_timeout` (int): timeout for initialization
        `message_end` (str): message end character
        `model` (str): device model
        `flags` (SimpleNamespace[str, bool]): flags for the device
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
    
    ### Methods

    #### General
        `clear`: clear the input and output buffers
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `query`: query the device (i.e. write and read data)
        `read`: read data from the device
        `write`: write data to the device
    
    #### Initialization
        `disableBootScreen`: permanent deactivation of the boot screen startup text
        `disableCLED`: permanent deactivation of the LED indication lights
        `enableBootScreen`: permanent activation of the boot screen startup text
        `enableCLED`: permanent activation of the LED indication lights
        `flashLed`: user device LED flashes five times
        `getCLED`: returns the status LED state
        `getDescription`: returns model type
        `getErrorList`: returns a list with errors and warnings which can occur during processing
        `getSerial`: returns the device serial number
        `getVersion`: returns the firmware version number
        `info`: retrieve the boot screen text
        `resetDevice`: restarts the controller
        `setBuzzer`: ring the buzzer for duration in milliseconds
        `version`: returns the model type and firmware version number
    
    #### ECO
        `leaveEcoMode`: leaves the economical mode and switches into the normal operating state
        `setEcoMode`: witches the shaker into economical mode and reduces electricity consumption
    
    #### Shaking
        `getShakeAcceleration`: returns the acceleration/deceleration value
        `getShakeAccelerationMax`: get the maximum acceleration/deceleration time in seconds
        `getShakeAccelerationMin`: get the minimum acceleration/deceleration time in seconds
        `getShakeActualSpeed`: returns the current mixing speed
        `getShakeDefaultDirection`: returns the mixing direction when the device starts up
        `getShakeDirection`: returns the current mixing direction
        `getShakeMaxRpm`: returns the device specific maximum target speed (i.e. hardware limits)
        `getShakeMinRpm`: returns the device specific minimum target speed (i.e. hardware limits)
        `getShakeRemainingTime`: returns the remaining time in seconds if device was started with the command `shakeOnWithRuntime`
        `getShakeSpeedLimitMax`: returns the upper limit for the target speed
        `getShakeSpeedLimitMin`: returns the lower limit for the target speed
        `getShakeState`: returns shaker state as an integer
        `getShakeStateAsString`: returns shaker state as a string
        `getShakeTargetSpeed`: returns the target mixing speed
        `setShakeAcceleration`: sets the acceleration/deceleration value in seconds
        `setShakeDefaultDirection`: permanently sets the default mixing direction after device start up
        `setShakeDirection`: sets the mixing direction
        `setShakeSpeedLimitMax`: permanently set upper limit for the target speed (between 0 to 3000)
        `setShakeSpeedLimitMin`: permanently set lower limit for the target speed (between 0 to 3000)
        `setShakeTargetSpeed`: set the target mixing speed
        `shakeEmergencyOff`: stop the shaker immediately at an undefined position ignoring the defined deceleration time
        `shakeGoHome`: move shaker to the home position and locks in place
        `shakeOff`: stops shaking within the defined deceleration time, go to the home position and locks in place
        `shakeOffNonZeroPos`: tops shaking within the defined deceleration time, do not go to home position and do not lock in home position
        `shakeOffWithDeEnergizeSolenoid`: tops shaking within the defined deceleration time, go to the home position and locks in place for 1 second, then unlock home position
        `shakeOn`: tarts shaking with defined speed with defined acceleration time
        `shakeOnWithRuntime`: starts shaking with defined speed within defined acceleration time for given time value in seconds
    
    #### Temperature
        `getTemp40Calibr`: returns the offset value at the 40°C calibration point
        `getTemp90Calibr`: returns the offset value at the 90°C calibration point
        `getTempActual`: returns the current temperature in celsius
        `getTempLimiterMax`: returns the upper limit for the target temperature in celsius
        `getTempLimiterMin`: returns the lower limit for the target temperature in celsius
        `getTempMax`: returns the device specific maximum target temperature in celsius (i.e. hardware limits)
        `getTempMin`: returns the device specific minimum target temperature in celsius (i.e. hardware limits)
        `getTempState`: returns the state of the temperature control feature
        `getTempTarget`: returns the target temperature
        `setTemp40Calibr`: permanently sets the offset value at the 40°C calibration point in 1/10°C increments
        `setTemp90Calibr`: permanently sets the offset value at the 90°C calibration point in 1/10°C increments
        `setTempLimiterMax`: permanently sets the upper limit for the target temperature in 1/10°C increments
        `setTempLimiterMin`: permanently sets the lower limit for the target temperature in 1/10°C increments
        `setTempTarget`: sets target temperature between TempMin and TempMax in 1/10°C increments
        `tempOff`: switches off the temperature control feature and stops heating/cooling
        `tempOn`: switches on the temperature control feature and starts heating/cooling
    
    #### ELM
        `getElmSelftest`: returns whether the ELM self-test is enabled or disabled at device startup
        `getElmStartupPosition`: returns whether ELM is unlocked after device startup
        `getElmState`: returns the ELM status
        `getElmStateAsString`: returns the ELM status as a string
        `setElmLockPos`: close the ELM
        `setElmSelftest`: permanently set whether the ELM self-test is enabled at device startup
        `setElmStartupPosition`: permanently set whether the ELM is unlocked after device startup
        `setElmUnlockPos`: open the ELM
    """
    
    _default_flags: SimpleNamespace = SimpleNamespace(verbose=False, connected=False, simulation=False)
    def __init__(self,
        port: str|None = None, 
        baudrate: int = 9600, 
        timeout: int = 1, 
        *,
        init_timeout: int = 5,
        message_end: str = '\r',
        simulation: bool = False,
        verbose: bool = False,
        **kwargs
    ):
        """
        Initialize QInstrumentsDevice class

        Args:
            port (str|None, optional): serial port for the device. Defaults to None.
            baudrate (int, optional): baudrate for the device. Defaults to 9600.
            timeout (int, optional): timeout for the device. Defaults to 1.
            init_timeout (int, optional): timeout for initialization. Defaults to 5.
            message_end (str, optional): message end character. Defaults to '\\r'.
            simulation (bool, optional): whether to simulate the device. Defaults to False.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self._port = ''
        self._baudrate = 0
        self._timeout = 0
        self.init_timeout = init_timeout
        self.message_end = message_end
        self.flags = deepcopy(self._default_flags)
        
        self.serial = serial.Serial()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        
        self.flags.simulation = simulation
        
        self._logger = logger.getChild(f"{self.__class__.__name__}_{id(self)}")
        self._logger.addHandler(logging.StreamHandler())
        self.verbose = verbose
        
        self.model = ''
        return
    
    @property
    def port(self) -> str:
        """Device serial port"""
        return self._port
    @port.setter
    def port(self, value:str):
        self._port = value
        self.serial.port = value
        return
    
    @property
    def baudrate(self) -> int:
        """Device baudrate"""
        return self._baudrate
    @baudrate.setter
    def baudrate(self, value:int):
        assert isinstance(value, int), "Ensure baudrate is an integer"
        assert value in serial.Serial.BAUDRATES, f"Ensure baudrate is one of the standard values: {serial.Serial.BAUDRATES}"
        self._baudrate = value
        self.serial.baudrate = value
        return
    
    @property
    def timeout(self) -> int:
        """Device timeout"""
        return self._timeout
    @timeout.setter
    def timeout(self, value:int):
        self._timeout = value
        self.serial.timeout = value
        return
    
    @property
    def connection_details(self) -> dict:
        """Connection details for the device"""
        return {
            'port': self.port,
            'baudrate': self.baudrate,
            'timeout': self.timeout
        }
    
    @property
    def is_connected(self) -> bool:
        """Whether the device is connected"""
        connected = self.flags.connected if self.flags.simulation else self.serial.is_open
        return connected
    
    @property
    def verbose(self) -> bool:
        """Verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        level = logging.DEBUG if value else logging.INFO
        for handler in self._logger.handlers:
            if not isinstance(handler, logging.StreamHandler):
                continue
            handler.setLevel(level)
        return
    
    # General methods
    def clear(self):
        """Clear the input and output buffers"""
        if self.flags.simulation:
            return
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        return

    def connect(self):
        """Connect to the device"""
        if self.is_connected:
            return
        try:
            self.serial.open()
        except serial.SerialException as e:
            self._logger.error(f"Failed to connect to {self.port} at {self.baudrate} baud")
            self._logger.debug(e)
        else:
            self._logger.info(f"Connected to {self.port} at {self.baudrate} baud")
            time.sleep(self.init_timeout)
        self.model = self.getDescription()
        self.flags.connected = True
        return

    def disconnect(self):
        """Disconnect from the device"""
        if not self.is_connected:
            return
        try:
            self.serial.close()
        except serial.SerialException as e:
            self._logger.error(f"Failed to disconnect from {self.port}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Disconnected from {self.port}")
        self.flags.connected = False
        return
    
    def query(self, 
            data: Any, 
            lines: bool = False, 
            *,
            numeric: bool = False, 
            timeout_s: float = 0.3
        ) -> Any:
        """
        Query the device (i.e. write and read data)

        Args:
            data (Any): data to query
            lines (bool, optional): whether to read multiple lines. Defaults to False.
            numeric(bool, optional): whether to expect a numeric response. Defaults to False.
            timeout_s (float, optional): duration to wait before timeout. Defaults to 0.3.
        
        Returns:
            str|float|None: response (string / float)
        """
        start_time = time.perf_counter()
        try:    # NOTE: temporary for transition to new SerialDevice
            data = self.processInput(data)
        except:
            pass
        self.write(str(data))
        response = ''
        while not response:
            if time.perf_counter() - start_time > timeout_s:
                break
            time.sleep(timeout_s + int(lines))
            try:    # NOTE: temporary for transition to new SerialDevice
                response = self.readAll() if lines else self.read()
            except:
                response = self.read(lines=lines)
        if response.startswith('u ->'):
            error_message = f"{self.model} received an invalid command: {data!r}"
            self._logger.error(error_message)
            raise AttributeError(error_message)
        if self.flags.simulation:
            response = '0' if numeric else ''
        try:
            return response if not numeric else float(response)
        except ValueError:
            self._logger.warning(f"Unable to parse response to numeric: {response!r}")
        return response
    
    def read(self, lines:bool = False) -> str:
        """
        Read data from the device
        
        Args:
            lines (bool, optional): whether to read multiple lines. Defaults to False.

        Returns:
            str|list[str]: line(s) of data read from the device
        """
        data = ''
        try:
            if lines:
                data = self.serial.read_all()       # response template: <response><\r><\n>
                data = data.decode("utf-8", "replace").strip() 
            else:
                data = self.serial.readline().decode("utf-8", "replace").strip()
            self._logger.debug(f"Received: {data!r}")
            self.serial.reset_output_buffer()
        except serial.SerialException as e:
            self._logger.debug(f"Failed to receive data")
        return data

    def write(self, data:str) -> bool:
        """
        Write data to the device

        Args:
            data (str): data to write
        
        Returns:
            bool: whether the write was successful
        """
        assert isinstance(data, str), "Ensure data is a string"
        data = f"{data}{self.message_end}" if not data.endswith(self.message_end) else data
        try:
            self.serial.write(data.encode())
            self._logger.debug(f"Sent: {data!r}")
        except serial.SerialException as e:
            self._logger.debug(f"Failed to send: {data!r}")
            return False
        return True

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

    def getCLED(self) -> bool|None:
        """
        Returns the status LED state
        
        Returns:
            bool|None: whether the LED is enabled
        """
        response = self.query("getCLED", numeric=True)
        if response is None or response == '':
            return None
        state = bool(int(response)%2)
        return state
        
    def getDescription(self) -> str:
        """
        Returns model type
        
        Returns:
            str: model type
        """
        return self.query("getDescription", lines=True)
        
    def getErrorList(self) -> list[str]:
        """
        Returns a list with errors and warnings which can occur during processing
        
        Returns:
            list[str]: list of errors and warnings
        """
        response = self.query("getErrorList", lines=True)
        error_list = response[1:-1].split("; ")
        return error_list
        
    def getSerial(self) -> str:
        """
        Returns the device serial number
        
        Returns:
            str: device serial number
        """
        return self.query("getSerial", lines=True)
        
    def getVersion(self) -> str:
        """
        Returns the firmware version number

        Returns:
            str: firmware version number
        """
        return self.query("getVersion", lines=True)
        
    def info(self):
        """Retrieve the boot screen text"""
        return self.query("info", lines=True)
        
    def resetDevice(self, timeout:int = 30):
        """
        Restarts the controller
        
        Note: This takes about 30 seconds for BS units and 5 for the Q1, CP models
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 30.
        """
        self.query("resetDevice")
        start_time = time.perf_counter()
        while self.getShakeState() != 3:
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
            self._logger.warning("Please input duration of between 50 and 999 milliseconds.")
        return
        
    def version(self) -> str:
        """
        Returns the model type and firmware version number

        Returns:
            str: model type and firmware version number
        """
        return self.query("version", lines=True)
    
    # ECO methods
    def leaveEcoMode(self, timeout:int = 5):
        """
        Leaves the economical mode and switches into the normal operating state
        
        Args:
            timeout (int, optional): number of seconds to wait before aborting. Defaults to 5.
        """
        self.query("leaveEcoMode")
        start_time = time.perf_counter()
        while self.getShakeState() != 3:
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
            response = self.read()#[0]
        return
        
    # Shaking methods
    def getShakeAcceleration(self) -> float|None:
        """
        Returns the acceleration/deceleration value

        Returns:
            float|None: acceleration/deceleration value
        """
        response = self.query("getShakeAcceleration", numeric=True)
        if response is None or response == '':
            return None
        return response
        
    def getShakeAccelerationMax(self) -> float|None:
        """
        Get the maximum acceleration/deceleration time in seconds

        Returns:
            float|None: acceleration/deceleration time in seconds
        """
        response = self.query("getShakeAccelerationMax", numeric=True)
        if response is None or response == '':
            return None
        return response
    
    def getShakeAccelerationMin(self) -> float|None:
        """
        Get the minimum acceleration/deceleration time in seconds

        Returns:
            float|None: acceleration/deceleration time in seconds
        """
        response = self.query("getShakeAccelerationMin", numeric=True)
        if response is None or response == '':
            return None
        return response
    
    def getShakeActualSpeed(self) -> float|None:
        """
        Returns the current mixing speed

        Returns:
            float|None: current mixing speed
        """
        response = self.query("getShakeActualSpeed", numeric=True)
        if response is None or response == '':
            return None
        return response
    
    def getShakeDefaultDirection(self) -> bool|None:
        """
        Returns the mixing direction when the device starts up

        Returns:
            bool|None: whether mixing direction is counterclockwise
        """
        response = self.query("getShakeDefaultDirection", numeric=True)
        if response is None or response == '':
            return None
        state = bool(int(response)%2)
        return state
        
    def getShakeDirection(self) -> bool|None:
        """
        Returns the current mixing direction

        Returns:
            bool|None: whether mixing direction is counterclockwise
        """
        response = self.query("getShakeDirection", numeric=True)
        if response is None or response == '':
            return None
        state = bool(int(response)%2)
        return state
        
    def getShakeMaxRpm(self) -> float|None:
        """
        Returns the device specific maximum target speed (i.e. hardware limits)

        Returns:
            float|None: maximum target shake speed
        """
        response = self.query("getShakeMaxRpm", numeric=True)
        if response is None or response == '':
            return None
        return response
    
    def getShakeMinRpm(self) -> float|None:
        """
        Returns the device specific minimum target speed (i.e. hardware limits)

        Returns:
            float|None: minimum target shake speed
        """
        response = self.query("getShakeMinRpm", numeric=True)
        if response is None or response == '':
            return None
        return response
    
    def getShakeRemainingTime(self) -> float|None:
        """
        Returns the remaining time in seconds if device was started with the command `shakeOnWithRuntime`

        Returns:
            float|None: minimum target shake speed
        """
        response = self.query("getShakeRemainingTime", numeric=True)
        if response is None or response == '':
            return None
        return response
    
    def getShakeSpeedLimitMax(self) -> float|None:
        """
        Returns the upper limit for the target speed

        Returns:
            float|None: upper limit for the target speed
        """
        response = self.query("getShakeSpeedLimitMax", numeric=True)
        if response is None or response == '':
            return None
        return response
    
    def getShakeSpeedLimitMin(self) -> float|None:
        """
        Returns the lower limit for the target speed

        Returns:
            float|None: lower limit for the target speed
        """
        response = self.query("getShakeSpeedLimitMin", numeric=True)
        if response is None or response == '':
            return None
        return response
    
    def getShakeState(self) -> int|None:
        """
        Returns shaker state as an integer
        
        Returns:
            int|None: shaker state as integer
        """
        response = self.query("getShakeState", numeric=True)
        if response is None or response == '':
            return None
        code = f"ss{int(response)}"
        if code in ShakeStateCode._member_names_:
            self._logger.info(ShakeStateCode[code].value)
        return int(response)
        
    def getShakeStateAsString(self) -> str|None:
        """
        Returns shaker state as a string
        
        Returns:
            str|None: shaker state as string
        """
        response = self.query("getShakeStateAsString")
        code = response.replace("+","t").replace("-","_")
        if code in ShakeStateString._member_names_:
            self._logger.info(ShakeStateString[code].value)
        return response
        
    def getShakeTargetSpeed(self) -> float|None:
        """
        Returns the target mixing speed

        Returns:
            float|None: target mixing speed
        """
        response = self.query("getShakeTargetSpeed", numeric=True)
        if response is None or response == '':
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
        while self.getShakeState() != 3:
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
    def getTemp40Calibr(self) -> float|None:
        """
        Returns the offset value at the 40°C calibration point

        Returns:
            float|None: offset value at the 40°C calibration point
        """
        response = self.query("getTemp40Calibr", numeric=True)
        if response is None or response == '':
            return None
        return response
    
    def getTemp90Calibr(self) -> float|None:
        """
        Returns the offset value at the 90°C calibration point

        Returns:
            float|None: offset value at the 90°C calibration point
        """
        response = self.query("getTemp90Calibr", numeric=True)
        if response is None or response == '':
            return None
        return response
    
    def getTempActual(self) -> float|None:
        """
        Returns the current temperature in celsius

        Returns:
            float|None: current temperature in celsius
        """
        response = self.query("getTempActual", numeric=True)
        if response is None or response == '':
            return None
        return response
        
    def getTempLimiterMax(self) -> float|None:
        """
        Returns the upper limit for the target temperature in celsius

        Returns:
            float|None: upper limit for the target temperature in celsius
        """
        response = self.query("getTempLimiterMax", numeric=True)
        if response is None or response == '':
            return None
        return response
    
    def getTempLimiterMin(self) -> float|None:
        """
        Returns the lower limit for the target temperature in celsius

        Returns:
            float|None: lower limit for the target temperature in celsius
        """
        response = self.query("getTempLimiterMin", numeric=True)
        if response is None or response == '':
            return None
        return response
    
    def getTempMax(self) -> float|None:
        """
        Returns the device specific maximum target temperature in celsius (i.e. hardware limits)

        Returns:
            float|None: device specific maximum target temperature in celsius
        """
        response = self.query("getTempMax", numeric=True)
        if response is None or response == '':
            return None
        return response
    
    def getTempMin(self) -> float|None:
        """
        Returns the device specific minimum target temperature in celsius (i.e. hardware limits)

        Returns:
            float|None: device specific minimum target temperature in celsius
        """
        response = self.query("getTempMin", numeric=True)
        if response is None or response == '':
            return None
        return response
    
    def getTempState(self) -> bool:
        """
        Returns the state of the temperature control feature

        Returns:
            bool: whether temperature control is enabled
        """
        response = self.query("getTempState", numeric=True)
        if response is None or response == '':
            return None
        state = bool(int(response)%2)
        return state
    
    def getTempTarget(self) -> float|None:
        """
        Returns the target temperature

        Returns:
            float|None: target temperature
        """
        response = self.query("getTempTarget", numeric=True)
        if response is None or response == '':
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
        if response is None or response == '':
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
        if response is None or response == '':
            return None
        state = bool(int(response)%2)
        return state
    
    def getElmState(self) -> int|None:
        """
        Returns the ELM status
        
        Returns:
            int|None: ELM status as integer
        """
        response = self.query("getElmState", numeric=True)
        if response is None or response == '':
            return None
        code = f"es{int(response)}"
        if code in ELMStateCode._member_names_:
            self._logger.info(ELMStateCode[code].value)
        return int(response)
    
    def getElmStateAsString(self) -> str|None:
        """
        Returns the ELM status as a string
        
        Returns:
            str|None: ELM status as string
        """
        response = self.query("getElmStateAsString")
        if response in ELMStateString._member_names_:
            self._logger.info(ELMStateString[response].value)
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
            response = self.read()#[0]
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
            response = self.read()#[0]
        return
    