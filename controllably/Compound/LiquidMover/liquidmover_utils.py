# -*- coding: utf-8 -*-
"""
This module holds the class for liquid mover setups.

Classes:
    LiquidMoverSetup (CompoundSetup)
"""
# Standard library imports
from __future__ import annotations
import logging
from types import SimpleNamespace
from typing import Sequence, Optional, Protocol

# Third party imports
import numpy as np

# Local application imports
from ...core.compound import Compound, Part
from ...core.position import Well, Position, Labware, Deck

from ..compound_utils import CompoundSetup

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

class Liquid(Protocol):
    offset: Sequence[float]
    tip_inset_mm: float                     # For liquid handlers with replaceable tips
    tip_length: float                       # For liquid handlers with replaceable tips
    def aspirate(self, *args, **kwargs):
        ...
    def dispense(self, *args, **kwargs):
        ...
    def setFlag(self, *args, **kwargs):
        ...
    def eject(self, *args, **kwargs):       # For liquid handlers with replaceable tips
        ...
    def isTipOn(self, *args, **kwargs):     # For liquid handlers with replaceable tips
        ...

class Mover(Protocol):
    deck: Deck
    tool_offset: Position                   # For liquid handlers with replaceable tips
    def loadDeck(self, *args, **kwargs):
        ...
    def move(self, *args, **kwargs):
        ...
    def moveTo(self, *args, **kwargs):
        ...
    def safeMoveTo(self, *args, **kwargs):
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
            config = config, 
            layout = layout, 
            component_config = component_config, 
            layout_dict = layout_dict, 
            components = components,
            **kwargs
        )
        self.tip_approach_height = tip_approach_height
        self.ascent_speed_ratio = kwargs.get('ascent_speed_ratio', 0.2)
        self.descent_speed_ratio = kwargs.get('descent_speed_ratio', 0.2)
        self.pick_tip_speed_ratio = kwargs.get('pick_tip_speed_ratio', 0.01)
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
        if not self.mover.isFeasible(coordinates, transform_in=True, tool_offset=True):
            raise ValueError(f"Infeasible tool position! {coordinates}")
        self.mover.safeMoveTo(
            coordinates, 
            ascent_speed_ratio = self.ascent_speed_ratio, 
            descent_speed_ratio = self.descent_speed_ratio
        )
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
            logger.info("[aspirate] There is no tip attached.")
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
        else:
            self.align(coordinates=coordinates)
            self.liquid.aspirate(volume=volume, speed=speed)
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
        if 'eject' not in dir(self.liquid):
            raise AttributeError("`attachTip` and `attachTipAt` methods not available.")
        if self.liquid.isTipOn():
            raise RuntimeError("Please eject current tip before attaching new tip.")
        
        if start_tip is not None:
            self.updateStartTip(start_tip=start_tip, slot=slot)
        well = self.deck.at(slot).wells_list[-len(self.positions[slot])]
        logger.info(well.name)
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
        self.mover.move(
            'z', -self.tip_approach_height, 
            speed_factor = self.pick_tip_speed_ratio
        )
        
        self.liquid.tip_length = tip_length
        self.mover.implement_offset = self.mover.implement_offset + tip_offset
        self.mover.move(
            'z', self.tip_approach_height - tip_offset[2], 
            speed_factor = self.ascent_speed_ratio
        )
        self.liquid.setFlag(tip_on=True)
        
        if not self.liquid.isTipOn():
            tip_length = self.liquid.tip_length
            tip_offset = np.array((0,0,-tip_length + self.liquid.tip_inset_mm))
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
            logger.info("[dispense] There is no tip attached.")
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
        else:
            self.align(coordinates=coordinates)
            self.liquid.dispense(volume=volume, speed=speed)
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
        if 'eject' not in dir(self.liquid):
            raise AttributeError("`ejectTip` and `ejectTipAt` methods not available.")
        if not self.liquid.isTipOn():
            tip_length = self.liquid.tip_length
            tip_offset = np.array((0,0,-tip_length + self.liquid.tip_inset_mm))
            self.mover.implement_offset = self.mover.implement_offset - tip_offset
            self.liquid.tip_length = 0
            self.liquid.setFlag(tip_on=False)
            raise RuntimeError("There is currently no tip to eject.")
        
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
        self.liquid.eject()
        
        tip_length = self.liquid.tip_length
        tip_offset = np.array((0,0,-tip_length + self.liquid.tip_inset_mm))
        self.mover.implement_offset = self.mover.implement_offset - tip_offset
        self.liquid.tip_length = 0
        self.liquid.setFlag(tip_on=False)
        return coordinates
    
    def loadDeck(self, layout_file:Optional[str] = None, layout_dict:Optional[dict] = None, **kwargs):
        """
        Load Labware objects onto the deck from file or dictionary
        
        Args:
            layout_file (Optional[str], optional): filename of layout .json file. Defaults to None.
            layout_dict (Optional[dict], optional): dictionary of layout. Defaults to None.
        """
        super().loadDeck(layout_file=layout_file, layout_dict=layout_dict, **kwargs)
        self.mover.loadDeck(layout_file=layout_file, layout_dict=layout_dict, **kwargs)
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
    
    def returnTip(self, insert_mm:int = 18) -> tuple[float]:
        """
        Return current tip to its original rack position
        
        Args:
            insert_mm (int, optional): length of tip to insert into rack before ejecting. Defaults to 18.

        Returns:
            tuple[float]: coordinates of eject tip location
        """
        coordinates = self.__dict__.pop('_temp_tip_home')
        coordinates = self.ejectTipAt(coordinates=(*coordinates[:2],coordinates[2]-insert_mm))
        rack_coordinates = (*coordinates[:2],coordinates[2]+insert_mm)
        return rack_coordinates
    
    def touchTip(self, well:Well, safe_move:bool = False, speed_factor:float = 0.2, **kwargs) -> tuple[float]:
        """
        Touch the tip against the inner walls of the well
        
        Args:
            well (Well): Well object
            safe_move (bool, optional): whether to move safely (i.e. go back to safe height first). Defaults to False.
            speed_factor (float, optional): fraction of maximum speed to perform touch tip. Defaults to 0.2.

        Returns:
            tuple[float]: coordinates of well center
        """
        diameter = well.diameter
        depth = well.depth *0.05
        if safe_move:
            self.align(coordinates=well.fromTop((0,0,-depth)))
        else:
            self.mover.moveTo(coordinates=well.fromTop((0,0,-depth)))
        _, prevailing_speed_factor = self.mover.setSpeedFactor(speed_factor)
        for axis in ('x','y'):
            self.mover.move(axis, diameter/2)
            self.mover.move(axis, -diameter)
            self.mover.move(axis, diameter/2)
        self.mover.setSpeedFactor(prevailing_speed_factor)
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
            logger.info(f"Received: start_tip={start_tip}; slot={slot}")
            logger.info("Please enter a compatible set of inputs.")
            return
        self.positions[slot] = [(well.top, well.depth) for well in wells_list]
        for name in well_names:
            if name == start_tip:
                break
            self.positions[slot].pop(0)
        return


