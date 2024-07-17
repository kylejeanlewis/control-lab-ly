# %% -*- coding: utf-8 -*-
"""
This module holds the class for force clamp setups.

Classes:
    ForceClampSetup (CompoundSetup)
"""
# Standard library imports
from __future__ import annotations
import logging
import time
from typing import Optional, Protocol

# Third party imports
import numpy as np

# Local application imports
from ..compound_utils import CompoundSetup

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class Mover(Protocol):
    limits: tuple[tuple]
    max_speeds: np.ndarray
    position: tuple[np.ndarray]
    tool_position: tuple[np.ndarray]
    def home(self, *args, **kwargs):
        ...
    def move(self, *args, **kwargs):
        ...
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
    - `toggleClamp`: close or open the clamp
    - `waitTouch`: wait for the sensor to make contact with sample
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
        
        # Quick approach
        target_z = min(self.mover.limits[0][2], self.mover.limits[1][2])
        target = np.array((*self.mover.position[0][:2],target_z))
        target = self.mover._transform_out(target)
        self.mover.moveTo(target, speed_factor=speed_factor, wait=False, jog=True)
        self.waitTouch(threshold=threshold, timeout=timeout)
        self.mover.stop()
        target = self.mover.tool_position[0]
        
        # Retract a little to avoid overshooting
        self.mover.move('z',retract_height)
        # time.sleep(2)
        
        # Reduce movement speed and approach again
        self.mover.moveTo(target, speed_factor=0.1, wait=False, jog=True)
        self.waitTouch(threshold=threshold, timeout=timeout)
        self.mover.stop()
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
    
    def waitTouch(self, threshold:float, timeout:float = 60):
        """
        Wait for the sensor to make contact with sample

        Args:
            threshold (float): threshold value to register as making contact
            timeout (float, optional): timeout in seconds before aborting clamp. Defaults to 60.
        """
        start = time.time()
        while True:
            time.sleep(0.001)
            if abs(self.sensor.getValue()) >= abs(threshold):
                logger.info('Made contact')
                break
            if time.time() - start > timeout:
                logger.info('Touch timeout')
                break
        return
    