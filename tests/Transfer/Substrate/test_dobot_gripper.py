import pytest
from typing import Sequence

from controllably.Transfer.Substrate import GripperMixin
from controllably.Move.Jointed.Dobot import M1Pro
from controllably.core.connection import match_current_ip_address
from controllably.core.position import Position, Deck

HOST = '192.109.209.21'

class DobotGrip(GripperMixin, M1Pro):    
    def __init__(self, 
        host: str,
        joint_limits: Sequence[Sequence[float]]|None = None,
        right_handed: bool = True, 
        *,
        robot_position: Position = Position(),
        home_waypoints: Sequence[Position] = list(),
        home_position: Position = Position((300,0,240)),                # in terms of robot coordinate system
        tool_offset: Position = Position(),
        calibrated_offset: Position = Position(),
        scale: float = 1.0,
        deck: Deck|None = None,
        safe_height: float|None = 240,                                  # in terms of robot coordinate system
        saved_positions: dict = dict(),                                 # in terms of robot coordinate system
        speed_max: float|None = None,                                   # in mm/min
        movement_buffer: int|None = None,
        movement_timeout: int|None = None,
        gripper_on_delay: int|float = 1,
        gripper_off_delay: int|float = 1,
        verbose: bool = False, 
        simulation: bool = False,
        **kwargs
    ):
        super().__init__(
            host=host, joint_limits=joint_limits, right_handed=right_handed,
            robot_position=robot_position, home_waypoints=home_waypoints, home_position=home_position,
            tool_offset=tool_offset, calibrated_offset=calibrated_offset, scale=scale,
            deck=deck, safe_height=safe_height, saved_positions=saved_positions,
            speed_max=speed_max, movement_buffer=movement_buffer, movement_timeout=movement_timeout,
            verbose=verbose, simulation=simulation,
            **kwargs
        )
        self.gripper_channels = dict(on=20, off=20)
        self.gripper_delays = dict(on=gripper_on_delay, off=gripper_off_delay)
        return
    
    def toggleGrip(self, on:bool):
        channel = self.gripper_channels.get("on" if on else "off", 20)
        return self.device.DOExecute(channel, int(on))

configs = {
    'host': HOST,
    'home_position': [[300,0,240],[-33,0,0]],
    'calibrated_offset': [[-374,496.75,254.2],[-89.11611149,0,0]],
    'scale': 1.0,
    'tool_offset': [[0,0,-232],[122.11611149,0,0]],
    'safe_height': 240,
    'verbose': True,
    'simulation': True,
}

@pytest.fixture(scope="session")
def m1pro_grip():
    mg = DobotGrip(**configs)
    return mg

@pytest.mark.skipif((not match_current_ip_address(HOST)), reason="Requires connection to local lab network")
def test_m1pro_em_grip(m1pro_grip,capsys):
    m1pro_grip.grab(5)
    assert f'Receive from {HOST}:29999: DOExecute(20,1)' in capsys.readouterr().out
    m1pro_grip.drop(5)
    assert f'Receive from {HOST}:29999: DOExecute(20,0)' in capsys.readouterr().out
