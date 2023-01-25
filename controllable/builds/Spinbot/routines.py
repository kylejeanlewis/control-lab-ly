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

CNC_SPEED = 250
CONFIG_FILE = "config.yaml"

class SpinbotSetup(object):
    """
    Spinbot routines

    Args:
        config (str, optional): filename of config .yaml file. Defaults to CONFIG_FILE.
        config_option (int, optional): configuration option from config file. Defaults to 0.
        ignore_connections (bool, optional): whether to ignore connections and run methods. Defaults to False.
    """
    def __init__(self, config=CONFIG_FILE, config_option=0, ignore_connections=False, **kwargs):
        self.components = {}
        self.deck = Deck()
        self.positions = {}
        self._config = Helper.read_plans(config, config_option, __name__)
        self._flags = {
            'at_rest': False
        }
        self._connect(ignore_connections=ignore_connections)
        self.loadDeck()
        pass
    
    @property
    def liquid(self):
        return self.components.get('transfer')
    
    @property
    def mover(self):
        return self.components.get('move')
    
    def _connect(self, diagnostic=True, ignore_connections=False):
        """
        Make connections to the respective components

        Args:
            diagnostic (bool, optional): whether to run diagnostic to check equipment. Defaults to True.
            ignore_connections (bool, optional): whether to ignore connections and run methods. Defaults to False.
        """
        for component in self._config:
            if component not in ['make','move','transfer']:
                continue
            component_module = component.split('_')[0].title()
            component_class = Helper.get_class(component_module, self._config[component]['class'])
            self.components[component] = component_class(**self._config[component]['settings'])
        
        if 'labelled_positions' in self._config.keys():
            self.labelPositions(self._config['labelled_positions'])

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
        self.mover.safeMoveTo(coordinates, descent_speed_fraction=0.2)
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
        if 'eject' in dir(self.liquid) and not self.liquid.isTipOn(): # or not self.liquid.tip_length:
            print("[aspirate] There is no tip attached.")
            return
        offset = self.liquid.channels[channel].offset if 'channels' in dir(self.liquid) else self.liquid.offset
        self.align(coordinates=coordinates, offset=offset)
        self.liquid.aspirate(volume=volume, speed=speed, channel=channel)
        return
    
    def attachTip(self, tip_length=80, channel=None):
        """
        Attach new pipette tip

        Args:
            tip_length (int, optional): length of pipette tip. Defaults to 80.
            channel (int, optional): channel to use. Defaults to None.
        """
        next_tip_location = self.positions.get('pipette_tips').pop(0)
        return self.attachTipAt(next_tip_location, tip_length=tip_length, channel=channel)
    
    def attachTipAt(self, coordinates:tuple, tip_length=80, channel=None):
        """
        Attach new pipette tip from specified location

        Args:
            coordinates (tuple): coordinates of pipette tip
            tip_length (int, optional): length of pipette tip. Defaults to 80.
            channel (int, optional): channel to use. Defaults to None.
        """
        if 'eject' not in dir(self.liquid):
            print("'attachTip' method not available.")
            return
        if self.liquid.isTipOn():# or self.liquid.tip_length:
            print("Please eject current tip before attaching new tip.")
            return
        self.mover.safeMoveTo(coordinates, descent_speed_fraction=0.2)
        self.mover.move('z', -20, speed_fraction=0.01)
        time.sleep(3)
        self.liquid.tip_length = tip_length
        self.mover.implement_offset = tuple(np.array(self.mover.implement_offset) + np.array([0,0,-tip_length]))
        self.mover.move('z', 20+tip_length, speed_fraction=0.2)
        time.sleep(1)
        return
    
    def dispenseAt(self, coordinates, volume, speed=None, channel=None, **kwargs):
        """
        Dispense specified volume at desired location, at target speed

        Args:
            coordinates (tuple): coordinates of desired location
            volume (int, or float): volume in uL
            speed (int, optional): speed to dispense at (uL/s). Defaults to None.
            channel (int, optional): channel to use. Defaults to None.
        """
        if 'eject' in dir(self.liquid) and not self.liquid.isTipOn(): # or not self.liquid.tip_length:
            print("[dispense] There is no tip attached.")
            return
        offset = self.liquid.channels[channel].offset if 'channels' in dir(self.liquid) else self.liquid.offset
        self.align(coordinates=coordinates, offset=offset)
        self.liquid.dispense(volume=volume, speed=speed, channel=channel)
        return
    
    def ejectTip(self, channel=None):
        """
        Eject the pipette tip at the specified location

        Args:
            channel (int, optional): channel to use. Defaults to None.
        """
        bin_location = self.positions.get('bin')
        return self.ejectTipAt(bin_location, channel=channel)
    
    def ejectTipAt(self, coordinates, channel=None):
        """
        Eject the pipette tip at the specified location

        Args:
            coordinates (tuple): coordinate of where to eject tip
            channel (int, optional): channel to use. Defaults to None.
        """
        if 'eject' not in dir(self.liquid):
            print("'ejectTip' method not available.")
            return
        if not self.liquid.isTipOn(): # or not self.liquid.tip_length:
            print("There is currently no tip to eject.")
            return
        self.mover.safeMoveTo(coordinates, descent_speed_fraction=0.2)
        time.sleep(1)
        self.liquid.eject()
        tip_length = self.liquid.tip_length
        self.mover.implement_offset = tuple(np.array(self.mover.implement_offset) - np.array([0,0,-tip_length]))
        self.liquid.tip_length = 0
        return
    
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
    
    def loadDeck(self):
        """
        Load the deck layout from JSON file
        """
        self.deck.load_layout(self._config.get('deck'), __name__)
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
        self.mover.safeMoveTo(rest_coordinates)
        self._flags['at_rest'] = True
        return
    