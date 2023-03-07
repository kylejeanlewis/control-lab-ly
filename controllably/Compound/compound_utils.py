# %% -*- coding: utf-8 -*-
"""
Created: Tue 2023/02/12 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports

# Third party imports

# Local application imports
from ..misc import Deck, Helper
print(f"Import: OK <{__name__}>")

class CompoundSetup(object):
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
        if self.isConnected():
            print("Hardware / connection ok!")
        elif ignore_connections:
            print("Connection(s) not established. Ignoring...")
        else:
            print("Check hardware / connection!")
            return
        
        # Test tools
        for component in self.components.values():
            if '_diagnostic' in dir(component):
                component._diagnostic()
        print('Ready!')
        return
    
    def isBusy(self):
        """
        Checks whether the setup is busy

        Returns:
            bool: whether the setup is busy
        """
        return any([component.isBusy() for component in self.components.values() if 'isBusy' in dir(component)])
    
    def isFeasible(self, coordinates):
        """
        Checks whether the coordinates is feasible

        Returns:
            bool: whether the coordinates is feasible
        """
        return not self.deck.is_excluded(coordinates)
    
    def isConnected(self):
        """
        Checks whether the setup is connected

        Returns:
            bool: whether the setup us connected
        """
        return all([component.isConnected() for component in self.components.values()])
    
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
        Reset setup
        """
        return
 