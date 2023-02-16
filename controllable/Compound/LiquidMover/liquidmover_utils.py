# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import numpy as np
import time

# Third party imports

# Local application imports
from ...misc import Deck, Helper
print(f"Import: OK <{__name__}>")

TIP_APPROACH_HEIGHT = 12

class LiquidMoverSetup(object):
    """
    Liquid Mover Setup routines

    Args:
        config (str): filename of config .yaml file
        config_option (int, optional): configuration option from config file. Defaults to 0.
        layout (str, optional): filename of config .yaml file. Defaults to None.
        layout_dict (dict, optional): dictionary of layout. Defaults to None.
        ignore_connections (bool, optional): whether to ignore connections and run methods. Defaults to False.
    """
    def __init__(self, config:str = None, layout:str = None, component_config:dict = None, layout_dict:dict = None, ignore_connections:bool = False, **kwargs):
        self.components = {}
        self.deck = Deck()
        self.positions = {}
        self._config = Helper.get_plans(config) if config is not None else component_config
        self._flags = {
            'at_rest': False
        }
        self._connect(ignore_connections=ignore_connections)
        self.loadDeck(layout, layout_dict)
        pass
    
    @property
    def liquid(self):
        return self.components.get('liquid')
    
    @property
    def mover(self):
        return self.components.get('mover')
    
    def _connect(self, diagnostic=True, ignore_connections=False):
        """
        Make connections to the respective components

        Args:
            diagnostic (bool, optional): whether to run diagnostic to check equipment. Defaults to True.
            ignore_connections (bool, optional): whether to ignore connections and run methods. Defaults to False.
        """
        self.components = Helper.load_components(self._config)
        self.labelPositions(self._config.get('labelled_positions', {}))

        if diagnostic:
            self._run_diagnostic(ignore_connections)
        return
    
    def _run_diagnostic(self, ignore_connections=False):
        """
        Run diagnostic test actions to see if equipment working as expected

        Args:
            ignore_connections (bool, optional): whether to ignore connections and run methods. Defaults to False.
        """
        connects = [self.mover.isConnected(), self.liquid.isConnected()]
        if all(connects):
            print("Hardware / connection ok!")
        elif ignore_connections:
            print("Connection(s) not established. Ignoring...")
        else:
            print("Check hardware / connection!")
            return
        
        # Test tools
        self.mover._diagnostic()
        self.rest()
        self.liquid._diagnostic()
        print('Ready!')
        return

    def align(self, coordinates:tuple, offset=(0,0,0)):
        """
        Align the end effector to the specified coordinates, while considering any addition offset

        Args:
            coordinates (tuple): coordinates of desired location
            offset (tuple, optional): x,y,z offset from tool tip. Defaults to (0,0,0).
        """
        coordinates = np.array(coordinates) - np.array(offset)
        if not self.mover.isFeasible(coordinates, transform=True, tool_offset=True):
            print(f"Infeasible toolspace coordinates! {coordinates}")
        self.mover.safeMoveTo(coordinates, ascent_speed_fraction=0.2, descent_speed_fraction=0.2)
        self._flags['at_rest'] = False
        return
    
    def aspirateAt(self, coordinates:tuple, volume, speed=None, channel=None, **kwargs):
        """
        Aspirate specified volume at desired location, at target speed

        Args:
            coordinates (tuple): coordinates of desired location
            volume (int, or float): volume in uL
            speed (int, optional): speed to aspirate at (uL/s). Defaults to None.
            channel (int, optional): channel to use. Defaults to None.
        """
        if 'eject' in dir(self.liquid) and not self.liquid.isTipOn():
            print("[aspirate] There is no tip attached.")
            return
        offset = self.liquid.channels[channel].offset if 'channels' in dir(self.liquid) else self.liquid.offset
        self.align(coordinates=coordinates, offset=offset)
        self.liquid.aspirate(volume=volume, speed=speed, channel=channel)
        return
    
    def attachTip(self, slot='tip_rack', tip_length=80, channel=None):
        """
        Attach new pipette tip

        Args:
            slot (str, optional): name of slot with pipette tips. Defaults to 'tip_rack'.
            tip_length (int, optional): length of pipette tip. Defaults to 80.
            channel (int, optional): channel to use. Defaults to None.
        
        Returns:
            tuple: coordinates of top of tip rack well
        """
        next_tip_location, tip_length = self.positions.get(slot, [(0,0,0), tip_length]).pop(0)
        return self.attachTipAt(next_tip_location, tip_length=tip_length, channel=channel)
    
    def attachTipAt(self, coordinates:tuple, tip_length=80, channel=None):
        """
        Attach new pipette tip from specified location

        Args:
            coordinates (tuple): coordinates of pipette tip
            tip_length (int, optional): length of pipette tip. Defaults to 80.
            channel (int, optional): channel to use. Defaults to None.
            
        Returns:
            tuple: coordinates of attach tip location
        """
        if 'eject' not in dir(self.liquid):
            print("'attachTip' method not available.")
            return coordinates
        if self.liquid.isTipOn():
            print("Please eject current tip before attaching new tip.")
            return coordinates
        self.align(coordinates)
        self.mover.move('z', -TIP_APPROACH_HEIGHT, speed_fraction=0.01)
        time.sleep(3)
        self.liquid.tip_length = tip_length
        self.mover.implement_offset = tuple(np.array(self.mover.implement_offset) + np.array([0,0,-tip_length]))
        self.mover.move('z', TIP_APPROACH_HEIGHT+tip_length, speed_fraction=0.2)
        time.sleep(1)
        self.liquid.setFlag('tip_on', True)
        if not self.liquid.isTipOn():
            tip_length = self.liquid.tip_length
            self.mover.implement_offset = tuple(np.array(self.mover.implement_offset) - np.array([0,0,-tip_length]))
            self.liquid.tip_length = 0
            self.liquid.setFlag('tip_on', False)
        self._temp_tip_home = coordinates
        return coordinates
    
    def dispenseAt(self, coordinates, volume, speed=None, channel=None, **kwargs):
        """
        Dispense specified volume at desired location, at target speed

        Args:
            coordinates (tuple): coordinates of desired location
            volume (int, or float): volume in uL
            speed (int, optional): speed to dispense at (uL/s). Defaults to None.
            channel (int, optional): channel to use. Defaults to None.
        """
        if 'eject' in dir(self.liquid) and not self.liquid.isTipOn():
            print("[dispense] There is no tip attached.")
            return
        offset = self.liquid.channels[channel].offset if 'channels' in dir(self.liquid) else self.liquid.offset
        self.align(coordinates=coordinates, offset=offset)
        self.liquid.dispense(volume=volume, speed=speed, channel=channel)
        return
    
    def ejectTip(self, slot='bin', channel=None):
        """
        Eject the pipette tip at the specified location

        Args:
            slot (str, optional): name of slot with bin. Defaults to 'bin'.
            channel (int, optional): channel to use. Defaults to None.
            
        Raises:
            Exception: No bin location specified.
            
        Returns:
            tuple: coordinates of top of bin well
        """
        bin_location,_ = self.positions.get(slot, [(None, 0)])[0]
        if bin_location is None:
            raise Exception("No bin location specified.")
        return self.ejectTipAt(bin_location, channel=channel)
    
    def ejectTipAt(self, coordinates, channel=None):
        """
        Eject the pipette tip at the specified location

        Args:
            coordinates (tuple): coordinate of where to eject tip
            channel (int, optional): channel to use. Defaults to None.
            
        Returns:
            tuple: coordinates of eject tip location
        """
        if 'eject' not in dir(self.liquid):
            print("'ejectTip' method not available.")
            return coordinates
        if not self.liquid.isTipOn():
            print("There is currently no tip to eject.")
            tip_length = self.liquid.tip_length
            self.mover.implement_offset = tuple(np.array(self.mover.implement_offset) - np.array([0,0,-tip_length]))
            self.liquid.tip_length = 0
            return coordinates
        self.align(coordinates=coordinates)
        time.sleep(1)
        self.liquid.eject()
        tip_length = self.liquid.tip_length
        self.mover.implement_offset = tuple(np.array(self.mover.implement_offset) - np.array([0,0,-tip_length]))
        self.liquid.tip_length = 0
        self.liquid.setFlag('tip_on', False)
        return coordinates
    
    def isBusy(self):
        """
        Checks whether the setup is busy

        Returns:
            bool: whether the setup is busy
        """
        return any([self.liquid.isBusy()])
    
    def isConnected(self):
        """
        Checks whether the setup is connected

        Returns:
            bool: whether the setup us connected
        """
        return all([component.isConnected() for component in self.components.values])
    
    def labelPositions(self, names_coords={}, overwrite=False):
        """
        Set predefined labelled positions

        Args:
            names_coords (dict, optional): name,coordinate key-values of labelled positions. Defaults to {}.
            overwrite (bool, optional): whether to overwrite existing positions that has the same key/name. Defaults to False.
        """
        for name,coordinates in names_coords.items():
            if name not in self.positions.keys() or overwrite:
                self.positions[name] = coordinates
            else:
                print(f"The position '{name}' has already been defined at: {self.positions[name]}")
        return
    
    def loadDeck(self, layout:str = None, layout_dict:dict = None):
        """
        Load the deck layout from JSON file
        
        Args:
            layout (str, optional): filename of layout .json file. Defaults to None.
            layout_dict (dict, optional): dictionary of layout. Defaults to None.
        """
        self.deck.load_layout(layout, layout_dict)
        for name in self.deck.names:
            self.positions[name] = [(well.top, well.depth) for well in self.deck.get_slot(name=name).wells_list]
        return
    
    def reset(self):
        """
        Alias for rest
        """
        # Empty liquids
        self.rest()
        return
    
    def rest(self):
        """
        Go back to the rest position, or home
        """
        if self._flags['at_rest']:
            return
        rest_coordinates = self.positions.get('rest', self.mover._transform_out((self.mover.home_coordinates)))
        self.align(coordinates=rest_coordinates)
        self._flags['at_rest'] = True
        return
    
    def returnTip(self):
        """
        Return current tip to its original rack position

        Returns:
            tuple: coordinates of eject tip location
        """
        coordinates = self.__dict__.pop('_temp_tip_home')
        return self.ejectTipAt(coordinates=(*coordinates[:2],coordinates[2]-18))
    