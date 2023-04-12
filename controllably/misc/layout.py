# %% -*- coding: utf-8 -*-
"""
This module holds the layout classes in Control.lab.ly.

Classes:
    Deck
    Labware
    Well
"""
# Standard library imports
from __future__ import annotations
import numpy as np
from typing import Optional, Union

# Local application imports
from . import helper
print(f"Import: OK <{__name__}>")

class Well:
    """
    Well represents a single well in a Labware object

    ### Constructor
    Args:
        `labware_info` (dict): dictionary of truncated Labware information (name, slot, reference point)
        `name` (str): name of well
        `details` (dict[str, Union[float, tuple[float]]]): well details
    
    ### Attributes
    - `details` (dict): well details; dictionary of depth, total liquid volume, shape, diameter, x,y,z
    - `name` (str): name of well
    - `reference_point` (tuple[int]): bottom left reference corner of Labware
    
    ### Properties
    - `bottom` (np.ndarray): bottom of well
    - `center` (np.ndarray): center of well
    - `depth` (np.ndarray): well depth
    - `middle` (np.ndarray): middle of well
    - `offset` (np.ndarray): well offset from Labware reference point
    - `top` (np.ndarray): top of well
    
    ### Methods
    - `from_bottom`: offset from bottom of well
    - `from_middle`: offset from middle of well
    - `from_top`: offset from top of well
    """
    
    def __init__(self, 
        labware_info: dict, 
        name: str, 
        details: dict[str, Union[float, tuple[float]]]
    ):
        """
        Instantiate the class

        Args:
            labware_info (dict): dictionary of truncated Labware information (name, slot, reference point)
            name (str): name of well
            details (dict[str, Union[float, tuple[float]]]): well details
        """
        self.details = details  # depth,totalLiquidVolume,shape,diameter,x,y,z
        self.name = name
        self.reference_point = labware_info.get('reference_point', (0,0,0))
        
        self._labware_name = labware_info.get('name','')
        self._labware_slot = labware_info.get('slot','')
        pass
    
    def __repr__(self) -> str:
        return f"{self.name} in {self._labware_name} at Slot {self._labware_slot}" 
    
    # Properties
    @property
    def bottom(self) -> np.ndarray:
        return self.center
    
    @property
    def center(self) -> np.ndarray:
        return np.array(self.reference_point) + self.offset
    
    @property
    def depth(self) -> float:
        return self.details.get('depth', 0)
    
    @property
    def middle(self) -> np.ndarray:
        depth = self.details.get('depth', 0)
        return self.center + np.array((0,0,depth/2))
        
    @property
    def offset(self) -> np.ndarray:
        x = self.details.get('x', 0)
        y = self.details.get('y', 0)
        z = self.details.get('z', 0)
        return np.array((x,y,z))
    
    @property
    def top(self) -> np.ndarray:
        depth = self.details.get('depth', 0)
        return self.center + np.array((0,0,depth))
    
    def from_bottom(self, offset:tuple[float]) -> np.ndarray:
        """
        Offset from bottom of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: bottom of well with offset
        """
        return self.bottom + np.array(offset)
    
    def from_middle(self, offset:tuple[float]) -> np.ndarray:
        """
        Offset from middle of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: middle of well with offset
        """
        return self.middle + np.array(offset)
    
    def from_top(self, offset:tuple[float]) -> np.ndarray:
        """
        Offset from top of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: top of well with offset
        """
        return self.top + np.array(offset)


