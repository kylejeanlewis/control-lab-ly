import pytest
import time
from typing import Sequence

from controllably.Transfer.Substrate import GripperMixin
from controllably.Make.Vacuum import VacuumMixin
from controllably.Move.Cartesian import Gantry
from controllably.core.connection import get_ports
from controllably.core.position import Position, Deck

PORT = 'COM3'

class GantryGrip(VacuumMixin, GripperMixin, Gantry):
    def __init__(self, 
        port: str,
        limits: Sequence[Sequence[float]] = ((0,0,0),(0,0,0)),          # in terms of robot coordinate system
        *, 
        robot_position: Position = Position(),
        home_position: Position = Position(),                           # in terms of robot coordinate system
        tool_offset: Position = Position(),
        calibrated_offset: Position = Position(),
        scale: float = 1.0,
        deck: Deck|None = None,
        safe_height: float|None = None,                                 # in terms of robot coordinate system
        speed_max: float|None = None,                                   # in mm/min
        device_type_name: str = 'GRBL',
        baudrate: int = 115200, 
        movement_buffer: int|None = None,
        movement_timeout: int|None = None,
        vacuum_on_delay: float = 3,
        vacuum_off_delay: float = 3,
        verbose: bool = False, 
        simulation: bool = False,
        **kwargs
    ):
        super().__init__(
            port=port, baudrate=baudrate, limits=limits,
            robot_position=robot_position, home_position=home_position,
            tool_offset=tool_offset, calibrated_offset=calibrated_offset, scale=scale, 
            deck=deck, safe_height=safe_height, speed_max=speed_max, 
            device_type_name=device_type_name, movement_buffer=movement_buffer, 
            movement_timeout=movement_timeout, verbose=verbose, simulation=simulation,
            message_end='\r\n',
            **kwargs
        )
        self.vacuum_delays = dict(on=vacuum_on_delay, off=vacuum_off_delay)
        return
    
    def home(self, axis: str|None = None, *, timeout:int|None = None) -> bool:  # TODO: implement state file / saving in case of unexpected power outage
        timeout = self.movement_timeout if timeout is None else timeout
        order = ('Z', 'X', 'Y')
        if axis is not None:
            order = (axis,)
        for axis in order:
            success = self.device.home(axis=axis, timeout=timeout)
            if not success:
                return False
            xyz = [(coord if axis.upper()!=ax else 0) for coord,ax in zip(self.robot_position.coordinates,'XYZ')]
            print(xyz)
            self.updateRobotPosition(to=Position(xyz))
        self.rotateTo(self.home_position.Rotation)
        time.sleep(self.movement_buffer)
        self.updateRobotPosition(to=self.home_position)
        # logger.info(f"Homed | axis={axis}")
        return True
    
    def toggleGrip(self, on: bool):
        return self.evacuate(self.vacuum_delays.get('on',3)) if on else self.vent(self.vacuum_delays.get('off',3))
    
    def toggleVacuum(self, on: bool):
        return self.toggleCoolantValve(on=on)


@pytest.fixture(scope="session")
def gantry_grip():
    gg = GantryGrip(port=PORT)
    return gg

 
@pytest.mark.skipif((PORT not in get_ports()), reason="Requires serial connection to device")
def test_gantry_grip(gantry_grip):
    ...