class LiquidMover(Compound):
    """
    LiquidMover provides a high-level interface for liquid handling operations
    
    ### Constructor
        `parts` (dict[str,Part]): dictionary of parts
        `tip_approach_distance` (float, optional): distance in mm from top to travel down to pick tip. Defaults to 20.
        `speed_factor_pick_tip` (float, optional): speed factor to pick up tip. Defaults to 0.01.
        `speed_factor_lateral` (float, optional): speed factor for lateral movement. Defaults to None.
        `speed_factor_up` (float, optional): speed factor for upward movement. Defaults to 0.2.
        `speed_factor_down` (float, optional): speed factor for downward movement. Defaults to 0.2.
        `verbose` (bool, optional): verbosity of output. Defaults to False.
        
    ### Attributes and properties
        `tip_approach_distance` (float): distance in mm from top to travel down to pick tip
        `speed_factor_pick_tip` (float): speed factor to pick up tip
        `speed_factor_lateral` (float): speed factor for lateral movement
        `speed_factor_up` (float): speed factor for upward movement
        `speed_factor_down` (float): speed factor for downward movement
        `liquid` (Liquid): liquid transfer tool
        `mover` (Mover): movement / translation robot
        `connection_details` (dict): connection details of each part
        `parts` (SimpleNamespace[str,Part]): namespace of parts
        `flags` (SimpleNamespace[str,bool]): flags of class
        `is_busy` (bool): whether any part is busy
        `is_connected` (bool): whether all parts are connected
        `verbose` (bool): verbosity of class
        
        #### (For liquid handlers with replaceable tips)
        `bin_slots` (dict[int,Labware]): dictionary of bin slots
        `tip_racks` (dict[int,Labware]): dictionary of tip racks
        `tip_lists` (dict[int,list[str]]): dictionary of tip lists
        `current_tip_detail` (dict[str, str|np.ndarray]): dictionary of current tip details
        
    ### Methods
        `align`: align the tool tip to the target coordinates, while also considering any additional offset
        `aspirateAt`: aspirate specified volume at target location, at desired speed
        `dispenseAt`: dispense specified volume at target location, at desired speed
        `touchTip`: touch the tip against the inner walls of the well
        
        #### (For liquid handlers with replaceable tips)
        `findTipRacks`: find all tip racks on the deck
        `assignTipRack`: assign a tip rack by its slot
        `assignBin`: assign a bin by its slot
        `attachTip`: attach new pipette tip from next available rack position
        `attachTipAt`: attach new pipette tip from specified location
        `ejectTip`: eject the pipette tip at the bin
        `ejectTipAt`: eject the pipette tip at the specified location
        `resetTips`: reset (i.e. clear) all tip racks
        `returnTip`: return current tip to its original rack position
        `updateStartTip`: set the name of the first available pipette tip
    """
    
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(verbose=False)
    def __init__(self, 
        *args, 
        parts: dict[str,Part], 
        tip_approach_distance: float = 20,
        speed_factor_pick_tip: float = 0.01,
        speed_factor_lateral: float|None = None,
        speed_factor_up: float = 0.2,
        speed_factor_down: float = 0.2,
        verbose = False, 
        **kwargs
    ):
        """ 
        Initialize LiquidMover class
        
        Args:
            parts (dict[str,Part]): dictionary of parts
            tip_approach_distance (float, optional): distance in mm from top to travel down to pick tip. Defaults to 20.
            speed_factor_pick_tip (float, optional): speed factor to pick up tip. Defaults to 0.01.
            speed_factor_lateral (float, optional): speed factor for lateral movement. Defaults to None.
            speed_factor_up (float, optional): speed factor for upward movement. Defaults to 0.2.
            speed_factor_down (float, optional): speed factor for downward movement. Defaults to 0.2.
            verbose (bool, optional): verbosity of output. Defaults to False.
        """
        super().__init__(*args, parts=parts, verbose=verbose, **kwargs)
        self.tip_approach_distance = tip_approach_distance
        self.speed_factor_pick_tip = speed_factor_pick_tip
        self.speed_factor_lateral = speed_factor_lateral
        self.speed_factor_up = speed_factor_up
        self.speed_factor_down = speed_factor_down
        
        # For liquid handlers with replaceable tips
        if hasattr(self.liquid, 'eject'):
            self.bin_slots: dict[int, Labware] = {}
            self.tip_racks: dict[int, Labware] = {}
            self.tip_lists: dict[int, list[str]] = {}
            self.current_tip_detail: dict[str, str|np.ndarray] = {}
        
        return
    
    # Properties
    @property
    def liquid(self) -> Liquid:
        return getattr(self.parts, 'liquid')
    
    @property
    def mover(self) -> Mover:
        return getattr(self.parts, 'mover')
    
    def align(self, 
        coordinates: Sequence[float]|np.ndarray, 
        offset: Sequence[float] = (0,0,0)
    ) -> Position:
        """
        Align the tool tip to the target coordinates, while also considering any additional offset
        
        Args:
            coordinates (Sequence[float]|np.ndarray): target coordinates
            offset (Sequence[float], optional): additional x,y,z offset from tool tip. Defaults to (0,0,0).
            
        Returns:
            Position: final coordinates of tool tip
        """
        target_coordinates = np.array(coordinates) - np.array(offset)
        return self.mover.safeMoveTo(
            target_coordinates,
            speed_factor_lateral = self.speed_factor_lateral,
            speed_factor_up = self.speed_factor_up,
            speed_factor_down = self.speed_factor_down
        )
    
    def aspirateAt(self,
        coordinates: Sequence[float]|np.ndarray,
        volume: float,
        speed: float|None = None,
        *,
        channel: int|None = None
    ):
        """
        Aspirate specified volume at target location, at desired speed
        
        Args:
            coordinates (Sequence[float]|np.ndarray): target coordinates
            volume (float): volume in uL
            speed (float|None, optional): speed to aspirate at (uL/s). Defaults to None.
            channel (int|None, optional): channel to use. Defaults to None.
        """
        assert not (hasattr(self.liquid, 'eject') and not self.liquid.isTipOn()), "A tip is required and no tip is attached."
        assert not (hasattr(self.liquid, 'channels') and channel is None), "Please specify a channel."
        offset = self.liquid.channels[channel].offset if hasattr(self.liquid, 'channels') else self.liquid.offset
        self.align(coordinates=coordinates, offset=offset)
        self.liquid.aspirate(volume=volume, speed=speed, channel=channel)
        return
    
    def dispenseAt(self,
        coordinates: Sequence[float]|np.ndarray,
        volume: float,
        speed: float|None = None,
        *,
        channel: int|None = None
    ):
        """
        Dispense specified volume at target location, at desired speed
        
        Args:
            coordinates (Sequence[float]|np.ndarray): target coordinates
            volume (float): volume in uL
            speed (float|None, optional): speed to dispense at (uL/s). Defaults to None.
            channel (int|None, optional): channel to use. Defaults to None.
        """
        assert not (hasattr(self.liquid, 'eject') and not self.liquid.isTipOn()), "A tip is required and no tip is attached."
        assert not (hasattr(self.liquid, 'channels') and channel is None), "Please specify a channel."
        offset = self.liquid.channels[channel].offset if hasattr(self.liquid, 'channels') else self.liquid.offset
        self.align(coordinates=coordinates, offset=offset)
        self.liquid.dispense(volume=volume, speed=speed, channel=channel)
        return
    
    def touchTip(self,
        well: Well,
        fraction_depth_from_top: float = 0.05,
        safe_move: bool = False,
        speed_factor: float = 0.2
    ) -> np.ndarray:
        """
        Touch the tip against the inner walls of the well
        
        Args:
            well (Well): `Well` object
            fraction_depth_from_top (float, optional): fraction of well depth from top to travel down. Defaults to 0.05.
            safe_move (bool, optional): whether to move safely (i.e. go back to safe height first). Defaults to False.
            speed_factor (float, optional): fraction of maximum speed to perform touch tip. Defaults to 0.2.
            
        Returns:
            np.ndarray: coordinates of top of well
        """
        dimensions = list(well.dimensions)
        dimensions = dimensions*2 if len(dimensions) == 1 else dimensions
        depth = well.depth * fraction_depth_from_top
        target = well.fromTop((0,0,-depth))
        _  = self.align(target) if safe_move else self.mover.moveTo(target)
        for axis,distance in zip('xy',dimensions):
            self.mover.move(axis, distance/2, speed_factor)
            self.mover.move(axis, -distance, speed_factor)
            self.mover.move(axis, distance/2, speed_factor)
        self.mover.moveTo(well.top)
        return well.top
    
    # For liquid handlers with replaceable tips
    def findTipRacks(self):
        """Find all tip racks on the deck"""
        deck = self.mover.deck
        assert isinstance(deck, Deck), "Please first load a Deck using `Mover.loadDeck()`."
        count = 0
        for slot_name, slot in deck.slots.items():
            labware = deck.slots[slot_name].loaded_labware
            if isinstance(labware, Labware) and labware.is_tiprack:
                self.assignTipRack(slot=slot_name, use_by_columns=True)
                count += 1
        self._logger.info(f"Found and assigned {count} tip racks.")
        return
    
    def assignTipRack(self, 
        slot:str, 
        zone:str|None = None, 
        *, 
        use_by_columns:bool = True, 
        start_tip:str|None = None
    ):
        """
        Assign a tip rack by its slot
        
        Args:
            slot (str): name of slot with tip rack
            zone (str|None, optional): name of zone. Defaults to None.
            use_by_columns (bool, optional): whether to use tips by columns. Defaults to True.
            start_tip (str|None, optional): name of start tip. Defaults to None.
        """
        deck = self.mover.deck
        assert deck is not None, "Please first load a Deck using `Mover.loadDeck()`."
        if zone is not None:
            assert zone in deck.zones, "Please enter a valid zone."
            deck = deck.zones[zone]
        assert slot in deck.slots, "Please enter a valid slot."
        
        labware = deck.slots[slot].loaded_labware
        assert labware is not None, "No Labware on the specified slot."
        assert labware.is_tiprack, "Labware is not a tip rack."
        
        index = max(self.tip_racks.keys()) + 1 if len(self.tip_racks) > 0 else 0
        self.tip_racks[index] = labware
        
        well_names = labware.listColumns() if use_by_columns else labware.listWells()
        well_name_list = []
        for l in well_names:
            well_name_list.extend(l)
        if start_tip is not None:
            assert start_tip in well_name_list, "Please enter a valid start tip."
            well_name_list = well_name_list[well_name_list.index(start_tip):]
        self.tip_lists[index] = well_name_list
        return
    
    def assignBin(self, slot:str, zone:str|None = None):
        """
        Assign a bin by its slot
        
        Args:
            slot (str): name of slot with bin
            zone (str|None, optional): name of zone. Defaults to None.
        """
        deck = self.mover.deck
        assert deck is not None, "Please first load a Deck using `Mover.loadDeck()`."
        if zone is not None:
            assert zone in deck.zones, "Please enter a valid zone."
            deck = deck.zones[zone]
        assert slot in deck.slots, "Please enter a valid slot."
        
        labware = deck.slots[slot].loaded_labware
        assert labware is not None, "No Labware on the specified slot."
        assert len(labware.wells) == 1, "Ensure the bin has only one well."
        
        index = max(self.bin_slots.keys()) + 1 if len(self.bin_slots) > 0 else 0
        self.bin_slots[index] = labware
        return
    
    def attachTip(self) -> np.ndarray:
        """
        Attach new pipette tip from next available rack position
        
        Returns:
            np.ndarray: coordinates of attach tip location
        """
        assert hasattr(self.liquid, 'eject'), "Tip not required."
        assert not self.liquid.isTipOn(), "A tip is already attached."
        
        index = min(self.tip_racks.keys())
        labware = self.tip_racks[index]
        name = self.tip_lists[index].pop(0)
        if len(self.tip_lists[index]) == 0:
            self.tip_lists.pop(index)
            self.tip_racks.pop(index)
        well = labware.wells[name]
        coordinates, tip_length = well.top, well.depth
        self.current_tip_detail['name'] = name
        return self.attachTipAt(coordinates, tip_length)
        
    def attachTipAt(self,
        coordinates: Sequence[float]|np.ndarray,
        tip_length: float
    ) -> np.ndarray:
        """ 
        Attach new pipette tip from specified location
        
        Args:
            coordinates (Sequence[float]|np.ndarray): coordinates of pipette tip
            tip_length (float): length of pipette tip
            
        Returns:
            np.ndarray: coordinates of attach tip location
        """
        assert hasattr(self.liquid, 'eject'), "Tip not required."
        assert not self.liquid.isTipOn(), "A tip is already attached."
        coordinates = np.array(coordinates)
        self.align(coordinates)
        
        self.mover.move('z', -self.tip_approach_distance, self.speed_factor_pick_tip)
        tip_inset = self.liquid.tip_inset_mm
        self.mover.tool_offset.translate((0,0,tip_inset))
        self.mover.tool_offset.translate((0,0,-tip_length))
        self.liquid.tip_length = tip_length
        
        self.mover.move('z', self.tip_approach_distance+tip_length-tip_inset, self.speed_factor_up)
        self.liquid.setFlag(tip_on=True)
        
        if not self.liquid.isTipOn():
            self.mover.tool_offset.translate((0,0,tip_length))
            self.mover.tool_offset.translate((0,0,-tip_inset))
            self.liquid.tip_length = 0
            self.liquid.setFlag(tip_on=False)
            return coordinates
        self.current_tip_detail['coordinates'] = coordinates
        return coordinates
    
    def ejectTip(self) -> np.ndarray:
        """
        Eject the pipette tip at the bin
        
        Returns:
            np.ndarray: coordinates of eject tip location
        """
        assert hasattr(self.liquid, 'eject'), "Ejection not required."
        assert self.liquid.isTipOn(), "No tip to eject."
        index = min(self.bin_slots.keys())
        labware = self.bin_slots[index]
        well = labware.listWells('c')[0]
        return self.ejectTipAt(well.top)
        
    def ejectTipAt(self, coordinates: Sequence[float]|np.ndarray) -> np.ndarray:
        """
        Eject the pipette tip at the specified location
        
        Args:
            coordinates (Sequence[float]|np.ndarray): coordinate of where to eject tip
            
        Returns:
            np.ndarray: coordinates of eject tip location
        """
        assert hasattr(self.liquid, 'eject'), "Ejection not required."
        assert self.liquid.isTipOn(), "No tip to eject."
        coordinates = np.array(coordinates)
        self.align(coordinates)
        
        self.liquid.eject()
        self.mover.tool_offset.translate((0,0,self.liquid.tip_length))
        self.mover.tool_offset.translate((0,0,-self.liquid.tip_inset_mm))
        self.liquid.tip_length = 0
        self.liquid.setFlag(tip_on=False)
        self._current_tip_origin = None
        return coordinates
    
    def resetTips(self):
        """Reset (i.e. clear) all tip racks"""
        self.tip_lists = {}
        self.tip_racks = {}
        return
    
    def returnTip(self, offset_from_top: Sequence[float]|np.ndarray = (0,0,-20)) -> np.ndarray:
        """
        Return current tip to its original rack position
        
        Args:
            offset_from_top (Sequence[float]|np.ndarray, optional): offset from top to eject tip. Defaults to (0,0,-20).
            
        Returns:
            np.ndarray: coordinates of eject tip location
        """
        assert {'name','coordinates'} == set(self.current_tip_detail.keys()), "Current tip details not properly defined."
        name = self.current_tip_detail.pop('name')
        coordinates = self.current_tip_detail.pop('coordinates')
        target_coordinates = coordinates + np.array(offset_from_top)
        self.ejectTipAt(target_coordinates)
        
        index = min(self.tip_racks.keys())
        self.tip_lists[index].append(name)
        return coordinates
    
    def updateStartTip(self, start_tip:str):
        """
        Set the name of the first available pipette tip
        
        Args:
            start_tip (str): well name of the first available pipette tip
        """
        index = min(self.tip_racks.keys())
        well_name_list = self.tip_lists[index]
        assert start_tip in well_name_list, "Please enter a valid start tip."
        well_name_list = well_name_list[well_name_list.index(start_tip):]
        self.tip_lists[index] = well_name_list
        if len(self.tip_lists[index]) == 0:
            self.tip_lists.pop(index)
            self.tip_racks.pop(index)
        return
        
