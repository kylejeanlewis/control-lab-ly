import pytest
import logging
from types import SimpleNamespace
from typing import Sequence

import numpy as np

from controllably.Compound.VacuumMover import VacuumGantry
from controllably.core.connection import get_ports
from controllably.core.position import Position

PORT = 'COM9'
LOADING_POSITION = (-118,0,0)
CLOSING_WAYPOINTS = ((-3,0,0),(-3,-27,0))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
   
class VacuumChamber(VacuumGantry):
    _default_flags = SimpleNamespace(busy=False, verbose=False, vented=True, closed=False)
    def __init__(self, 
        port: str,
        limits: Sequence[Sequence[float]] = ((0,0,0),(0,0,0)),          # in terms of robot coordinate system
        loading_position:Sequence[int|float]|np.ndarray|None = None,
        closing_waypoints:Sequence[Sequence[int|float]]|np.ndarray|None = None,
        **kwargs
    ):
        super().__init__(
            port=port, limits=limits, **kwargs
        )
        loading_position = loading_position if loading_position is not None else LOADING_POSITION
        closing_waypoints = closing_waypoints if closing_waypoints is not None else CLOSING_WAYPOINTS
        self.loading_position = Position(loading_position)
        self.closing_waypoints = [Position(wp) for wp in closing_waypoints]
        return
    
    # VacuumMixin methods
    def evacuate(self):
        if not self.flags.closed:
            logger.warning("Please close the chamber before evacuating.")
            return
        super().evacuate()
        self.flags.vented = False
        return

    # Movement methods
    def home(self):
        """Make the robot go home"""
        if not self.flags.vented:
            self.vent()
        super().home()
        self.flags.closed = False
        return 
    
    def moveBy(self,
        by: Sequence[float]|Position|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        rapid: bool = False,
        robot: bool = False
    ) -> Position:
        if self.flags.closed:
            logger.warning("Please home before moving.")
            return
        return super().moveBy(by, speed_factor=speed_factor, jog=jog, rapid=rapid, robot=robot)
    
    def moveTo(self,
        to: Sequence[float]|Position|np.ndarray,
        speed_factor: float|None = None,
        *,
        jog: bool = False,
        rapid: bool = False,
        robot: bool = False
    ) -> Position:
        if self.flags.closed:
            logger.warning("Please home before moving.")
            return
        return super().moveTo(to, speed_factor=speed_factor, jog=jog, rapid=rapid, robot=robot)

    # Combined methods
    def closeChamber(self):
        """Close the chamber"""
        if self.flags.closed:
            return
        # Descend
        for wp in self.closing_waypoints:
            self.moveTo(wp)
        self.flags.closed = True
        return
    
    def openChamber(self, loading_position:bool = False):
        """
        Open the chamber, making sure to vent the chamber and home first
        
        Args:
            loading_position (bool, optional): whether to move to loading position. Defaults to False.
        """
        self.vent()
        self.home()
        if loading_position:
            self.moveTo(self.loading_position)
        self.flags.closed = False
        return


@pytest.fixture(scope="session")
def vacuum_chamber():
    vc = VacuumChamber(port=PORT)
    return vc

@pytest.mark.skipif((PORT not in get_ports()), reason="Requires serial connection to device")
def test_vacuum_chamber(vacuum_chamber):
    vacuum_chamber.home()
    vacuum_chamber.openChamber(loading_position=True)
    vacuum_chamber.closeChamber()
    vacuum_chamber.evacuate()
    vacuum_chamber.vent()
    vacuum_chamber.openChamber(loading_position=False)

if __name__ == "__main__":
    vc = VacuumChamber(port=PORT, limits=[[-118,-28,0],[0,0,0]])
    vc.home()
    vc.openChamber(loading_position=True)
    vc.closeChamber()
    vc.evacuate()
    vc.vent()
    vc.openChamber(loading_position=False)
