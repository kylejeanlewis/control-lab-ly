# Standard library imports
from __future__ import annotations
import time
from typing import Sequence

# Local application imports
from ...core.position import Position, Deck
from ...Make.Heat import HeaterMixin
from .cartesian import Gantry

class Ender(Gantry, HeaterMixin):
    """
    
    """
    
    def __init__(self, 
        port: str,
        limits: Sequence[Sequence[float]] = ((0, 0, 0), (0, 0, 0)),     # in terms of robot coordinate system
        *, 
        robot_position: Position = Position(),
        home_position: Position = Position(),                           # in terms of robot coordinate system
        tool_offset: Position = Position(),
        calibrated_offset: Position = Position(),
        scale: float = 1.0,
        deck: Deck|None = None,
        safe_height: float|None = None,                                 # in terms of robot coordinate system
        saved_positions: dict|None = None,                                 # in terms of robot coordinate system
        speed_max: float|None = None,                                   # in mm/min
        device_type_name: str = 'Marlin',
        baudrate: int = 115200, 
        movement_buffer: int|None = None,
        movement_timeout: int|None = None,
        verbose: bool = False, 
        simulation: bool = False,
        **kwargs
    ):
        """ 
        Initialize Gantry class
        
        Args:
            port (str): serial port address
            limits (Sequence[Sequence[float]], optional): lower and upper limits of gantry, in terms of robot coordinate system. Defaults to ((0, 0, 0), (0, 0, 0)).
            robot_position (Position, optional): current position of the robot. Defaults to Position().
            home_position (Position, optional): home position of the robot in terms of robot coordinate system. Defaults to Position().
            tool_offset (Position, optional): tool offset from robot to end effector. Defaults to Position().
            calibrated_offset (Position, optional): calibrated offset from robot to work position. Defaults to Position().
            scale (float, optional): factor to scale the basis vectors by. Defaults to 1.0.
            deck (Deck, optional): Deck object for workspace. Defaults to None.
            safe_height (float, optional): safe height in terms of robot coordinate system. Defaults to None.
            saved_positions (dict, optional): dictionary of saved positions. Defaults to dict().
            speed_max (float, optional): maximum speed of robot in mm/min. Defaults to None.
            device_type_name (str, optional): name of the device type. Defaults to 'GRBL'.
            baudrate (int, optional): baudrate. Defaults to 115200.
            movement_buffer (Optional[int], optional): buffer for movement. Defaults to None.
            movement_timeout (Optional[int], optional): timeout for movement. Defaults to None.
            verbose (bool, optional): verbosity of class. Defaults to False.
            simulation (bool, optional): whether to simulate. Defaults to False.
        """
        saved_positions = saved_positions or dict()
        super().__init__(
            port=port, baudrate=baudrate, limits = limits,
            robot_position=robot_position, home_position=home_position,
            tool_offset=tool_offset, calibrated_offset=calibrated_offset, scale=scale, 
            deck=deck, safe_height=safe_height, saved_positions=saved_positions,
            speed_max=speed_max, device_type_name=device_type_name, movement_buffer=movement_buffer, 
            movement_timeout=movement_timeout, verbose=verbose, simulation=simulation,
            **kwargs
        )
        return
    
    def getTemperature(self):
        data,_ = self.device.query("M105")
        try:
            temperatures = [r for r in data if '@' in r]
        except Exception as e:
            raise e
        else:
            bed_temperatures = temperatures[-1].split(':')[2].split(' ')[:2]
            temperature, set_temperature = bed_temperatures
        return temperature
    
    def _set_temperature(self, temperature):
        self.device.query(f"M190 S{temperature}")
        time.sleep(1)
        return