import pytest
from typing import Sequence

from controllably.Make.Vacuum import VacuumMixin
from controllably.Move.Jointed.Dobot import M1Pro
from controllably.core.connection import match_current_ip_address
from controllably.core.position import Position, Deck

IP_ADDRESS = '127.0.0.1'

class DobotVacuum(VacuumMixin, M1Pro):    
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
        self.gripper_channels = dict(on=2, off=1)
        self.gripper_delays = dict(on=gripper_on_delay, off=gripper_off_delay)
        return
    
    def toggleVacuum(self, on:bool):
        channel = self.gripper_channels.get("on" if on else "off", 2)
        return self.device.DOExecute(channel, int(on))


@pytest.fixture(scope="session")
def m1pro_vacuum():
    mv = DobotVacuum(host=IP_ADDRESS)
    return mv


@pytest.mark.skipif((not match_current_ip_address(IP_ADDRESS)), reason="Requires connection to local lab network")
def test_m1pro_vacuum(m1pro_vacuum):
    ...
