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
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

# Third party imports
import numpy as np
from scipy.spatial.transform import Rotation

# Local application imports
from . import helper
print(f"Import: OK <{__name__}>")

@dataclass
class Position:
    _coordinates: Sequence[float]
    _rotation: Rotation = Rotation.from_euler('zyx',[0,0,0],degrees=True)
    rotation_type: str = 'euler'
    
    def __post_init__(self):
        self._coordinates = tuple(self._coordinates)
        return
    
    def __repr__(self):
        return f"Position {self._coordinates} with ({self.rotation_type}) rotation\n{self.rotation}"
    
    @property
    def coordinates(self):
        return np.array(self._coordinates)
    @coordinates.setter
    def coordinates(self, value):
        if len(value) != 3:
            raise Exception('Please input x,y,z coordinates')
        self._coordinates = tuple(value)
        return
    
    @property
    def rotation(self):
        match self.rotation_type:
            case 'quaternion':
                return self._rotation.as_quat()
            case 'matrix':
                return self._rotation.as_matrix()
            case 'angle_axis':
                return self._rotation.as_rotvec()
            case 'euler':
                return self._rotation.as_euler('zyx', degrees=True)
            case 'mrp':
                return self._rotation.as_mrp()
            case 'davenport':
                return self._rotation.as_davenport()
            case _:
                raise ValueError(f"Invalid rotation type: {self.rotation_type}")
        return
    @rotation.setter
    def rotation(self, value):
        if isinstance(value, Rotation):
            raise Exception('Please input a Rotation object')
        self._rotation = value
        return
    

class Well:
    """
    Well represents a single well in a Labware object

    ### Constructor
    Args:
        `labware_info` (dict): dictionary of truncated Labware information (name, slot, reference point)
        `name` (str): name of well
        `details` (dict[str, float|tuple[float]]): well details
    
    ### Attributes
    - `content` (dict): contains the details of the contents within the well
    - `details` (dict): well details; dictionary of depth, total liquid volume, shape, diameter, x,y,z
    - `name` (str): name of well
    - `reference_point` (tuple[int]): bottom left reference corner of Labware
    - `volume` (float): volume of contents in well
    
    ### Properties
    - `base_area` (float): base area of well in mm^2
    - `bottom` (np.ndarray): bottom of well
    - `center` (np.ndarray): center of well
    - `depth` (float): well depth
    - `diameter` (float): well diameter
    - `dimensions` (tuple[float]): dimensions of base in mm
    - `level` (float): level of contents in well
    - `middle` (np.ndarray): middle of well
    - `offset` (np.ndarray): well offset from Labware reference point
    - `shape` (str): shape of well
    - `top` (np.ndarray): top of well
    
    ### Methods
    - `fromBottom`: offset from bottom of well
    - `fromMiddle`: offset from middle of well
    - `fromTop`: offset from top of well
    """
    
    def __init__(self, 
        labware_info: dict, 
        name: str, 
        details: dict[str, float|tuple[float]]
    ):
        """
        Instantiate the class

        Args:
            labware_info (dict): dictionary of truncated Labware information (name, slot, reference point)
            name (str): name of well
            details (dict[str, float|tuple[float]]): well details
        """
        self.content = {}
        self.details = details  # depth,totalLiquidVolume,shape,diameter,x,y,z
        self.name = name
        self.reference_point = labware_info.get('reference_point', (0,0,0))
        self.volume = 0
        
        self._labware_name = labware_info.get('name','')
        self._labware_slot = labware_info.get('slot','')
        self._labware_orientation = labware_info.get('orientation', np.array((0,0,0)))
        pass
    
    def __repr__(self) -> str:
        return f"{self.name} in {self._labware_name} at Slot {self._labware_slot}" 
    
    # Properties
    @property
    def base_area(self) -> float:
        """Base area in mm^2"""
        area_mm2 = 1
        if self.shape == 'circular':
            area_mm2 = 3.141592/4 * self.dimensions[0]**2
        elif self.shape == 'rectangular':
            area_mm2 = self.dimensions[0] * self.dimensions[1]
        return area_mm2
    
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
    def diameter(self) -> float:
        return self.details.get('diameter', 0)
    
    @property
    def dimensions(self) -> tuple[float]:
        """Dimensions of base in mm"""
        dim = []
        if self.shape == 'circular':
            dim.append(self.diameter)
        elif self.shape == 'rectangular':
            dim.append(self.details.get('xDimension',0))
            dim.append(self.details.get('yDimension',0))
        return tuple(dim)
    
    @property
    def level(self) -> float:
        return self.volume / self.base_area
        
    @property
    def middle(self) -> np.ndarray:
        depth = self.details.get('depth', 0)
        return self.center + np.array((0,0,depth/2))
        
    @property
    def offset(self) -> np.ndarray:
        x = self.details.get('x', 0)
        y = self.details.get('y', 0)
        z = self.details.get('z', 0)
        vector = np.array((x,y,z))
        orientation = Rotation.from_euler('zyx', self._labware_orientation, degrees=True)
        return orientation.apply(vector)
    
    @property
    def shape(self) -> str:
        return self.details.get('shape', '')
    
    @property
    def top(self) -> np.ndarray:
        depth = self.details.get('depth', 0)
        return self.center + np.array((0,0,depth))
    
    def fromBottom(self, offset:tuple[float]) -> np.ndarray:
        """
        Offset from bottom of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: bottom of well with offset
        """
        return self.bottom + np.array(offset)
    
    def fromMiddle(self, offset:tuple[float]) -> np.ndarray:
        """
        Offset from middle of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: middle of well with offset
        """
        return self.middle + np.array(offset)
    
    def fromTop(self, offset:tuple[float]) -> np.ndarray:
        """
        Offset from top of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: top of well with offset
        """
        return self.top + np.array(offset)
    
    def from_bottom(self, offset:tuple[float]) -> np.ndarray:
        """
        Offset from bottom of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: bottom of well with offset
        """
        print("'from_bottom()' method to be deprecated. Use 'fromBottom()' instead.")
        return self.fromBottom(offset=offset)
    
    def from_middle(self, offset:tuple[float]) -> np.ndarray:
        """
        Offset from middle of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: middle of well with offset
        """
        print("'from_middle()' method to be deprecated. Use 'fromMiddle()' instead.")
        return self.fromMiddle(offset=offset)
    
    def from_top(self, offset:tuple[float]) -> np.ndarray:
        """
        Offset from top of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: top of well with offset
        """
        print("'from_top()' method to be deprecated. Use 'fromTop()' instead.")
        return self.fromTop(offset=offset)


