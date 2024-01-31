# %% -*- coding: utf-8 -*-
"""
This module holds the class for movement tools based on Primitiv. (Grbl firmware)

Classes:
    Grbl (Gantry)
    Primitiv (Grbl)
"""
# Standard library imports
from __future__ import annotations
import numpy as np
import time
from typing import Optional

# Local application imports
from ...misc import Helper
from .cartesian_utils import Gantry
from .grbl_lib import AlarmCode, ErrorCode, SettingCode
print(f"Import: OK <{__name__}>")

class Grbl(Gantry):
    """
    Grbl provides controls for the platforms using the Grbl firmware

    ### Constructor
    Args:
        `port` (str): COM port address
        `limits` (tuple[tuple[float]], optional): lower and upper limits of gantry. Defaults to ((-410,-290,-120), (0,0,0)).
        `safe_height` (float, optional): height at which obstacles can be avoided. Defaults to -80.
    
    ### Methods
    - `getAcceleration`: get maximum acceleration rates (mm/s^2)
    - `getCoordinates`: get current coordinates from device
    - `getMaxSpeeds`:  get maximum speeds (mm/s)
    - `getSettings`: get hardware settings
    - `getStatus`: get the current status of the tool
    - `home`: make the robot go home
    - `stop`: stop movement immediately
    """
    
    _default_flags = {'busy': False, 'connected': False, 'jog':False}
    def __init__(self, 
        port: str, 
        limits: tuple[tuple[float]] = ((-410,-290,-120), (0,0,0)), 
        safe_height: float = -80, 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            port (str): COM port address
            limits (tuple[tuple[float]], optional): lower and upper limits of gantry. Defaults to ((-410,-290,-120), (0,0,0)).
            safe_height (float, optional): height at which obstacles can be avoided. Defaults to -80.
        """
        super().__init__(port=port, limits=limits, safe_height=safe_height, **kwargs)
        return
    
    def getAcceleration(self) -> np.ndarray:
        """
        Get maximum acceleration rates (mm/s^2)

        Returns:
            np.ndarray: acceleration rates
        """
        settings = self.getSettings()
        relevant = [s for s in settings if '$12' in s][-3:]
        accels = [s.split('=')[1] for s in relevant]
        xyz_max_accels = [float(a) for a in accels]
        self._accel_max = {k:v for k,v in zip(('x','y','z'), xyz_max_accels)}
        return self.max_accels
    
    def getCoordinates(self) -> np.ndarray:
        """
        Get current coordinates from device

        Returns:
            np.ndarray: current device coordinates
        """
        status = self.getStatus()
        relevant = [s for s in status if 'MPos' in s][-1]
        positions = relevant.split(":")[1].split(",")
        return np.array([float(p) for p in positions])
    
    def getMaxSpeeds(self) -> np.ndarray:
        """
        Get maximum speeds (mm/s)

        Returns:
            np.ndarray: maximum speeds
        """
        settings = self.getSettings()
        relevant = [s for s in settings if '$11' in s][-3:]
        speeds_str_list = [s.split('=')[1] for s in relevant]        # mm/min
        xyz_max_speeds = [float(s)/60 for s in speeds_str_list]
        self._speed_max = {k:v for k,v in zip(('x','y','z'), xyz_max_speeds)}
        super().getMaxSpeeds()
        return self.max_speeds
    
    def getSettings(self) -> list[str]:
        """
        Get hardware settings

        Returns:
            list[str]: hardware settings
        """
        responses = self._query("$$\n")
        parsed_responses = responses.copy()
        for s,setting in enumerate(responses):
            command = setting.split('=')[0]
            code = command[1:]
            if f'sc{code}' in SettingCode._member_names_:
                parsed_responses[s] = setting.replace(command, f'[{command}] ' + eval(f'SettingCode.sc{code}.value.message'))
        if self.verbose:
            for r in parsed_responses:
                print(r)
        return responses
    
    def getStatus(self) -> list[str]:
        """
        Get the current status of the tool

        Returns:
            list[str]: status output
        """
        responses = self._query('?\n')
        print(responses)
        for r in responses:
            if '<' in r and '>' in r:
                status_string = r.strip()
                return status_string[1:-1].split('|')
        return ['busy']
    
    @Helper.safety_measures
    def home(self) -> bool:
        """Make the robot go home"""
        self._query("$H\n")
        self.coordinates = self.home_coordinates
        print("Homed")
        return True

    @Helper.safety_measures
    def moveTo(self, coordinates:tuple[float], tool_offset:bool = True, jog:bool = False, **kwargs) -> bool:
        """
        Move the robot to target position

        Args:
            coordinates (tuple[float]): x,y,z coordinates to move to
            tool_offset (bool, optional): whether to consider tooltip offset. Defaults to True.

        Returns:
            bool: whether movement is successful
        """
        self.setFlag(jog=jog)
        ret = super().moveTo(coordinates=coordinates, tool_offset=tool_offset, **kwargs)
        self.setFlag(jog=False)
        return ret
    
    def setSpeedFactor(self, speed_factor: float) -> tuple[bool, float]:
        """
        Set the speed fraction of the robot

        Args:
            speed_factor (float): speed fraction between 0 and 1
        
        Returns:
            tuple[bool, float]: whether speed has changed; prevailing speed fraction
        """
        if speed_factor == self.speed_factor or speed_factor is None:
            return False, self.speed_factor
        if speed_factor < 0 or speed_factor > 1:
            return False, self.speed_factor
        prevailing_speed_factor = self.speed_factor
        ret,_ = self.setSpeed(self.max_feedrate * speed_factor)
        if ret:
            self._speed_factor = speed_factor
        return ret, prevailing_speed_factor
    
    def stop(self):
        """Halt all movement and print current coordinates"""
        self._query("!")
        self._query("$X")
        self._query("~")
        self._query("F10800")
        self.coordinates = self.getCoordinates()
        return

    # Protected method(s)
    def _connect(self, port:str, baudrate:int = 115200, timeout:Optional[int] = 0.1):
        """
        Connection procedure for tool

        Args:
            port (str): COM port address
            baudrate (int, optional): baudrate. Defaults to 115200.
            timeout (Optional[int], optional): timeout in seconds. Defaults to 0.1.
        """
        super()._connect(port, baudrate, timeout)
        try:
            self.device.close()
        except Exception as e:
            if self.verbose:
                print(e)
        else:
            self.device.open()
            # Start grbl 
            self._write("\r\n\r\n")
            time.sleep(2)
            self.device.reset_input_buffer()
            self._query("$X")
            self._query('F10800')
        return
    
    def _query(self, command: str) -> list[str]:
        """
        Write command to and read response from device

        Args:
            command (str): command string to send to device

        Returns:
            list[str]: list of response string(s) from device
        """
        if command.startswith("G1") and self.flags.get('jog',False):
            # axes = ('x','y','z','a','b','c')
            move = command.strip().split("G1 ")[1]
            # axis = move[0].lower()
            command = f"$J= {move} F{int(60*self.speed)}"
        return super()._query(command)

    # def _handle_alarms_and_errors(self, response:str):
    #     """
    #     Handle the alarms and errors arising from the tool
        
    #     Args:
    #         response (str): string response from the tool
    #     """
    #     if 'reset' in response.lower():
    #         self.reset()
    #         self.home()
            
    #     if 'ALARM' not in response and 'error' not in response:
    #         return
    #     code_int = response.strip().split(":")[1]
    #     code_int = int(code_int) if code_int.isnumeric() else code_int
        
    #     # Alarms
    #     if 'ALARM' in response:
    #         code = f'ac{code_int:02}'
    #         if code_int in (1,3,8,9):
    #             self.home()
    #         if code in AlarmCode._member_names_:
    #             print(AlarmCode[code].value)
        
    #     # Errors
    #     if 'error' in response:
    #         code = f'er{code_int:02}'
    #         if code in ErrorCode._member_names_:
    #             print(ErrorCode[code].value)
    #     return


class Primitiv(Grbl):
    """
    Primitiv provides controls for the Primitv platform

    ### Constructor
    Args:
        `port` (str): COM port address
        `limits` (tuple[tuple[float]], optional): lower and upper limits of gantry. Defaults to ((-410,-290,-120), (0,0,0)).
        `safe_height` (float, optional): height at which obstacles can be avoided. Defaults to -80.
    
    ### Methods
    - `getSettings`: get hardware settings
    - `getStatus`: get the current status of the tool
    - `home`: make the robot go home
    - `stop`: stop movement immediately
    """
    
    def __init__(self, 
        port: str, 
        limits: tuple[tuple[float]] = ((-410, -290, -120), (0, 0, 0)), 
        safe_height: float = -80, 
        **kwargs
    ):
        super().__init__(port, limits, safe_height, **kwargs)
        