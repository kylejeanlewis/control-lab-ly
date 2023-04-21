# %% -*- coding: utf-8 -*-
"""
This module holds the base class for compound setups that combine multiple basic tools.

Classes:
    CompoundSetup (ABC)
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

# Local application imports
from ..misc import Factory, Layout
print(f"Import: OK <{__name__}>")

class CompoundSetup(ABC):
    """
    Abstract Base Class (ABC) for CompoundSetup objects (i.e. compound tools that combine multiple basic tools).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Args:
        `config` (Optional[str], optional): filename of config .yaml file. Defaults to None.
        `layout` (Optional[str], optional): filename of layout .json file. Defaults to None.
        `component_config` (Optional[dict], optional): configuration dictionary of component settings. Defaults to None.
        `layout_dict` (Optional[dict], optional): dictionary of layout. Defaults to None.
        `components` (Optional[dict], optional): dictionary of components. Defaults to None.
        `diagnostic` (bool, optional): whether to run diagnostic tests to check equipment. Defaults to False.
        `verbose` (bool, optional): verbosity of class. Defaults to False.

    ### Attributes
    - `components` (dict): dictionary of component parts
    - `deck` (Layout.Deck): Deck object for workspace
    - `flags` (dict[str, bool]): keywords paired with boolean flags
    - `positions` (dict[str, tuple[float]]): specified position names and values
    - `verbose` (bool): verbosity of class
    
    ### Methods
    #### Abstract
    - `reset`: reset the setup
    #### Public
    - `isBusy`: checks and returns whether the setup is busy
    - `isConnected`: checks and returns whether the setup is connected
    - `isFeasible`: checks and returns whether the target coordinates is feasible
    - `loadDeck`: load Labware objects onto the deck from file or dictionary
    - `resetFlags`: reset all flags to class attribute `_default_flags`
    - `setFlag`: set flags by using keyword arguments
    - `setPosition`: set predefined positions using keyword arguments
    """
    
    _default_flags: dict[str, bool] = {}
    def __init__(self, 
        config: Optional[str] = None, 
        layout: Optional[str] = None, 
        component_config: Optional[dict] = None, 
        layout_dict: Optional[dict] = None,
        components: Optional[dict] = None,
        diagnostic: bool = False,
        verbose: bool = False,
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
            diagnostic (bool, optional): whether to run diagnostic tests to check equipment. Defaults to False.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.components = {} if components is None else components
        self.deck = Layout.Deck()
        self.flags = self._default_flags.copy()
        self.positions = {}
        self.verbose = verbose
        self._config = Factory.get_plans(config) if config is not None else component_config

        self._connect(diagnostic=diagnostic)
        self.loadDeck(layout_file=layout, layout_dict=layout_dict)
        pass
    
    @abstractmethod
    def reset(self, *args, **kwargs):
        """Reset the setup"""
    
    def isBusy(self) -> bool:
        """
        Checks and returns whether the setup is busy
        
        Returns:
            bool: whether the setup is busy
        """
        return any([component.isBusy() for component in self.components.values() if 'isBusy' in dir(component)])
    
    def isConnected(self) -> bool:
        """
        Checks and returns whether the setup is connected

        Returns:
            bool: whether the setup is connected
        """
        return all([component.isConnected() for component in self.components.values() if 'isConnected' in dir(component)])
    
    def isFeasible(self, coordinates:tuple[float]) -> bool:
        """
        Checks and returns whether the target coordinates is feasible
        
        Args:
            coordinates (tuple[float]): target coordinates

        Returns:
            bool: whether the coordinates is feasible
        """
        return not self.deck.is_excluded(coordinates)
    
    def loadDeck(self, layout_file:Optional[str] = None, layout_dict:Optional[dict] = None):
        """
        Load Labware objects onto the deck from file or dictionary
        
        Args:
            layout_file (Optional[str], optional): filename of layout .json file. Defaults to None.
            layout_dict (Optional[dict], optional): dictionary of layout. Defaults to None.
        """
        self.deck.load_layout(layout_file=layout_file, layout_dict=layout_dict)
        for name in self.deck.names:
            self.positions[name] = [(well.top, well.depth) for well in self.deck.get_slot(name=name).wells_list]
        return
    
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = self._default_flags.copy()
        return
    
    def setFlag(self, **kwargs):
        """
        Set flags by using keyword arguments

        Kwargs:
            key, value: (flag name, boolean) pairs
        """
        if not all([type(v)==bool for v in kwargs.values()]):
            raise ValueError("Ensure all assigned flag values are boolean.")
        for key, value in kwargs.items():
            self.flags[key] = value
        return
    
    def setPosition(self, overwrite:bool = False, **kwargs):
        """
        Set predefined positions using keyword arguments

        Args:
            overwrite (bool, optional): whether to overwrite existing position. Defaults to False.
        
        Kwargs:
            key, value: (position name, float value) pairs
        """
        for key, value in kwargs.items():
            if key not in self.positions or overwrite:
                self.positions[key] = value
            elif not overwrite:
                print(f"Previously saved height '{key}': {self.positions[key]}\n")
                print(f"New height received: {value}")
                if input('Overwrite? [y/n]').lower() == 'n':
                    continue
                self.positions[key] = value
        return
    
    # Protected method(s)
    def _connect(self, diagnostic:bool = False):
        """
        Make connections to the respective components

        Args:
            diagnostic (bool, optional): whether to run diagnostic tests to check equipment. Defaults to False.
        """
        components = Factory.load_components(self._config)
        self.components.update(components)
        labelled_positions = self._config.get('labelled_positions', {})
        self.setPosition(**labelled_positions)
        if diagnostic:
            self._diagnostic()
        return
    
    def _diagnostic(self):
        """Run diagnostic test"""
        for component in self.components.values():
            print(component.__dict__.get('connection_details', {}))
            if not component.isConnected():
                print("Check hardware / connection!")
                continue
            print("Hardware / connection ok!")
            if '_diagnostic' in dir(component):
                component._diagnostic()
        print('Ready!')
        return
    