class Labware:
    """
    Labware represents a single Labware on the Deck

    ### Constructor
    Args:
        `slot` (str): deck slot number
        `bottom_left_coordinates` (tuple[float]): coordinates of bottom left corner of Labware (i.e. reference point)
        `labware_file` (str): filepath of Labware JSON file
        `package` (str|None, optional): name of package to look in. Defaults to None.
    
    ### Attributes
    - `details` (dict): dictionary read from Labware file
    - `name` (str): name of Labware
    - `slot` (str): deck slot number
    
    ### Properties
    - `center` (dict[np.ndarray, np.ndarray]): bottom-left reference point and center of Labware
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
    - `at`: alias for `getWell()`
    - `getWell`: get `Well` using its name
    """
    
    def __init__(self, 
        slot: str, 
        bottom_left_coordinates: tuple[float], 
        orientation: tuple[float],
        labware_file: str, 
        package: str|None = None
    ):
        """
        Instantiate the class

        Args:
            slot (str): deck slot number
            bottom_left_coordinates (tuple[float]): coordinates of bottom left corner (i.e. reference point)
            labware_file (str): filepath of Labware JSON file
            package (str|None, optional): name of package to look in. Defaults to None.
        """
        self.details = helper.read_json(json_file=labware_file, package=package)
        self.name = self.details.get('metadata',{}).get('displayName', '')
        self.order_wells_by_rows = False
        self._reference_point = tuple(bottom_left_coordinates)
        self._orientation = Rotation.from_euler('zyx', orientation, degrees=True)
        self.slot = slot
        self._wells = {}
        self._load_wells()
        pass
    
    def __repr__(self) -> str:
        return f"{self.name} at Slot {self.slot}" 
    
    # Properties
    @property
    def center(self) -> dict[np.ndarray, np.ndarray]:
        dimensions = self.details.get('dimensions',{})
        x = dimensions.get('xDimension', 0)
        y = dimensions.get('yDimension', 0)
        z = dimensions.get('zDimension', 0)
        # return self.reference_point, np.array((x/2,y/2,z))
        return dict(reference=np.array(self.reference_point), center=np.array((x/2,y/2,z)))
    
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
        vector = np.array((x,y,z))
        return self._orientation.apply(vector)

    @property
    def info(self) -> dict[str, str|tuple[float]]:
        return {'name':self.name, 'reference_point':self.reference_point, 'orientation': self.orientation, 'slot':self.slot}
    
    @property
    def orientation(self) -> np.ndarray:
        return self._orientation.as_euler('zyx', degrees=True)
    
    @property
    def reference_point(self) -> np.ndarray:
        return np.array(self._reference_point)
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
        if self.order_wells_by_rows:
            return {w:self._wells[w] for l in self.rows_list for w in l}
        return self._wells
    
    @property
    def wells_list(self) -> list[Well]:
        if self.order_wells_by_rows:
            return [self._wells[w] for l in self.rows_list for w in l]
        return [self._wells[well] for well in self.details.get('wells',{})]

    def at(self, name:str) -> Well:
        """
        Get `Well` using its name.
        Alias for `getWell()`.

        Args:
            name (str): name of well

        Returns:
            Well: `Well` object
        """
        return self.getWell(name=name)
    
    def getWell(self, name:str) -> Well:
        """
        Get `Well` using its name

        Args:
            name (str): name of well

        Returns:
            Well: `Well` object
        """
        return self.wells.get(name)
    
    def get_well(self, name:str) -> Well:
        """
        Get `Well` using its name

        Args:
            name (str): name of well

        Returns:
            Well: `Well` object
        """
        print("'get_well()' method to be deprecated. Use 'getWell()' instead.")
        return self.getWell(name=name)
    
    # Protected method(s)
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
        `layout_file` (str|None, optional): filepath of deck layout JSON file. Defaults to None.
        `package` (str|None, optional): name of package to look in. Defaults to None.
    
    ### Attributes
    - `details` (dict): details read from layout file
    - `exclusion_zones` (dict): dictionary of cuboidal zones to avoid
    - `names` (dict): labels for deck slots
    
    ### Properties
    - `slots` (dict[str, Labware]): loaded Labware in slots
    
    ### Methods
    - `at`: alias for `getSlot()`, with mixed input
    - `getSlot`: get Labware in slot using slot id or name
    - `isExcluded`: checks and returns whether the coordinates are in an excluded region
    - `loadLabware`: load Labware into slot
    - `loadLayout`: load deck layout from layout file
    - `removeLabware`: remove Labware in slot using slot id or name
    """
    
    def __init__(self, layout_file:str|None = None, package:str|None = None, repository:str|None = None):
        """
        Instantiate the class

        Args:
            layout_file (str|None, optional): filepath of deck layout JSON file. Defaults to None.
            package (str|None, optional): name of package to look in. Defaults to None.
            repository (str|None, optional): name of repository to look in. Defaults to None.
        """
        self.details = {}
        self._slots = {}
        self.names = {}
        self.origin = Position((0,0,0))
        self.exclusion_zones: dict[str,np.ndarray] = {}
        self.loadLayout(layout_file=layout_file, package=package, repository=repository)
        pass
    
    def __repr__(self) -> str:
        labwares = [''] + [repr(labware) for labware in self.slots.values()]
        labware_string = '\n'.join(labwares)
        return f"Deck with Labwares:{labware_string}" 
    
    @property
    def slots(self) -> dict[str, Labware]:
        return self._slots
    
    def at(self, slot:int|str) -> Labware|None:
        """
        Get Labware in slot using slot id or name, with mixed input.
        Alias for `getSlot()`.

        Args:
            slot (int|str): id or name of slot

        Returns:
            Labware|None: Labware in slot
        """
        if type(slot) == int:
            return self.getSlot(index=slot)
        elif type(slot) == str:
            return self.getSlot(name=slot)
        print("Input a valid slot id or name of Labware in slot.")
        return
    
    def getSlot(self, index:int|None = None, name:str|None = None) -> Labware|None:
        """
        Get Labware in slot using slot id or name

        Args:
            index (int|None, optional): slot id number. Defaults to None.
            name (str|None, optional): nickname of Labware. Defaults to None.

        Raises:
            ValueError: Please input either slot id or name

        Returns:
            Labware|None: Labware in slot
        """
        if not any((index, name)) or all((index, name)):
            raise ValueError('Please input either slot id or name.')
        if index is None and name is not None:
            index = self.names.get(name)
        return self._slots.get(str(index))
    
    def isExcluded(self, coordinates:tuple[float]) -> bool:
        """
        Checks and returns whether the coordinates are in an excluded region.

        Args:
            coordinates (tuple[float]): target coordinates

        Returns:
            bool: whether the coordinates are in an excluded region
        """
        coordinates = np.array(coordinates)
        for key, value in self.exclusion_zones.items():
            l_bound, u_bound = value.min(1), value.max(1)
            if key == 'boundary':
                if any(np.less(coordinates, l_bound)) and any(np.greater(coordinates, u_bound)):
                    print(f"Deck limits reached! {value}")
                    return True
                continue
            if all(np.greater(coordinates, l_bound)) and all(np.less(coordinates, u_bound)):
                name = [k for k,v in self.names.items() if str(v)==key][0] if key in self.names.values() else f'Labware in Slot {key}'
                print(f"{name} is in the way! {value}")
                return True
        return False
    
    def loadLabware(self, 
        slot: int, 
        labware_file: str, 
        package: str|None = None, 
        name: str|None = None, 
        exclusion_height: float|None = None
    ):
        """
        Load Labware into slot

        Args:
            slot (int): slot id
            labware_file (str): filepath Labware JSON file
            package (str|None, optional): name of package to look in. Defaults to None.
            name (str|None, optional): nickname of Labware. Defaults to None.
            exclusion_height (float|None, optional): height clearance from top of Labware. Defaults to None.
        """
        if name:
            self.names[name] = slot
        reference_position = tuple( self.details.get('reference_positions',{}).get(str(slot),((0,0,0),(0,0,0))) )
        # bottom_left_coordinates = tuple( self.details.get('reference_points',{}).get(str(slot),(0,0,0)) )
        if len(reference_position) != 2 or isinstance(reference_position[0], (int,float)):
            reference_position = (reference_position, (0,0,0))
            
        bottom_left_coordinates, orientation = reference_position
        labware = Labware(slot=str(slot), bottom_left_coordinates=bottom_left_coordinates, orientation=orientation, labware_file=labware_file, package=package)
        self._slots[str(slot)] = labware
        if exclusion_height is not None:
            top_right_coordinates= tuple(map(sum, zip(bottom_left_coordinates, labware.dimensions, (0,0,exclusion_height))))
            self.exclusion_zones[str(slot)] = np.array(bottom_left_coordinates, top_right_coordinates)
        return
    
    def loadLayout(
        self, 
        layout_file: str|None = None, 
        layout_dict: dict|None = None, 
        package: str|None = None, 
        labware_package: str|None = None,
        repository: str = 'control-lab-le'
    ):
        """
        Load deck layout from layout file

        Args:
            layout_file (str|None, optional): filepath of deck layout JSON file. Defaults to None.
            layout_dict (dict|None, optional): layout details. Defaults to None.
            package (str|None, optional): name of package to look in for layout file. Defaults to None.
            labware_package (str|None, optional): name of package to look in for Labware file. Defaults to None.
            repository (str, optional): name of repository to look in. Defaults to 'control-lab-le'.

        Raises:
            Exception: lease input either `layout_file` or `layout_dict`
        """
        if layout_file is None and layout_dict is None:
            return
        elif layout_file is not None and layout_dict is not None:
            raise Exception("Please input either `layout_file` or `layout_dict`.")
        elif layout_file is not None:
            self.details = helper.read_json(json_file=layout_file, package=package)
        else:
            self.details = layout_dict
        origin_position = self.details.get('origin_position', ((0,0,0),(0,0,0)))
        if len(origin_position) != 2 or isinstance(origin_position[0], (int,float)):
            origin_position = (origin_position, (0,0,0))
        self.origin = Position(origin_position[0], Rotation.from_euler('zyx', origin_position[1], degrees=True))
        
        slots = self.details.get('slots', {})
        root = str(Path().absolute()).split(repository)[0].replace('\\','/')
        for slot in sorted(list(slots)):
            info = slots[slot]
            name = info.get('name')
            labware_file = info.get('filepath','')
            labware_file = labware_file if Path(labware_file).is_absolute() else f"{root}{repository}/{labware_file.split(repository)[1]}"
            exclusion_height = info.get('exclusion_height', -1)
            exclusion_height = exclusion_height if exclusion_height >= 0 else None
            self.loadLabware(slot=slot, name=name, exclusion_height=exclusion_height, labware_file=labware_file, package=labware_package)
        return

    def removeLabware(self, index:int|None = None, name:str|None = None):
        """
        Remove Labware in slot using slot id or name

        Args:
            index (int|None, optional): slot id. Defaults to None.
            name (str|None, optional): nickname of Labware. Defaults to None.

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
    
    def get_slot(self, index:int|None = None, name:str|None = None) -> Labware|None:
        """
        Get Labware in slot using slot id or name

        Args:
            index (int|None, optional): slot id number. Defaults to None.
            name (str|None, optional): nickname of Labware. Defaults to None.

        Raises:
            ValueError: Please input either slot id or name

        Returns:
            Labware|None: Labware in slot
        """
        print("'get_slot()' method to be deprecated. Use 'getSlot()' instead.")
        return self.getSlot(index=index, name=name)
    
    def is_excluded(self, coordinates:tuple[float]) -> bool:
        """
        Checks and returns whether the coordinates are in an excluded region.

        Args:
            coordinates (tuple[float]): target coordinates

        Returns:
            bool: whether the coordinates are in an excluded region
        """
        print("'is_excluded()' method to be deprecated. Use 'isExcluded()' instead.")
        return self.isExcluded(coordinates=coordinates)
    
    def load_labware(self, 
        slot: int, 
        labware_file: str, 
        package: str|None = None, 
        name: str|None = None, 
        exclusion_height: float|None = None
    ):
        """
        Load Labware into slot

        Args:
            slot (int): slot id
            labware_file (str): filepath Labware JSON file
            package (str|None, optional): name of package to look in. Defaults to None.
            name (str|None, optional): nickname of Labware. Defaults to None.
            exclusion_height (float|None, optional): height clearance from top of Labware. Defaults to None.
        """
        print("'load_labware()' method to be deprecated. Use 'loadLabware()' instead.")
        return self.loadLabware(slot=slot, labware_file=labware_file, package=package, name=name, exclusion_height=exclusion_height)
    
    def load_layout(
        self, 
        layout_file: str|None = None, 
        layout_dict: dict|None = None, 
        package: str|None = None, 
        labware_package: str|None = None
    ):
        """
        Load deck layout from layout file

        Args:
            layout_file (str|None, optional): filepath of deck layout JSON file. Defaults to None.
            layout_dict (dict|None, optional): layout details. Defaults to None.
            package (str|None, optional): name of package to look in for layout file. Defaults to None.
            labware_package (str|None, optional): name of package to look in for Labware file. Defaults to None.

        Raises:
            Exception: lease input either `layout_file` or `layout_dict`
        """
        print("'load_layout()' method to be deprecated. Use 'loadLayout()' instead.")
        return self.loadLayout(layout_file=layout_file, layout_dict=layout_dict, package=package, labware_package=labware_package)

    def remove_labware(self, index:int|None = None, name:str|None = None):
        """
        Remove Labware in slot using slot id or name

        Args:
            index (int|None, optional): slot id. Defaults to None.
            name (str|None, optional): nickname of Labware. Defaults to None.

        Raises:
            Exception: Please input either slot id or name
        """
        print("'remove_labware()' method to be deprecated. Use 'removeLabware()' instead.")
        return self.removeLabware(index=index, name=name)

__where__ = "misc.Layout"
from .factory import include_this_module
include_this_module(get_local_only=True)