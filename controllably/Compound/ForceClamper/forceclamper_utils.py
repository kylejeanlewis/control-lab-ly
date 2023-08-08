# %% -*- coding: utf-8 -*-
"""

"""
# Standard library imports
from __future__ import annotations
import numpy as np
import time
from typing import Optional, Protocol

# Local application imports
from ...misc.layout import Well
from ..compound_utils import CompoundSetup
print(f"Import: OK <{__name__}>")

class Sensor(Protocol):
    def getValue(self):
        ...

class Mover(Protocol):
    limits: np.ndarray
    max_speed: np.ndarray
    tool_position: tuple[np.ndarray]
    def home(self, *args, **kwargs):
        ...
    def move(self, *args, **kwargs):
        ...
    def setSpeed(self, *args, **kwargs):
        ...
    def stop(self, *args, **kwargs):
        ...

class ForceClampSetup (CompoundSetup):
    def __init__(self, 
        config: Optional[str] = None, 
        layout: Optional[str] = None, 
        component_config: Optional[dict] = None, 
        layout_dict: Optional[dict] = None, 
        components: Optional[dict] = None,
        **kwargs
    ):
        super().__init__(
            config=config, 
            layout=layout, 
            component_config=component_config, 
            layout_dict=layout_dict, 
            components=components,
            **kwargs
        )
        self.threshold = 0  # TODO: baseline * 1.01
        return
    
    # Properties
    @property
    def mover(self) -> Mover:
        return self.components.get('mover')
    
    @property
    def sensor(self) -> Sensor:
        return self.components.get('sensor')
    
    def clamp(self, threshold:Optional[float] = None, retract_height:int = 5, timeout:float = 60):
        threshold = self.threshold if threshold is None else threshold
        speed = self.mover.max_speed[2]
        self.mover.setSpeed(speed)
        
        # Quick approach
        target_z = min(self.mover.limits[0][2], self.mover.limits[1][2])
        target = np.array((*self.mover.tool_position[0][:2],target_z))
        start = time.time()
        self.mover.moveTo(target, wait=False, jog=True)
        while True:
            time.sleep(0.001)
            if self.sensor.getValue() >= threshold:
                self.mover.stop()
                break
            if time.time() - start > timeout:
                break
        
        # Retract a little to avoid overshooting
        target = self.mover.tool_position[0]
        self.mover.move('z',retract_height)
        time.sleep(1)
        
        # Reduce movement speed and approach again
        self.mover.setSpeed(speed*0.1)
        start = time.time()
        self.mover.moveTo(target, wait=False)
        while True:
            time.sleep(0.001)
            if self.sensor.getValue() >= threshold:
                self.mover.stop()
                break
            if time.time() - start > timeout:
                break
        
        self.mover.setSpeed(speed)
        return
    
    def toggleClamp(self, on:bool = False, threshold:Optional[float] = None):
        if on:
            self.clamp(threshold)
        else:
            self.mover.home()
        return
    