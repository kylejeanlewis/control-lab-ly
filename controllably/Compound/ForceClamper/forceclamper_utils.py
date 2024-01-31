# %% -*- coding: utf-8 -*-
"""
This module holds the class for force clamp setups.

Classes:
    ForceClampSetup (CompoundSetup)
"""
# Standard library imports
from __future__ import annotations
import numpy as np
import time
from typing import Optional, Protocol

# Local application imports
from ..compound_utils import CompoundSetup
print(f"Import: OK <{__name__}>")

class Mover(Protocol):
    limits: tuple[tuple]
    max_speeds: np.ndarray
    tool_position: tuple[np.ndarray]
    def home(self, *args, **kwargs):
        ...
    def move(self, *args, **kwargs):
        ...
    # def setSpeed(self, *args, **kwargs):
    #     ...
    # def setSpeedFactor(self, *args, **kwargs):
    #     ...
    def stop(self, *args, **kwargs):
        ...
        
class Sensor(Protocol):
    baseline: float
    def getValue(self):
        ...

class ForceClampSetup(CompoundSetup):
    """
    Force Clamp Setup routines

    ### Constructor 
    Args:
        `config` (Optional[str], optional): filename of config .yaml file. Defaults to None.
        `layout` (Optional[str], optional): filename of layout .json file. Defaults to None.
        `component_config` (Optional[dict], optional): configuration dictionary of components. Defaults to None.
        `layout_dict` (Optional[dict], optional): dictionary of layout. Defaults to None.
        `components` (Optional[dict], optional): dictionary of components. Defaults to None.
    
    ### Attributes
    - `threshold` (float): threshold value to trigger clamp to stop
    
    ### Properties
    - `mover` (Mover): movement / translation robot
    - `sensor` (Sensor): sensor tool to measure force exerted
    
    ### Methods
    - `clamp`: clamp down on object
    - `reset`: reset the z-height of mover
    - `toggleClamp`:
    """
    
    def __init__(self, 
        config: Optional[str] = None, 
        layout: Optional[str] = None, 
        component_config: Optional[dict] = None, 
        layout_dict: Optional[dict] = None, 
        components: Optional[dict] = None,
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            config (Optional[str], optional): filename of config .yaml file. Defaults to None.
            layout (Optional[str], optional): filename of layout .json file. Defaults to None.
            component_config (Optional[dict], optional): configuration dictionary of components. Defaults to None.
            layout_dict (Optional[dict], optional): dictionary of layout. Defaults to None.
            components (Optional[dict], optional): dictionary of components. Defaults to None.
        """
        super().__init__(
            config=config, 
            layout=layout, 
            component_config=component_config, 
            layout_dict=layout_dict, 
            components=components,
            **kwargs
        )
        self.threshold = 1.05 * self.sensor.baseline
        return
    
    # Properties
    @property
    def mover(self) -> Mover:
        return self.components.get('mover')
    
    @property
    def sensor(self) -> Sensor:
        return self.components.get('sensor')
    
    def clamp(
        self, 
        threshold:Optional[float] = None, 
        retract_height:int = 5, 
        speed_factor: float = 1.0,
        timeout:float = 60
    ):
        """
        Clamp down on object

        Args:
            threshold (Optional[float], optional): threshold value to trigger clamp to stop. Defaults to None.
            retract_height (int, optional): z-distance to retract before re-approach at slower speed. Defaults to 5.
            speed_factor (float, optional): fraction of max speed to perform initial approach. Defaults to 1.0.
            timeout (float, optional): timeout in seconds before aborting clamp. Defaults to 60.
        """
        threshold = self.threshold if threshold is None else threshold
        # speed_z = self.mover.max_speeds[2] * speed_factor
        # _,prevailing_speed = self.mover.setSpeed(speed_z)
        # _,prevailing_speed_factor = self.mover.setSpeedFactor(speed_factor)
        
        # Quick approach
        target_z = min(self.mover.limits[0][2], self.mover.limits[1][2])
        target = np.array((*self.mover.position[0][:2],target_z))
        target = self.mover._transform_out(target)
        start = time.time()
        # self.mover.moveTo(target, wait=False, jog=True)
        self.mover.moveTo(target, speed_factor=speed_factor, wait=False, jog=True)
        while True:
            time.sleep(0.001)
            if abs(self.sensor.getValue()) >= abs(threshold):
                self.mover.stop()
                break
            if time.time() - start > timeout:
                break
        
        # Retract a little to avoid overshooting
        target = self.mover.tool_position[0]
        self.mover.move('z',retract_height)
        time.sleep(2)
        
        # Reduce movement speed and approach again
        # self.mover.setSpeed(speed_z*0.1)
        # self.mover.setSpeedFactor(0.1)
        start = time.time()
        self.mover.moveTo(target, speed_factor=0.1, wait=False, jog=True)
        while True:
            time.sleep(0.001)
            if abs(self.sensor.getValue()) >= abs(threshold):
                self.mover.stop()
                break
            if time.time() - start > timeout:
                break
        
        # self.mover.setSpeed(prevailing_speed)
        # self.mover.setSpeedFactor(prevailing_speed_factor)
        return
    
    def reset(self):
        """Reset the z-height of mover"""
        target_z = max(self.mover.limits[0][2], self.mover.limits[1][2]) - 5
        target = np.array((*self.mover.position[0][:2],target_z))
        target = self.mover._transform_out(target)
        self.mover.moveTo(target)
        return
    
    def toggleClamp(self, on:bool = False, threshold:Optional[float] = None):
        """
        Close or open the clamp

        Args:
            on (bool, optional): whether to clamp down on sample. Defaults to False.
            threshold (Optional[float], optional): threshold value to trigger clamp to stop. Defaults to None.
        """
        if on:
            self.clamp(threshold=threshold)
        else:
            self.reset()
        return
    