class Labware:
    """
    Labware represents a single Labware on the Deck

    ### Constructor
    Args:
        `slot` (str): deck slot number
        `bottom_left_coordinates` (tuple[float]): coordinates of bottom left corner of Labware (i.e. reference point)
        `labware_file` (str): filepath of Labware JSON file
        `package` (Optional[str], optional): name of package to look in. Defaults to None.
        
    ### Attributes
    - `details` (dict): dictionary read from Labware file
    - `name` (str): name of Labware
    - `slot` (str): deck slot number
    
    ### Properties
    - `center` (np.ndarray): center of Labware
    - `columns` (dict[str, int]): Labware columns
    - `columns_list` (list[list[int]]): Labware columns as list
    - `dimensions` (np.ndarray): size of Labware
    - `info` (dict): summary of Labware info
    - `reference_point` (np.ndarray): coordinates of bottom left corner of Labware
    - `rows` (dict[str, int]): Labware rows
    - `rows_list` (list[list[int]]): Labware rows as list
    - `wells` (dict[str, Well]): Labware wells
    - `wells_list` (list[Well]): Labware wells as list
    
    ### Methods
    - `at`: alias for `get_well()`
    - `get_well`: get `Well` using its name
    """
    
    def __init__(self, 
        slot: str, 
        bottom_left_coordinates: tuple[float], 
        labware_file: str, 
        package: Optional[str] = None
    ):
        """
        Instantiate the class

        Args:
            slot (str): deck slot number
            bottom_left_coordinates (tuple[float]): coordinates of bottom left corner (i.e. reference point)
            labware_file (str): filepath of Labware JSON file
            package (Optional[str], optional): name of package to look in. Defaults to None.
        """
        self.details = helper.read_json(json_file=labware_file, package=package)
        self.name = self.details.get('metadata',{}).get('displayName', '')
        self._reference_point = tuple(bottom_left_coordinates)
        self.slot = slot
        self._wells = {}
        self._load_wells()
        pass
    
    def __repr__(self) -> str:
        return f"{self.name} at Slot {self.slot}" 
    
    # Properties
    @property
    def center(self) -> np.ndarray:
        dimensions = self.details.get('dimensions',{})
        x = dimensions.get('xDimension', 0)
        y = dimensions.get('yDimension', 0)
        z = dimensions.get('zDimension', 0)
        return self.reference_point, np.array((x/2,y/2,z))
    
    @property
    def columns(self) -> dict[str, int]:
        columns_list = self.columns_list
        return {str(c+1): columns_list[c] for c in range(len(columns_list))}
    
    @property
    def columns_list(self) -> list[list[int]]:
        return self.details.get('ordering', [[]])
    
    @property
    def dimensions(self) -> np.ndarray:
        dimensions = self.details.get('dimensions',{})
        x = dimensions.get('xDimension', 0)
        y = dimensions.get('yDimension', 0)
        z = dimensions.get('zDimension', 0)
        return np.array((x,y,z))

    @property
    def info(self) -> dict[str, Union[str, tuple[float]]]:
        return {'name':self.name, 'reference_point':self.reference_point, 'slot':self.slot}
    
    @property
    def reference_point(self) -> np.ndarray:
        return self._reference_point
    @reference_point.setter
    def reference_point(self, value:tuple[float]):
        self._reference_point = value
        return
    
    @property
    def rows(self) -> dict[str, int]:
        first_column = self.details.get('ordering', [[]])[0]
        rows_list = self.rows_list
        return {w[0]: rows_list[r] for r,w in enumerate(first_column)}
    
    @property
    def rows_list(self) -> list[list[int]]:
        columns = self.columns_list
        return [list(z) for z in zip(*columns)]
       
    @property
    def wells(self) -> dict[str, Well]:
        return self._wells
    
    @property
    def wells_list(self) -> list[Well]:
        return [self._wells[well] for well in self.details.get('wells',{})]

    def at(self, name:str) -> Well:
        """
        Get `Well` using its name.
        Alias for `get_well()`.

        Args:
            name (str): name of well

        Returns:
            Well: `Well` object
        """
        return self.get_well(name=name)
    
    def get_well(self, name:str) -> Well:
        """
        Get `Well` using its name

        Args:
            name (str): name of well

        Returns:
            Well: `Well` object
        """
        return self.wells.get(name)
    
    def _load_wells(self):
        """Load wells into memory"""
        wells = self.details.get('wells',{})
        for well in wells:
            self._wells[well] = Well(labware_info=self.info, name=well, details=wells[well])
        return


