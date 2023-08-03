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
    coordinates: np.ndarray
    limits: np.ndarray
    speed: float
    max_speed: np.ndarray
    def home(self, *args, **kwargs):
        ...
    def isFeasible(self, *args, **kwargs):
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
        self.threshold = 0
        return
    
    # Properties
    @property
    def mover(self) -> Mover:
        return self.components.get('mover')
    
    @property
    def sensor(self) -> Sensor:
        return self.components.get('sensor')
    
    def clamp(self, threshold:Optional[float] = None):
        threshold = self.threshold if threshold is None else threshold
        speed = self.mover.speed
        self.mover.setSpeed(self.mover.max_speed[2])
        
        # Quick approach
        target_z = self.mover.limits[1][2]
        target = np.array((*self.mover.coordinates[:2],target_z))
        start = time.time()
        self.mover.moveTo(target, wait=False)
        while True:
            time.sleep(0.1)
            if self.sensor.getValue() >= threshold:
                self.mover.stop()
                break
            if time.time() - start > 60:
                break
        
        # Retract a little to avoid overshooting
        target = self.mover.coordinates
        retract_height = 5
        self.mover.move('z',retract_height)
        
        # Reduce movement speed and approach again
        self.mover.setSpeed(self.mover.max_speed[2]*0.005)
        start = time.time()
        self.mover.moveTo(target, wait=False)
        while True:
            time.sleep(0.1)
            if self.sensor.getValue() >= threshold:
                self.mover.stop()
                break
            if time.time() - start > 60:
                break
        
        self.mover.setSpeed(speed)
        return
    
    def toggleClamp(self, on:bool = False, threshold:Optional[float] = None):
        if on:
            self.clamp(threshold)
        else:
            self.mover.home()
        return
    