# %%
import pytest
import logging
import time
from typing import Sequence

import numpy as np
from scipy.spatial.transform import Rotation

from controllably.Transfer.Substrate import GripperMixin
from controllably.Compound.VacuumMover import VacuumGantry
from controllably.core.connection import get_ports
from controllably.core.position import Position

PORT = 'COM9'
DEGREE_000 = 10
DEGREE_090 = 121
DEGREE_180 = 243

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class GantryGrip(GripperMixin, VacuumGantry):
    def __init__(self, 
        port: str,
        limits: Sequence[Sequence[float]] = ((0,0,0),(0,0,0)),          # in terms of robot coordinate system
        vacuum_on_delay: float = 3,
        vacuum_off_delay: float = 3,
        **kwargs
    ):
        super().__init__(
            port=port, limits=limits, 
            vacuum_on_delay=vacuum_on_delay, vacuum_off_delay=vacuum_off_delay,
            **kwargs
        )
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
        logger.info(f"Homed | axis={axis}")
        return True
    
    def rotateBy(self,
        by: Sequence[float]|Rotation|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        robot: bool = False
    ) -> Rotation:
        assert isinstance(by, (Sequence, Rotation, np.ndarray)), f"Ensure `by` is a Sequence or Rotation or np.ndarray object"
        if isinstance(by, (Sequence, np.ndarray)):
            assert len(by) == 3, f"Ensure `by` is a 3-element sequence for c,b,a"
        rotate_by = by if isinstance(by, Rotation) else Rotation.from_euler('zyx', by, degrees=True)
        logger.debug(f"Rotating by {rotate_by} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        rotate_by = rotate_by               # not affected by robot or tool coordinates for rotation
        
        # Implementation of relative rotation
        assert self.robot_position.z >= self.safe_height, f"Ensure robot is above safe height before rotating"
        current_orientation = self.robot_position.Rotation if robot else self.worktool_position.Rotation
        new_orientation = rotate_by * current_orientation
        return self.rotateTo(new_orientation, speed_factor=speed_factor, jog=jog, robot=robot)

    def rotateTo(self,
        to: Sequence[float]|Rotation|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        robot: bool = False
    ) -> Rotation:
        assert isinstance(to, (Sequence, Rotation, np.ndarray)), f"Ensure `to` is a Sequence or Rotation or np.ndarray object"
        if isinstance(to, (Sequence, np.ndarray)):
            assert len(to) == 3, f"Ensure `to` is a 3-element sequence for c,b,a"
        rotate_to = to if isinstance(to, Rotation) else Rotation.from_euler('zyx', to, degrees=True)
        logger.debug(f"Rotating to {rotate_to} at speed factor {speed_factor}")
        
        # Convert to robot coordinates
        if robot:
            rotate_to = rotate_to
        else:
            rotate_to = self.tool_offset.invert().Rotation * self.calibrated_offset.invert().Rotation * rotate_to
        
        # Implementation of absolute rotation
        assert self.robot_position.z >= self.safe_height, f"Ensure robot is above safe height before rotating"
        c_angle = rotate_to.as_euler('zyx', degrees=True)[0]
        assert (-180 <= c_angle <= 0), f"Ensure c angle is between -180 and 0 degrees"
        fixed_angles = {0: DEGREE_000, -90: DEGREE_090, -180: DEGREE_180}
        if c_angle in fixed_angles:
            value = fixed_angles[c_angle]
        elif 0 > c_angle > -90:
            value = (0+c_angle)/(0+90) * (DEGREE_090 - DEGREE_000)
        elif -90 > c_angle > -180:
            value = (-90+c_angle)/(-90+180) * (DEGREE_180 - DEGREE_090)
        self.device.query(f'M3 S{value}', wait=True)
        
        # Update position
        self.updateRobotPosition(to=rotate_to)
        return self.robot_position.Rotation if robot else self.worktool_position.Rotation
    
    def toggleGrip(self, on: bool):
        return self.evacuate() if on else self.vent()
    
    def toggleVacuum(self, on: bool):
        return self.toggleCoolantValve(on=on)

configs = {
    'port': PORT,
    'limits': [[0,-280,-240],[830,0,0]],
    'calibrated_offset': [[-50.0,404.76,237],[0,0,0]],
    'safe_height': -5,
    'verbose':  True
}

@pytest.fixture(scope="session")
def gantry_grip():
    gg = GantryGrip(port=PORT)
    return gg


@pytest.mark.skipif((PORT not in get_ports()), reason="Requires serial connection to device")
def test_gantry_grip(gantry_grip):
    ...
    
# %%
if __name__ == "__main__":
    gg = GantryGrip(**configs)
    gg.home()
    gg.moveBy((10,-10,-10))
    gg.grab()
    gg.moveToSafeHeight()
    gg.rotateTo((-90,0,0))
    gg.drop()
    gg.home()

# %%