class Deck:
    """
    Deck object

    ### Constructor
    Args:
        `layout_file` (Optional[str], optional): filepath of deck layout JSON file. Defaults to None.
        `package` (Optional[str], optional): name of package to look in. Defaults to None.
    
    ### Attributes
    - `details` (dict): details read from layout file
    - `exclusion_zones` (dict): dictionary of cuboidal zones to avoid
    - `names` (dict): labels for deck slots
    
    ### Properties
    - `slots` (dict[str, Labware]): loaded Labware in slots
    
    ### Methods
    - `at`: alias for `get_slot()`, with mixed input
    - `get_slot`: get Labware in slot using slot id or name
    - `is_excluded`: checks and returns whether the coordinates are in an excluded region
    - `load_labware`: load Labware into slot
    - `load_layout`: load deck layout from layout file
    - `remove_labware`: remove Labware in slot using slot id or name
    """
    
    def __init__(self, layout_file:Optional[str] = None, package:Optional[str] = None):
        """
        Instantiate the class

        Args:
            layout_file (Optional[str], optional): filepath of deck layout JSON file. Defaults to None.
            package (Optional[str], optional): name of package to look in. Defaults to None.
        """
        self.details = {}
        self._slots = {}
        self.names = {}
        self.exclusion_zones = {}
        self.load_layout(layout_file=layout_file, package=package)
        pass
    
    def __repr__(self) -> str:
        labwares = [''] + [repr(labware) for labware in self.slots.values()]
        labware_string = '\n'.join(labwares)
        return f"Deck with Labwares:{labware_string}" 
    
    @property
    def slots(self) -> dict[str, Labware]:
        return self._slots
    
    def at(self, slot:Union[int, str]) -> Optional[Labware]:
        """
        Get Labware in slot using slot id or name, with mixed input.
        Alias for `get_slot()`.

        Args:
            slot (Union[int, str]): id or name of slot

        Returns:
            Optional[Labware]: Labware in slot
        """
        if type(slot) == int:
            return self.get_slot(index=slot)
        elif type(slot) == str:
            return self.get_slot(name=slot)
        print("Input a valid slot id or name of Labware in slot.")
        return
    
    def get_slot(self, index:Optional[int] = None, name:Optional[str] = None) -> Optional[Labware]:
        """
        Get Labware in slot using slot id or name

        Args:
            index (Optional[int], optional): slot id number. Defaults to None.
            name (Optional[str], optional): nickname of Labware. Defaults to None.

        Raises:
            ValueError: Please input either slot id or name

        Returns:
            Optional[Labware]: Labware in slot
        """
        if not any((index, name)) or all((index, name)):
            raise ValueError('Please input either slot id or name.')
        if index is None and name is not None:
            index = self.names.get(name)
        return self._slots.get(str(index))
    
    def is_excluded(self, coordinates:tuple[float]) -> bool:
        """
        Checks and returns whether the coordinates are in an excluded region.

        Args:
            coordinates (tuple[float]): target coordinates

        Returns:
            bool: whether the coordinates are in an excluded region
        """
        coordinates = np.array(coordinates)
        for key, value in self.exclusion_zones.items():
            l_bound, u_bound = value
            if key == 'boundary':
                if any(np.less_equal(coordinates, l_bound)) and any(np.greater_equal(coordinates, u_bound)):
                    print(f"Deck limits reached! {value}")
                    return True
                continue
            if all(np.greater_equal(coordinates, l_bound)) and all(np.less_equal(coordinates, u_bound)):
                name = [k for k,v in self.names.items() if str(v)==key][0] if key in self.names.values() else f'Labware in Slot {key}'
                print(f"{name} is in the way! {value}")
                return True
        return False
    
    def load_labware(self, 
        slot: int, 
        labware_file: str, 
        package: Optional[str] = None, 
        name: Optional[str] = None, 
        exclusion_height: Optional[float] = None
    ):
        """
        Load Labware into slot

        Args:
            slot (int): slot id
            labware_file (str): filepath Labware JSON file
            package (Optional[str], optional): name of package to look in. Defaults to None.
            name (Optional[str], optional): nickname of Labware. Defaults to None.
            exclusion_height (Optional[float], optional): height clearance from top of Labware. Defaults to None.
        """
        if name:
            self.names[name] = slot
        bottom_left_coordinates = tuple( self.details.get('reference_points',{}).get(str(slot),(0,0,0)) )
        labware = Labware(slot=str(slot), bottom_left_coordinates=bottom_left_coordinates, labware_file=labware_file, package=package)
        self._slots[str(slot)] = labware
        if exclusion_height is not None:
            top_right_coordinates= tuple(map(sum, zip(bottom_left_coordinates, labware.dimensions, (0,0,exclusion_height))))
            self.exclusion_zones[str(slot)] = (bottom_left_coordinates, top_right_coordinates)
        return
    
    def load_layout(
        self, 
        layout_file: Optional[str] = None, 
        layout_dict: Optional[dict] = None, 
        package: Optional[str] = None, 
        labware_package: Optional[str] = None
    ):
        """
        Load deck layout from layout file

        Args:
            layout_file (Optional[str], optional): filepath of deck layout JSON file. Defaults to None.
            layout_dict (Optional[dict], optional): layout details. Defaults to None.
            package (Optional[str], optional): name of package to look in for layout file. Defaults to None.
            labware_package (Optional[str], optional): name of package to look in for Labware file. Defaults to None.

        Raises:
            Exception: lease input either `layout_file` or `layout_dict`
        """
        if layout_file is None and layout_dict is None:
            return
        elif layout_file is not None and layout_dict is not None:
            raise Exception("Please input either `layout_file` or `layout_dict`.")
            print()
        elif layout_file is not None:
            self.details = helper.read_json(json_file=layout_file, package=package)
        else:
            self.details = layout_dict
        
        slots = self.details.get('slots', {})
        for slot in sorted(list(slots)):
            info = slots[slot]
            name = info.get('name')
            labware_file = info.get('filepath','')
            exclusion_height = info.get('exclusion_height', -1)
            exclusion_height = exclusion_height if exclusion_height >= 0 else None
            self.load_labware(slot=slot, name=name, exclusion_height=exclusion_height, labware_file=labware_file, package=labware_package)
        return

    def remove_labware(self, index:Optional[int] = None, name:Optional[str] = None):
        """
        Remove Labware in slot using slot id or name

        Args:
            index (Optional[int], optional): slot id. Defaults to None.
            name (Optional[str], optional): nickname of Labware. Defaults to None.

        Raises:
            Exception: Please input either slot id or name
        """
        if not any((index, name)) or all((index, name)):
            raise Exception('Please input either slot id or name.')
        if index is None and name is not None:
            index = self.names.get(name)
        elif index is not None and name is None:
            name = [k for k,v in self.names.items() if v==index][0]
        self.names.pop(name)
        self._slots.pop(str(index))
        self.exclusion_zones.pop(str(index))
        return
