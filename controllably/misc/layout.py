# %% -*- coding: utf-8 -*-
"""
Adapted from @Pablo's labware code

Created: Tue 2023/01/25 17:13:35
@author: Chang Jie

Notes / actionables:
-
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
    Well object

    Args:
        labware_info (dict): labware info of name, slot, reference point
        name (str): name of well
        details (dict): details of well
    """
    def __init__(self, 
        labware_info: dict, 
        name: str, 
        details: dict[str, Union[float, tuple[float]]]
    ):
        self.details = details  # depth,totalLiquidVolume,shape,diameter,x,y,z
        self.name = name
        self.reference_point = labware_info.get('reference_point', (0,0,0))
        
        self._labware_name = labware_info.get('name','')
        self._labware_slot = labware_info.get('slot','')
        pass
    
    def __repr__(self) -> str:
        return f"{self.name} in {self._labware_name} at Slot {self._labware_slot}" 
    
    @property
    def center(self) -> np.ndarray:
        """
        Center of well bottom

        Returns:
            tuple: coordinates for center of well bottom
        """
        return np.array(self.reference_point) + self.offset
    
    @property
    def depth(self) -> float:
        """
        Depth of well

        Returns:
            float: depth of well in mm
        """
        return self.details.get('depth', 0)
    
    @property
    def offset(self) -> np.ndarray:
        """
        Well offset from labware reference point

        Returns:
            tuple: offset vector
        """
        x = self.details.get('x', 0)
        y = self.details.get('y', 0)
        z = self.details.get('z', 0)
        return np.array((x,y,z))
    
    @property
    def bottom(self) -> np.ndarray:
        """
        Bottom of well

        Returns:
            tuple: coordinates for bottom of well
        """
        return self.center
    
    @property
    def middle(self) -> np.ndarray:
        """
        Middle of well

        Returns:
            tuple: coordinates for middle of well
        """
        depth = self.details.get('depth', 0)
        return self.center + np.array((0,0,depth/2))
    
    @property
    def top(self) -> np.ndarray:
        """
        Top of well

        Returns:
            tuple: coordinates for top of well
        """
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
    Labware object

    Args:
        slot (str): deck slot
        bottom_left_coordinates (tuple): coordinates of bottom left corner (reference point)
        labware_file (str): JSON filepath for labware
        package (str, optional): name of package to look in. Defaults to None.
    """
    def __init__(self, 
        slot: str, 
        bottom_left_coordinates: tuple[float], 
        labware_file: str, 
        package: Optional[str] = None
    ):
        self.details = helper.read_json(json_file=labware_file, package=package)
        self.name = self.details.get('metadata',{}).get('displayName', '')
        self.reference_point = np.array(bottom_left_coordinates)
        self.slot = slot
        self._wells = {}
        self.load_wells()
        pass
    
    def __repr__(self) -> str:
        return f"{self.name} at Slot {self.slot}" 
    
    @property
    def info(self) -> dict[str, Union[str, tuple[float]]]:
        """
        Summary of labware info

        Returns:
            dict: dictionary of name, reference point, and slot
        """
        return {'name':self.name, 'reference_point':self.reference_point, 'slot':self.slot}
    
    @property
    def center(self) -> np.ndarray:
        """
        Center of labware

        Returns:
            tuple: coordinates of the center of labware
        """
        dimensions = self.details.get('dimensions',{})
        x = dimensions.get('xDimension', 0)
        y = dimensions.get('yDimension', 0)
        z = dimensions.get('zDimension', 0)
        return self.reference_point, np.array((x/2,y/2,z))
    
    @property
    def columns(self) -> dict[str, int]:
        """
        Labware columns

        Returns:
            dict: dictionary of labelled columns lists
        """
        columns_list = self.columns_list
        return {str(c+1): columns_list[c] for c in range(len(columns_list))}
    
    @property
    def columns_list(self) -> list[list[int]]:
        """
        Labware columns as list

        Returns:
            list: list of columns
        """
        return self.details.get('ordering', [[]])
    
    @property
    def dimensions(self) -> np.ndarray:
        """
        Size of labware

        Returns:
            tuple: coordinates of the center of labware
        """
        dimensions = self.details.get('dimensions',{})
        x = dimensions.get('xDimension', 0)
        y = dimensions.get('yDimension', 0)
        z = dimensions.get('zDimension', 0)
        return np.array((x,y,z))
    
    @property
    def rows(self) -> dict[str, int]:
        """
        Labware rows

        Returns:
            dict: dictionary of labelled rows lists
        """
        first_column = self.details.get('ordering', [[]])[0]
        rows_list = self.rows_list
        return {w[0]: rows_list[r] for r,w in enumerate(first_column)}
    
    @property
    def rows_list(self) -> list[list[int]]:
        """
        Labware rows as list

        Returns:
            list: list of rows
        """
        columns = self.columns_list
        return [list(z) for z in zip(*columns)]
       
    @property
    def wells(self) -> dict[str, Well]:
        """
        Labware wells

        Returns:
            dict: dictionary of labelled wells
        """
        return self._wells
    
    @property
    def wells_list(self) -> list[Well]:
        """
        Labware wells as list

        Returns:
            list: list of wells
        """
        return [self._wells[well] for well in self.details.get('wells',{})]

    def at(self, name:str) -> Well:
        return self.get_well(name=name)
    
    def get_well(self, name:str) -> Well:
        """
        Get well using name

        Args:
            name (str): name of well

        Returns:
            Well: well object
        """
        return self.wells.get(name)
    
    def load_wells(self):
        """
        Load wells into memory
        """
        wells = self.details.get('wells',{})
        for well in wells:
            self._wells[well] = Well(labware_info=self.info, name=well, details=wells[well])
        return


class Deck:
    """
    Deck object

    Args:
        layout_file (str, optional): JSON filepath of deck layout. Defaults to None.
        package (str, optional): name of package to look in. Defaults to None.
    """
    def __init__(self, layout_file:Optional[str] = None, package:Optional[str] = None):
        self.details = {}
        self._slots = {}
        self.names = {}
        self.exclusion_zones = {}
        self.load_layout(layout_file=layout_file, package=package)
        pass
    
    def __repr__(self) -> str:
        labwares = [''] + [repr(labware) for labware in self.slots.values()]
        labware_string = '\n'.join(labwares)
        return f"Deck with labwares:{labware_string}" 
    
    @property
    def slots(self) -> dict[str, Labware]:
        """
        Loaded Labware in slots

        Returns:
            dict: dictionary of labware in slots
        """
        return self._slots
    
    def at(self, slot:Union[int, str]) -> Optional[Labware]:
        """
        Alias for Deck.get_slot, with mixed input

        Args:
            slot (int/str): index or name of slot

        Returns:
            Labware: Labware in slot
        """
        if type(slot) == int:
            return self.get_slot(index=slot)
        elif type(slot) == str:
            return self.get_slot(name=slot)
        print("Input a valid index or name of Labware in slot.")
        return
    
    def get_slot(self, index:Optional[int] = None, name:Optional[str] = None) -> Optional[Labware]:
        """
        Get labware in slot using index or name

        Args:
            index (int, optional): slot index number. Defaults to None.
            name (str, optional): nickname of labware. Defaults to None.

        Raises:
            Exception: Inputs 'index' and 'name' cannot be both 'None'

        Returns:
            Labware: Labware in slot
        """
        if not any((index, name)) or all((index, name)):
            raise Exception('Please input either slot index or name')
        if index is None and name is not None:
            index = self.names.get(name)
        return self._slots.get(str(index))
    
    def is_excluded(self, coordinates:tuple[float]) -> bool:
        """
        Determine whether the coordinates are in an excluded region.

        Args:
            coordinates (tuple): tuple of given coordinates

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
            slot (int): slot index
            labware_file (str): JSON filepath of labware to be loaded
            package (str, optional): name of package to look in. Defaults to None.
            name (str, optional): nickname of labware. Defaults to None.
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
        Load deck layout

        Args:
            layout_file (str, optional): JSON filepath of deck layout. Defaults to None.
            layout_dict (dict, optional): dictionary of layout. Defaults to None.
            package (str, optional): name of package to look in. Defaults to None.
            labware_package (str, optional): name of package to look in for labware file. Defaults to None.
        """
        if (layout_file is None) == (layout_dict is None):
            raise Exception("Please input either `layout_file` or `layout_dict`")
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
        Remove labware in slot using index or name

        Args:
            index (int, optional): slot index number. Defaults to None.
            name (str, optional): nickname of labware. Defaults to None.

        Raises:
            Exception: Inputs 'index' and 'name' cannot be both 'None'
        """
        if not any((index, name)) or all((index, name)):
            raise Exception('Please input either slot index or name')
        if index is None and name is not None:
            index = self.names.get(name)
        elif index is not None and name is None:
            name = [k for k,v in self.names.items() if v==index][0]
        self.names.pop(name)
        self._slots.pop(str(index))
        self.exclusion_zones.pop(str(index))
        return
