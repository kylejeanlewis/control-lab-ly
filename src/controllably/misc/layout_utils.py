# %% -*- coding: utf-8 -*-
"""
Adapted from @Pablo's labware code

Created: Tue 2023/01/25 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports

# Local application imports
from .misc_utils import Helper
print(f"Import: OK <{__name__}>")

class Well(object):
    """
    Well object

    Args:
        labware_info (dict): labware info of name, slot, reference point
        name (str): name of well
        details (dict): details of well
    """
    def __init__(self, labware_info:dict, name:str, details:dict):
        self.details = details  # depth,totalLiquidVolume,shape,diameter,x,y,z
        self.labware_info = labware_info
        self.name = name
        self.reference_point = self.labware_info.get('reference_point', (0,0,0))
        pass
    
    def __repr__(self) -> str:
        return f"{self.name} in {self.labware_info.get('name','')} at Slot {self.labware_info.get('slot','')}" 
    
    @property
    def center(self):
        """
        Center of well bottom

        Returns:
            tuple: coordinates for center of well bottom
        """
        return tuple(map(sum, zip(self.reference_point, self.offset)))
    
    @property
    def depth(self):
        """
        Depth of well

        Returns:
            float: depth of well in mm
        """
        return self.details.get('depth', 0)
    
    @property
    def offset(self):
        """
        Well offset from labware reference point

        Returns:
            tuple: offset vector
        """
        x = self.details.get('x', 0)
        y = self.details.get('y', 0)
        z = self.details.get('z', 0)
        return x,y,z
    
    @property
    def bottom(self):
        """
        Bottom of well

        Returns:
            tuple: coordinates for bottom of well
        """
        return self.center
    
    @property
    def middle(self):
        """
        Middle of well

        Returns:
            tuple: coordinates for middle of well
        """
        depth = self.details.get('depth', 0)
        return tuple(map(sum, zip(self.center, (0,0,depth/2))))
    
    @property
    def top(self):
        """
        Top of well

        Returns:
            tuple: coordinates for top of well
        """
        depth = self.details.get('depth', 0)
        return tuple(map(sum, zip(self.center, (0,0,depth))))
    
    def from_bottom(self, offset:tuple):
        """
        Offset from bottom of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: bottom of well with offset
        """
        return tuple(map(sum, zip(self.bottom, offset)))
    
    def from_middle(self, offset:tuple):
        """
        Offset from middle of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: middle of well with offset
        """
        return tuple(map(sum, zip(self.middle, offset)))
    
    def from_top(self, offset:tuple):
        """
        Offset from top of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: top of well with offset
        """
        return tuple(map(sum, zip(self.top, offset)))


class Labware(object):
    """
    Labware object

    Args:
        slot (str): deck slot
        bottom_left_coordinates (tuple): coordinates of bottom left corner (reference point)
        labware_file (str): JSON filepath for labware
        package (str, optional): name of package to look in. Defaults to None.
    """
    def __init__(self, slot:str, bottom_left_coordinates:tuple, labware_file:str, package:str = None):
        self.details = Helper.read_json(json_file=labware_file, package=package)
        self.name = self.details.get('metadata',{}).get('displayName', '')
        self.reference_point = bottom_left_coordinates
        self.slot = slot
        self._wells = {}
        self.load_wells()
        pass
    
    def __repr__(self) -> str:
        return f"{self.name} at Slot {self.slot}" 
    
    @property
    def info(self):
        """
        Summary of labware info

        Returns:
            dict: dictionary of name, reference point, and slot
        """
        return {'name':self.name, 'reference_point':self.reference_point, 'slot':self.slot}
    
    @property
    def center(self):
        """
        Center of labware

        Returns:
            tuple: coordinates of the center of labware
        """
        dimensions = self.details.get('dimensions',{})
        x = dimensions.get('xDimension', 0)
        y = dimensions.get('yDimension', 0)
        z = dimensions.get('zDimension', 0)
        return tuple(map(sum, zip(self.reference_point, (x/2,y/2,z))))
    
    @property
    def columns(self):
        """
        Labware columns

        Returns:
            dict: dictionary of labelled columns lists
        """
        columns_list = self.columns_list
        return {str(c+1): columns_list[c] for c in range(len(columns_list))}
    
    @property
    def columns_list(self):
        """
        Labware columns as list

        Returns:
            list: list of columns
        """
        return self.details.get('ordering', [[]])
    
    @property
    def rows(self):
        """
        Labware rows

        Returns:
            dict: dictionary of labelled rows lists
        """
        first_column = self.details.get('ordering', [[]])[0]
        rows_list = self.rows_list
        return {w[0]: rows_list[r] for r,w in enumerate(first_column)}
    
    @property
    def rows_list(self):
        """
        Labware rows as list

        Returns:
            list: list of rows
        """
        columns = self.columns_list
        return [list(z) for z in zip(*columns)]
       
    @property
    def wells(self):
        """
        Labware wells

        Returns:
            dict: dictionary of labelled wells
        """
        return self._wells
    
    @property
    def wells_list(self):
        """
        Labware wells as list

        Returns:
            list: list of wells
        """
        return [self._wells[well] for well in self.details.get('wells',{})]

    def get_well(self, name:str):
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


class Deck(object):
    """
    Deck object

    Args:
        layout_file (str, optional): JSON filepath of deck layout. Defaults to None.
        package (str, optional): name of package to look in. Defaults to None.
    """
    def __init__(self, layout_file:str = None, package:str = None):
        self.details = {}
        self._slots = {}
        self.names = {}
        self.load_layout(layout_file=layout_file, package=package)
        pass
    
    def __repr__(self) -> str:
        labwares = [''] + [repr(labware) for labware in self.slots.values()]
        labware_string = '\n'.join(labwares)
        return f"Deck with labwares:{labware_string}" 
    
    @property
    def slots(self):
        """
        Loaded Labware in slots

        Returns:
            dict: dictionary of labware in slots
        """
        return self._slots
    
    def get_slot(self, index:int = None, name:str = None):
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
        if not any((index, name)):
            raise Exception('Please input either slot index or name')
        if index is None and name is not None:
            index = self.names.get(name)
        return self._slots.get(str(index))
    
    def load_labware(self, slot:int, labware_file:str, package:str = None, name:str = None):
        """
        Load Labware into slot

        Args:
            slot (int): slot index
            labware_file (str): JSON filepath of labware to be loaded
            package (str, optional): name of package to look in. Defaults to None.
            name (str, optional): nickname of labware. Defaults to None.
        """
        if name is not None:
            self.names[name] = slot
        bottom_left_coordinates = tuple(self.details.get('reference_points',{}).get(str(slot)))
        self._slots[str(slot)] = Labware(slot=str(slot), bottom_left_coordinates=bottom_left_coordinates, labware_file=labware_file, package=package)
        return
    
    def load_layout(self, layout_file:str = None, layout_dict:dict = None, package:str = None, labware_package:str = None):
        """
        Load deck layout

        Args:
            layout_file (str, optional): JSON filepath of deck layout. Defaults to None.
            layout_dict (dict, optional): dictionary of layout. Defaults to None.
            package (str, optional): name of package to look in. Defaults to None.
            labware_package (str, optional): name of package to look in for labware file. Defaults to None.
        """
        if layout_file is None and layout_dict is None:
            return
        elif layout_file is not None:
            self.details = Helper.read_json(json_file=layout_file, package=package)
        else:
            self.details = layout_dict
        slots = self.details.get('slots', {})
        for slot in sorted(list(slots)):
            info = slots[slot]
            name = info.get('name')
            labware_file = info.get('filepath','')
            self.load_labware(slot=slot, name=name, labware_file=labware_file, package=labware_package)
        return
