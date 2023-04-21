# %% -*- coding: utf-8 -*-
"""
This module holds the class for liquid mover setups.

Classes:
    LiquidMoverSetup (CompoundSetup)
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

class Liquid(Protocol):
    def aspirate(self, *args, **kwargs):
        ...
    def dispense(self, *args, **kwargs):
        ...
    def empty(self, *args, **kwargs):
        ...
    def fill(self, *args, **kwargs):
        ... 
    def setFlag(self, *args, **kwargs):
        ...

class Mover(Protocol):
    home_coordinates: np.ndarray
    implement_offset: np.ndarray
    speed: float
    _speed_max: float
    def home(self, *args, **kwargs):
        ...
    def isFeasible(self, *args, **kwargs):
        ...
    def loadDeck(self, *args, **kwargs):
        ...
    def move(self, *args, **kwargs):
        ...
    def moveTo(self, *args, **kwargs):
        ...
    def safeMoveTo(self, *args, **kwargs):
        ...
    def setSpeed(self, *args, **kwargs):
        ...
    
class LiquidMoverSetup(CompoundSetup):
    """
    Liquid Mover Setup routines

    ### Constructor
    Args:
        `config` (Optional[str], optional): filename of config .yaml file. Defaults to None.
        `layout` (Optional[str], optional): filename of layout .json file. Defaults to None.
        `component_config` (Optional[dict], optional): configuration dictionary of component settings. Defaults to None.
        `layout_dict` (Optional[dict], optional): dictionary of layout. Defaults to None.
        `components` (Optional[dict], optional): dictionary of components. Defaults to None.
        `tip_approach_height` (float, optional): height in mm from which to approach tip rack during pick up. Defaults to 20.
        
    ### Attributes
    - `tip_approach_height` (float): height in mm from which to approach tip rack during tip pickup
    
    ### Properties
    - `liquid` (Liquid): liquid transfer tool
    - `mover` (Mover): movement / translation robot
    
    ### Methods
    - `align`: align the tool tip to the target coordinates, while also considering any additional offset
    - `aspirateAt`: aspirate specified volume at target location, at desired speed
    - `attachTip`: attach new pipette tip
    - `attachTipAt`: attach new pipette tip from specified location
    - `dispenseAt`: dispense specified volume at target location, at desired speed
    - `ejectTip`: eject the pipette tip
    - `ejectTipAt`: eject the pipette tip at the specified location
    - `loadDeck`: load Labware objects onto the deck from file or dictionary
    - `reset`: alias for `rest()`
    - `rest`: go back to the rest position or home
    - `returnTip`: return current tip to its original rack position
    - `touchTip`: touch the tip against the inner walls of the well
    - `updateStartTip`: set the position of the first available pipette tip
    """
    
    _default_flags: dict[str, bool] = {'at_rest': False}
    def __init__(self, 
        config: Optional[str] = None, 
        layout: Optional[str] = None, 
        component_config: Optional[dict] = None, 
        layout_dict: Optional[dict] = None,
        components: Optional[dict] = None,
        tip_approach_height: float = 20, 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            config (Optional[str], optional): filename of config .yaml file. Defaults to None.
            layout (Optional[str], optional): filename of layout .json file. Defaults to None.
            component_config (Optional[dict], optional): configuration dictionary of component settings. Defaults to None.
            layout_dict (Optional[dict], optional): dictionary of layout. Defaults to None.
            components (Optional[dict], optional): dictionary of components. Defaults to None.
            tip_approach_height (float, optional): height in mm from which to approach tip rack during tip pickup. Defaults to 20.
        """
        super().__init__(
            config=config, 
            layout=layout, 
            component_config=component_config, 
            layout_dict=layout_dict, 
            components=components,
            **kwargs
        )
        self.tip_approach_height = tip_approach_height
        pass
    
    # Properties
    @property
    def liquid(self) -> Liquid:
        return self.components.get('liquid')
    
    @property
    def mover(self) -> Mover:
        return self.components.get('mover')

    def align(self, coordinates:tuple[float], offset:tuple[float] = (0,0,0)):
        """
        Align the tool tip to the target coordinates, while also considering any additional offset

        Args:
            coordinates (tuple[float]): target coordinates
            offset (tuple[float], optional): additional x,y,z offset from tool tip. Defaults to (0,0,0).
        """
        coordinates = np.array(coordinates) - np.array(offset)
        if not self.mover.isFeasible(coordinates, transform=True, tool_offset=True):
            raise ValueError(f"Infeasible tool position! {coordinates}")
        self.mover.safeMoveTo(coordinates, ascent_speed=0.2*self.mover._speed_max, descent_speed=0.2*self.mover._speed_max)
        self.setFlag(at_rest=False)
        return
    
    def aspirateAt(self, 
        coordinates: tuple[float], 
        volume: float, 
        speed: Optional[float] = None, 
        channel: Optional[int] = None, 
        **kwargs
    ):
        """
        Aspirate specified volume at target location, at desired speed

        Args:
            coordinates (tuple[float]): target coordinates
            volume (float): volume in uL
            speed (Optional[float], optional): speed to aspirate at (uL/s). Defaults to None.
            channel (Optional[int], optional): channel to use. Defaults to None.
        """
        if 'eject' in dir(self.liquid) and not self.liquid.isTipOn():
            print("[aspirate] There is no tip attached.")
            return
        if channel is not None:
            offset = self.liquid.channels[channel].offset if 'channels' in dir(self.liquid) else self.liquid.offset
            self.align(coordinates=coordinates, offset=offset)
            self.liquid.aspirate(volume=volume, speed=speed, channel=channel)
        elif 'channels' in dir(self.liquid):
            for chn in self.liquid.channels:
                offset = self.liquid.channels[chn].offset
                self.align(coordinates=coordinates, offset=offset)
                self.liquid.aspirate(volume=volume, speed=speed, channel=chn)
        return
    
    def attachTip(self, 
        slot: str = 'tip_rack', 
        start_tip: Optional[str] = None,
        tip_length: float = 80, 
        channel: Optional[int] = None
    ) -> tuple[float]:
        """
        Attach new pipette tip

        Args:
            slot (str, optional): name of slot with pipette tips. Defaults to 'tip_rack'.
            start_tip (Optional[str], optional): channel to use. Defaults to None.
            tip_length (float, optional): length of pipette tip. Defaults to 80.
            channel (Optional[int], optional): channel to use. Defaults to None.
        
        Returns:
            tuple[float]: coordinates of top of tip rack well
        """
        if start_tip is not None:
            self.updateStartTip(start_tip=start_tip, slot=slot)
        next_tip_location, tip_length = self.positions[slot].pop(0)
        return self.attachTipAt(next_tip_location, tip_length=tip_length, channel=channel)
    
    def attachTipAt(self, 
        coordinates: tuple[float], 
        tip_length: float = 80, 
        channel: Optional[int] = None
    ) -> tuple[float]:
        """
        Attach new pipette tip from specified location

        Args:
            coordinates (tuple[float]): coordinates of pipette tip
            tip_length (float, optional): length of pipette tip. Defaults to 80.
            channel (Optional[int], optional): channel to use. Defaults to None.

        Raises:
            AttributeError: `attachTip` and `attachTipAt` methods not available
            RuntimeError: eject current tip before attaching new tip

        Returns:
            tuple[float]: coordinates of attach tip location
        """
        if 'eject' not in dir(self.liquid):
            raise AttributeError("`attachTip` and `attachTipAt` methods not available.")
        if self.liquid.isTipOn():
            raise RuntimeError("Please eject current tip before attaching new tip.")
        
        tip_offset = np.array((0,0,-tip_length + self.liquid.tip_inset_mm))
        self.align(coordinates)
        self.mover.move('z', -self.tip_approach_height, speed=0.01*self.mover._speed_max)
        time.sleep(3)
        
        self.liquid.tip_length = tip_length
        self.mover.implement_offset = self.mover.implement_offset + tip_offset
        self.mover.move('z', self.tip_approach_height+tip_length, speed=0.2*self.mover._speed_max)
        time.sleep(1)
        self.liquid.setFlag(tip_on=True)
        
        if not self.liquid.isTipOn():
            tip_length = self.liquid.tip_length
            tip_offset = np.array((0,0,-tip_length))
            self.mover.implement_offset = self.mover.implement_offset - tip_offset
            self.liquid.tip_length = 0
            self.liquid.setFlag(tip_on=False)
        self._temp_tip_home = tuple(coordinates)
        return coordinates
    
    def dispenseAt(self, 
        coordinates: tuple[float], 
        volume: float, 
        speed: Optional[float] = None, 
        channel: Optional[int] = None, 
        **kwargs
    ):
        """
        Dispense specified volume at target location, at desired speed

        Args:
            coordinates (tuple[float]): target coordinates
            volume (float): volume in uL
            speed (Optional[float], optional): speed to dispense at (uL/s). Defaults to None.
            channel (Optional[int], optional): channel to use. Defaults to None.
        """
        if 'eject' in dir(self.liquid) and not self.liquid.isTipOn():
            print("[dispense] There is no tip attached.")
            return
        if channel is not None:
            offset = self.liquid.channels[channel].offset if 'channels' in dir(self.liquid) else self.liquid.offset
            self.align(coordinates=coordinates, offset=offset)
            self.liquid.dispense(volume=volume, speed=speed, channel=channel)
        elif 'channels' in dir(self.liquid):
            for chn in self.liquid.channels:
                offset = self.liquid.channels[chn].offset
                self.align(coordinates=coordinates, offset=offset)
                self.liquid.dispense(volume=volume, speed=speed, channel=chn)
        return
    
    def ejectTip(self, slot:str = 'bin', channel:Optional[int] = None) -> tuple[float]:
        """
        Eject the pipette tip

        Args:
            slot (str, optional): name of slot with bin. Defaults to 'bin'.
            channel (Optional[int], optional): channel to use. Defaults to None.
        
        Returns:
            tuple[float]: coordinates of top of bin well
        """
        bin_location,_ = self.positions[slot][0]
        return self.ejectTipAt(bin_location, channel=channel)
    
    def ejectTipAt(self, coordinates:tuple[float], channel:Optional[int] = None) -> tuple[float]:
        """
        Eject the pipette tip at the specified location

        Args:
            coordinates (tuple[float]): coordinate of where to eject tip
            channel (Optional[int], optional): channel to use. Defaults to None.
            
        Raises:
            AttributeError: `attachTip` and `attachTipAt` methods not available
            RuntimeError: no tip to eject
            
        Returns:
            tuple[float]: coordinates of eject tip location
        """
        if 'eject' not in dir(self.liquid):
            raise AttributeError("`ejectTip` and `ejectTipAt` methods not available.")
        if not self.liquid.isTipOn():
            tip_length = self.liquid.tip_length
            tip_offset = np.array((0,0,-tip_length + self.liquid.tip_inset_mm))
            self.mover.implement_offset = self.mover.implement_offset - tip_offset
            self.liquid.tip_length = 0
            self.liquid.setFlag(tip_on=False)
            raise RuntimeError("There is currently no tip to eject.")

        self.align(coordinates)
        time.sleep(1)
        self.liquid.eject()
        
        tip_length = self.liquid.tip_length
        tip_offset = np.array((0,0,-tip_length))
        self.mover.implement_offset = self.mover.implement_offset - tip_offset
        self.liquid.tip_length = 0
        self.liquid.setFlag(tip_on=False)
        return coordinates
    
    def loadDeck(self, layout_file:Optional[str] = None, layout_dict:Optional[dict] = None):
        """
        Load Labware objects onto the deck from file or dictionary
        
        Args:
            layout_file (Optional[str], optional): filename of layout .json file. Defaults to None.
            layout_dict (Optional[dict], optional): dictionary of layout. Defaults to None.
        """
        super().loadDeck(layout_file=layout_file, layout_dict=layout_dict)
        self.mover.loadDeck(layout_file=layout_file, layout_dict=layout_dict)
        return
    
    def reset(self):
        """Alias for `rest()`"""
        self.rest()
        return
    
    def rest(self):
        """Go back to the rest position or home"""
        if self.flags['at_rest']:
            return
        rest_coordinates = self.positions.get('rest', None)
        if rest_coordinates is None:
            self.mover.home()
        else:
            self.align(rest_coordinates)
        self.setFlag(at_rest=True)
        return
    
    def returnTip(self) -> tuple[float]:
        """
        Return current tip to its original rack position

        Returns:
            tuple[float]: coordinates of eject tip location
        """
        coordinates = self.__dict__.pop('_temp_tip_home')
        return self.ejectTipAt(coordinates=(*coordinates[:2],coordinates[2]-18))
    
    def touchTip(self, well:Well, safe_move:bool = False) -> tuple[float]:
        """
        Touch the tip against the inner walls of the well
        
        Args:
            well (Well): Well object
            safe_move (bool, optional): whether to move safely (i.e. go back to safe height first). Defaults to False.

        Returns:
            tuple[float]: coordinates of well center
        """
        diameter = well.diameter
        if safe_move:
            self.align(coordinates=well.from_top((0,0,-10)))
        else:
            speed = self.mover.speed
            self.mover.setSpeed(speed=0.2*self.mover._speed_max)
            self.mover.moveTo(coordinates=well.from_top((0,0,-10)))
            self.mover.setSpeed(speed=speed)
        for axis in ('x','y'):
            self.mover.move(axis, diameter/2, speed=0.2*self.mover._speed_max)
            self.mover.move(axis, -diameter, speed=0.2*self.mover._speed_max)
            self.mover.move(axis, diameter/2, speed=0.2*self.mover._speed_max)
        self.mover.moveTo(coordinates=well.top)
        return well.top
    
    def updateStartTip(self, start_tip:str, slot:str = 'tip_rack'):
        """
        Set the position of the first available pipette tip

        Args:
            start_tip (str): well name of the first available pipette tip
            slot (str, optional): name of slot with pipette tips. Defaults to 'tip_rack'.
        """
        wells_list = self.deck.at(slot).wells_list.copy()
        well_names = [well.name for well in wells_list]
        if start_tip not in well_names:
            print(f"Received: start_tip={start_tip}; slot={slot}")
            print("Please enter a compatible set of inputs.")
            return
        self.positions[slot] = wells_list
        for name in well_names:
            if name == start_tip:
                break
            self.positions[slot].pop(0)
        return
    