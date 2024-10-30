# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
from dataclasses import dataclass, field
import itertools
import json
import logging
import matplotlib.pyplot as plt
from pathlib import Path
from types import SimpleNamespace
from typing import Sequence, Any, Iterator

# Third party imports
import numpy as np
from scipy.spatial.transform import Rotation

# Local application imports
from .helper import read_json

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

MTP_DIMENSIONS = (127.76,85.48,0)
OBB_DIMENSIONS = (300,300,0)

@dataclass
class Position:
    _coordinates: Sequence[float] = (0,0,0)
    _rotation: Rotation = Rotation.from_euler('zyx',(0,0,0),degrees=True)
    rotation_type: str = 'euler'
    degrees: bool = True
    
    def __post_init__(self):
        assert isinstance(self._rotation, Rotation), "Please input a Rotation object"
        assert self.rotation_type in ['quaternion','matrix','angle_axis','euler','mrp','davenport'], f"Invalid rotation type: {self.rotation_type}"
        assert isinstance(self._coordinates,(Sequence,np.ndarray)) and len(self._coordinates) == 3, "Please input x,y,z coordinates"
        self._coordinates = tuple(self._coordinates)
        return
    
    def __repr__(self):
        return f"Position {self._coordinates} with ({self.rotation_type}) rotation\n{self.rotation}"
    
    @property
    def coordinates(self) -> np.ndarray[float]:
        return np.array(self._coordinates)
    @coordinates.setter
    def coordinates(self, value: Sequence[float]|np.ndarray[float]):
        assert isinstance(value, (Sequence,np.ndarray)) and len(value) == 3, "Please input x,y,z coordinates"
        self._coordinates = tuple(value)
        return
    
    @property
    def rotation(self) -> np.ndarray:
        match self.rotation_type:
            case 'quaternion':
                return self._rotation.as_quat()
            case 'matrix':
                return self._rotation.as_matrix()
            case 'angle_axis':
                return self._rotation.as_rotvec()
            case 'euler':
                return self._rotation.as_euler('zyx', degrees=self.degrees)
            case 'mrp':
                return self._rotation.as_mrp()
            case 'davenport':
                return self._rotation.as_davenport()
            case _:
                raise ValueError(f"Invalid rotation type: {self.rotation_type}")
        return
    @rotation.setter
    def rotation(self, value: Rotation):
        assert isinstance(value, Rotation), "Please input a Rotation object"
        self._rotation = value
        return
    
    @property
    def rot_matrix(self) -> np.ndarray: 
        return self._rotation.as_matrix()
    
    @property
    def x(self) -> float:
        return self.coordinates[0]
    
    @property
    def y(self) -> float:
        return self.coordinates[1]
    
    @property
    def z(self) -> float:
        return self.coordinates[2]
    
    @property
    def a(self) -> float:
        rotation = self._rotation.as_euler('zyx', degrees=self.degrees)
        return rotation[0]
    
    @property
    def b(self) -> float:
        rotation = self._rotation.as_euler('zyx', degrees=self.degrees)
        return rotation[1]
    
    @property
    def c(self) -> float:
        rotation = self._rotation.as_euler('zyx', degrees=self.degrees)
        return rotation[2]
    
    def apply(self, on:Position) -> Position:
        return on.translate(self.coordinates).orientate(self._rotation)
    
    def orientate(self, by:Rotation) -> Position:
        self._rotation = by*self._rotation
        return self
    
    def translate(self, by:Sequence[float]) -> Position:
        self.coordinates = self.coordinates + np.array(by)
        return self
    

@dataclass
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
    name: str
    _details: dict[str, str|float|tuple[float]]
    parent: Labware
    
    x: float = field(init=False, default=0)
    y: float = field(init=False, default=0)
    z: float = field(init=False, default=0)
    shape: str = field(init=False, default='')
    depth: float = field(init=False, default=0)
    volume: float = field(init=False, default=0)
    capacity: float = field(init=False, default=0)
    dimensions: tuple[float] = field(init=False, default=(0,))
    
    def __post_init__(self):
        self.x = self._details.get('x', 0)
        self.y = self._details.get('y', 0)
        self.z = self._details.get('z', 0)
        self.shape = self._details.get('shape', '')
        self.depth = self._details.get('depth', 0)
        self.capacity = self._details.get('totalLiquidVolume', 0)
        match self.shape:
            case 'circular':
                self.dimensions = (self._details.get('diameter', 0),)
            case 'rectangular':
                self.dimensions = (self._details.get('xDimension',0), self._details.get('yDimension',0))
            case _:
                logging.error(f"Invalid shape: {self.shape}")
        return
    
    def __repr__(self) -> str:
        return f"{self.name} ({self.__class__.__name__}:{id(self)}) -> {self.parent!r}" 
    
    def __str__(self) -> str:
        return f"{self.name} in {self.parent!s}" 
    
    # Properties
    @property
    def reference(self) -> Position:
        return self.parent.bottom_left_corner
    
    @property
    def offset(self) -> np.ndarray:
        return np.array((self.x,self.y,self.z))
    
    @property
    def center(self) -> np.ndarray:
        return self.reference.coordinates + self.reference._rotation.apply(self.offset)
     
    @property
    def bottom(self) -> np.ndarray:
        return self.center
    
    @property
    def middle(self) -> np.ndarray:
        return self.center + np.array((0,0,self.depth/2))
        
    @property
    def top(self) -> np.ndarray:
        return self.center + np.array((0,0,self.depth))
    
    @property
    def base_area(self) -> float:
        """Base area in mm^2"""
        area = 0
        match self.shape:
            case 'circular':
                area = 3.141592/4 * self.dimensions[0]**2
            case 'rectangular':
                dimensions = self.dimensions
                area =  dimensions[0]*dimensions[1]
            case _:
                logging.error(f"Invalid shape: {self.shape}")
        assert area > 0, f"Invalid base area: {area}"
        return area
    
    @property
    def level(self) -> float:
        return self.volume / self.base_area
        
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
    
    def _draw(self, ax, **kwargs):
        """Draw well on matplotlib axis"""
        match self.shape:
            case 'circular':
                ax.add_patch(plt.Circle(self.center, self.dimensions[0]/2, fill=False, **kwargs))
            case 'rectangular':
                ax.add_patch(plt.Rectangle(self.bottom, *self.dimensions, fill=False, **kwargs))
            case _:
                logging.error(f"Invalid shape: {self.shape}")
        return
    
    # Deprecated methods
    def from_bottom(self, offset:tuple[float]) -> np.ndarray:
        """
        Offset from bottom of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: bottom of well with offset
        """
        logger.warning("'from_bottom()' method to be deprecated. Use 'fromBottom()' instead.")
        return self.fromBottom(offset=offset)
    
    def from_middle(self, offset:tuple[float]) -> np.ndarray:
        """
        Offset from middle of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: middle of well with offset
        """
        logger.warning("'from_middle()' method to be deprecated. Use 'fromMiddle()' instead.")
        return self.fromMiddle(offset=offset)
    
    def from_top(self, offset:tuple[float]) -> np.ndarray:
        """
        Offset from top of well

        Args:
            offset (tuple): x,y,z offset

        Returns:
            tuple: top of well with offset
        """
        logger.warning("'from_top()' method to be deprecated. Use 'fromTop()' instead.")
        return self.fromTop(offset=offset)


@dataclass
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
    name: str
    _details: dict[str, Any]
    parent: Slot|None = None
    
    x: float = field(init=False, default=0)
    y: float = field(init=False, default=0)
    z: float = field(init=False, default=0)
    _dimensions: tuple[float] = field(init=False, default=(0,0,0))
    exclusion_zone: BoundingBox|None = field(init=False, default=None)
    _wells: dict[str, Well] = field(init=False, default_factory=dict)
    _ordering: list[list[str]] = field(init=False, default_factory=list)
    is_stackable: bool = field(init=False, default=False)
    is_tiprack: bool = field(init=False, default=False)
    slot_above: Slot|None = field(init=False, default=None)
    
    def __post_init__(self):
        dimensions = self._details.get('dimensions',{})
        self.x = dimensions.get('xDimension', 0)/2
        self.y = dimensions.get('yDimension', 0)/2
        self.z = dimensions.get('zDimension', 0)/2
        self._dimensions = (self.x*2,self.y*2,self.z*2)
        self.is_stackable = self._details.get('parameters',{}).get('isStackable', False)
        self.is_tiprack = self._details.get('parameters',{}).get('isTiprack', False)
        self._ordering = self._details.get('ordering', [[]])
        self._wells = {name:Well(name=name, _details=details, parent=self) for name,details in self._details.get('wells',{}).items()}
        
        buffer = self._details.get('parameters',{}).get('boundary_buffer', ((0,0,0),(0,0,0)))
        self.exclusion_zone = BoundingBox(self.reference, self.dimensions, buffer)
        
        details_above = self._details.get('slotAbove','')
        if self.is_stackable and details_above:
            below_name = self.parent.name if isinstance(self.parent, Slot) else 'None'
            above_name = below_name[:-1] + chr(ord(below_name[-1]) + 1)
            if below_name[-1].isdigit() or below_name[-2] != '_':
                above_name = below_name + '_a'
            self.slot_above = Slot(
                name=above_name, 
                _details=details_above, 
                parent=self,
                bottom_left_corner=self.bottom_left_corner.translate(by=(0,0,self.z))
            )
            self.slot_above.slot_below = self.parent
        return
    
    def __repr__(self) -> str:
        return f"{self.name} ({self.__class__.__name__}:{id(self)}) -> {self.parent.name} ({self.parent.__class__.__name__}:{id(self.parent)})" 
    
    def __str__(self) -> str:
        return f"{self.name} ({len(self._wells)}x) on {self.parent.name}" 
    
    @classmethod
    def fromConfigs(cls, details:dict[str, Any], parent:Slot|None = None):
        """
        Load Labware details from JSON file

        Args:
            json_file (str): filepath of Labware JSON file
            package (str|None, optional): name of package to look in. Defaults to None.
        """
        name = details.get('metadata',{}).get('displayName', '')
        return cls(name=name, _details=details, parent=parent)
    
    @classmethod
    def fromFile(cls, labware_file:str|Path, parent:Slot|None = None):
        """
        Load Labware from file

        Args:
            labware_file (str): filepath of Labware JSON file
            package (str|None, optional): name of package to look in. Defaults to None.
        """
        assert isinstance(labware_file,(str,Path)), "Please input a valid filepath"
        filepath = Path(labware_file)
        assert filepath.is_file(), "Please input a valid Labware filepath"
        with open(filepath, 'r') as file:
            details = json.load(file) # TODO read from file
        return cls.fromConfigs(details=details, parent=parent)
    
    # Properties
    @property
    def reference(self) -> Position:
        reference = self.parent.bottom_left_corner if isinstance(self.parent, Slot) else Position()
        return reference
        
    @property
    def offset(self) -> np.ndarray:
        return np.array((self.x,self.y,self.z))
    
    @property
    def center(self) -> np.ndarray:
        return self.reference.coordinates + self.reference._rotation.apply(self.offset)
    
    @property
    def bottom_left_corner(self) -> Position:
        return self.reference
    
    @property
    def dimensions(self) -> np.ndarray:
        return self.reference._rotation.apply(self._dimensions)
    
    @property
    def columns(self) -> dict[int, list[str]]:
        return {i+1: ordering for i,ordering in enumerate(self._ordering)}
    
    @property
    def rows(self) -> dict[str, list[str]]:
        first_column = self._ordering[0]
        rows_list = self.listRows()
        return {name[0]: rows_list[r] for r,name in enumerate(first_column)}
       
    @property
    def wells_columns(self) -> dict[str, list[Well]]:
        return self._wells
    
    @property
    def wells_rows(self) -> dict[str, list[Well]]:
        return {name:self._wells[name] for row in self.listRows() for name in row}

    @property
    def at(self) -> SimpleNamespace:
        return SimpleNamespace(**self._wells)

    def getWell(self, name:str) -> Well:
        """
        Get `Well` using its name

        Args:
            name (str): name of well

        Returns:
            Well: `Well` object
        """
        assert name in self._wells, f"Well '{name}' not found in Labware '{self.name}'"
        return self._wells.get(name)
    
    def listColumns(self) -> list[list[str]]:
        return self._ordering
    
    def listRows(self) -> list[list[str]]:
        return [list(r) for r in zip(*self._ordering)]
    
    def listWells(self, by:str) -> list[Well]:
        if by in ('c','col','cols','column','columns'):
            return self.wells_columns
        elif by in ('r','row','rows'):
            return self.wells_rows
        raise ValueError(f"Invalid argument: {by}")
    
    def show(self, zoom_out:bool = False) -> plt.Figure:
        fig, ax = plt.subplots()
        self._draw(ax=ax)
        
        if zoom_out:
            ax.set_xlim(-self.dimensions[0], self.dimensions[0]*2)
            ax.set_ylim(-self.dimensions[1], self.dimensions[1]*2)
        else:
            reference = self.reference.coordinates
            ax.set_xlim(reference[0], reference[0] + self.dimensions[0])
            ax.set_ylim(reference[1], reference[1] + self.dimensions[1])
        x_inch,y_inch = fig.get_size_inches()
        inches_per_line = max(x_inch/self.dimensions[0], y_inch/self.dimensions[1])
        new_size = tuple(np.array(self.dimensions[:2]) * inches_per_line)
        fig.set_size_inches(new_size)
        return fig
        
    def _draw(self, ax, **kwargs):
        """Draw Labware on matplotlib axis"""
        ax.add_patch(plt.Rectangle(self.reference.coordinates, *self.dimensions[:2], fill=False, **kwargs))
        for well in self._wells.values():
            well._draw(ax, **kwargs)
        return
    
    # Deprecated methods
    def get_well(self, name:str) -> Well:
        """
        Get `Well` using its name

        Args:
            name (str): name of well

        Returns:
            Well: `Well` object
        """
        logger.warning("'get_well()' method to be deprecated. Use 'getWell()' instead.")
        return self.getWell(name=name)
    

@dataclass
class Slot:
    name: str
    _details: dict[str, Any]
    parent: Deck|Labware
    
    x: float = field(init=False, default=0)
    y: float = field(init=False, default=0)
    z: float = field(init=False, default=0)
    _dimensions: tuple[float] = field(init=False, default=MTP_DIMENSIONS)
    bottom_left_corner: Position = field(init=False, default_factory=Position)
    loaded_labware: Labware|None = field(init=False, default=None)
    slot_above: Slot|None = field(init=False, default=None)
    slot_below: Slot|None = field(init=False, default=None)
    
    def __post_init__(self):
        corner_offset = self._details.get('cornerOffset',(0,0,0))
        new_corner_offset = self.reference.coordinates + self.reference._rotation.apply(corner_offset)
        orientation = self._details.get('orientation',(0,0,0))
        bottom_left_corner = Position(new_corner_offset, Rotation.from_euler('zyx',orientation,degrees=True))
        self.bottom_left_corner = bottom_left_corner.orientate(self.reference._rotation)
        
        dimensions = np.array(self._details.get('dimensions',self._dimensions))
        self.x,self.y,self.z = dimensions/2
        self._dimensions = tuple(dimensions)
        
        
        labware_file = Path(self._details.get('labware_file',''))
        if labware_file.is_file():
            self.loadLabwareFromFile(labware_file=labware_file)
        return
    
    def __repr__(self) -> str:
        loaded_labware_ref = 'Vacant'
        if isinstance(self.loaded_labware, Labware):
            labware = self.loaded_labware
            loaded_labware_ref = f"{labware.name} ({labware.__class__.__name__}:{id(labware)})" 
        return f"{self.name} ({self.__class__.__name__}:{id(self)}) on {self.parent.name} ({self.parent.__class__.__name__}:{id(self.parent)}) <- {loaded_labware_ref}" 
    
    def __str__(self) -> str:
        loaded_labware_name = f"with {self.loaded_labware.name}" if isinstance(self.loaded_labware, Labware) else '[Vacant]'
        return f"{self.name} on {self.parent.name} {loaded_labware_name}" 
    
    @property
    def reference(self) -> Position:
        return self.parent.bottom_left_corner
    
    @property
    def offset(self) -> np.ndarray:
        return np.array((self.x,self.y,self.z))
    
    @property
    def center(self) -> np.ndarray:
        return self.reference.coordinates + self.reference._rotation.apply(self.offset)
    
    @property
    def dimensions(self) -> np.ndarray:
        return self.bottom_left_corner._rotation.apply(self._dimensions)
    
    @property
    def exclusion_zone(self) -> BoundingBox|None:
        return self.loaded_labware.exclusion_zone if isinstance(self.loaded_labware, Labware) else None

    def loadLabware(self, labware:Labware):
        self.loaded_labware = labware
        self.slot_above = self.loaded_labware.slot_above
        return
    
    def loadLabwareFromConfigs(self, details:dict[str, Any]):
        labware = Labware.fromConfigs(details=details, parent=self)
        return self.loadLabware(labware=labware)
        
    def loadLabwareFromFile(self, labware_file:str):
        labware = Labware.fromFile(labware_file=labware_file, parent=self)
        return self.loadLabware(labware=labware)
        
    def removeLabware(self):
        assert self.loaded_labware is not None, "No Labware loaded in slot"
        if self.loaded_labware.is_stackable:
            assert self.loaded_labware.slot_above.loaded_labware is None, "Another Labware is stacked above"
        self.loaded_labware.slot_above.slot_below = None
        self.loaded_labware = None
        self.slot_above = None
        return

    def _draw(self, ax, **kwargs):
        """Draw Slot on matplotlib axis"""
        ax.add_patch(plt.Rectangle(self.bottom_left_corner.coordinates, *self.dimensions[:2], fill=False, linestyle=":", **kwargs))
        if  isinstance(self.loaded_labware, Labware):
            self.loaded_labware._draw(ax, **kwargs)
        return


@dataclass
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
    name: str
    _details: dict[str, Any]
    parent: Deck|None = None
    _nesting_lineage: tuple[Path] = (None,)
    
    x: float = field(init=False, default=0)
    y: float = field(init=False, default=0)
    z: float = field(init=False, default=0)
    _dimensions: tuple[float] = field(init=False, default=OBB_DIMENSIONS)
    bottom_left_corner: Position = field(init=False, default_factory=Position)
    _slots: dict[str, Slot] = field(init=False, default_factory=dict)
    _zones: dict[str, Deck] = field(init=False, default_factory=dict)
    
    def __post_init__(self):
        dimensions = np.array(self._details.get('dimensions',(0,0,0)))
        self.x,self.y,self.z = dimensions/2
        self._dimensions = tuple(dimensions)
        
        corner_offset = self._details.get('cornerOffset',(0,0,0))
        new_corner_offset = self.reference.coordinates + self.reference._rotation.apply(corner_offset)
        orientation = self._details.get('orientation',(0,0,0))
        bottom_left_corner = Position(new_corner_offset, Rotation.from_euler('zyx',orientation,degrees=True))
        self.bottom_left_corner = bottom_left_corner.orientate(self.reference._rotation)
        
        self._slots = {f"slot_{int(idx):02}":Slot(name=f"slot_{int(idx):02}", _details=details, parent=self) for idx,details in self._details.get('slots',{}).items()}
        for name,details in self._details.get('zones',{}).items():
            deck_file = Path(details.get('deck_file',''))
            if deck_file.is_file():
                parent_lineage = self.parent._nesting_lineage if isinstance(self.parent,Deck) else self._nesting_lineage
                if deck_file in parent_lineage:
                    parent_str = '\n+ '.join([p.as_uri() for p in parent_lineage if p is not None])
                    logging.error(f"Nested deck lineage:\n{parent_str}")
                    raise ValueError(f"Deck '{deck_file}' is already in the nested deck lineage")
                else:
                    self.loadNestedDeck(name=f"zone_{name}", details=details)
        return
    
    def __repr__(self) -> str:
        slots_ref = [f"\\__ {slot!r}" for slot in self.slots.values() if isinstance(slot, Slot)]
        zones_ref = [f"\\__ {zone!r}" for zone in self.zones.values()]
        return f"{self.name} ({self.__class__.__name__}:{id(self)})\n{'\n'.join(slots_ref)}\n\n{'\n'.join(zones_ref)}" 
    
    def __str__(self) -> str:
        slots_name = [f"+ {slot!s}" for slot in self.slots.values()]
        zones_name = [f"+ {zone!s}" for zone in self.zones.values()]
        return f"{self.name} comprising:\n{'\n'.join(slots_name)}\n{'\n'.join(zones_name)}"
    
    @classmethod
    def fromConfigs(cls, details:str, parent:Deck|None = None, _nesting_lineage:Sequence[Path|None]=(None,)):
        """
        Load deck layout from layout file

        Args:
            json_file (str): filepath of deck layout JSON file
            package (str|None, optional): name of package to look in. Defaults to None.
        """
        name = details.get('name',None)
        name = details.get('metadata',{}).get('displayName', '') if name is None else name
        return cls(name=name, _details=details, parent=parent, _nesting_lineage=tuple(_nesting_lineage))
    
    @classmethod
    def fromFile(cls, deck_file:str, parent:Deck|None = None):
        """
        Load deck layout from layout file

        Args:
            layout_file (str): filepath of deck layout JSON file
            package (str|None, optional): name of package to look in. Defaults to None.
        """
        assert isinstance(deck_file,(str,Path)), "Please input a valid filepath"
        filepath = Path(deck_file)
        assert filepath.is_file(), "Please input a valid Deck filepath"
        with open(filepath, 'r') as file:
            details = json.load(file) # TODO read from file
        return cls.fromConfigs(details=details, parent=parent, _nesting_lineage=(filepath,))
    
    # Properties
    @property
    def reference(self) -> Position:
        reference = self.parent.bottom_left_corner if isinstance(self.parent, Deck) else Position()
        return reference
    
    @property
    def offset(self) -> np.ndarray:
        return np.array((self.x,self.y,self.z))
    
    @property
    def center(self) -> np.ndarray:
        return self.reference.coordinates + self.reference._rotation.apply(self.offset)
    
    @property
    def dimensions(self) -> np.ndarray:
        return self.bottom_left_corner._rotation.apply(self._dimensions)
    
    @property
    def exclusion_zones(self) -> dict[str, np.ndarray]:
        raise NotImplementedError("Exclusion zones not implemented yet")
    
    @property
    def slots(self) -> dict[str, Slot]:
        return self._slots
    
    @property
    def zones(self) -> dict[str, Deck]:
        return self._zones
    
    @property
    def at(self) -> SimpleNamespace:
        return SimpleNamespace(**self._slots)
    
    @property
    def on(self) -> SimpleNamespace:
        return SimpleNamespace(**self._zones)
    
    def getSlot(self, value:int|str) -> Labware|None:
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
        if isinstance(value, int):
            value = f"slot_{value:02}"
        return self._slots.get(value, None)
    
    def loadNestedDeck(self, name:str, details:dict[str, Any]):
        deck_file = Path(details.pop('deck_file',''))
        assert deck_file.is_file(), "Please input a valid Deck filepath"
        with open(deck_file, 'r') as file:
            nested_details = json.load(file)
            nested_details.update(details)
            nested_details.update(dict(name=name))
        _nesting_lineage = (*self._nesting_lineage, deck_file)
        deck = Deck.fromConfigs(details=nested_details, parent=self, _nesting_lineage=_nesting_lineage)
        deck.name = name if not self.name.startswith('zone') else f"{self.name}_sub{name}"
        self._zones[name] = deck
        self._slots[name] = SimpleNamespace(**deck._slots)
        return
    
    def show(self, zoom_out:bool = False) -> plt.Figure:
        fig, ax = plt.subplots()
        color_iterator = iter(plt.rcParams['axes.prop_cycle'].by_key()['color'])
        color_iterator = itertools.chain(['none'], color_iterator, itertools.cycle(['black']))
        self._draw(ax=ax, color_iterator=color_iterator)
        
        if zoom_out:
            ax.set_xlim(-self.dimensions[0], self.dimensions[0]*2)
            ax.set_ylim(-self.dimensions[1], self.dimensions[1]*2)
        else:
            reference = self.reference.coordinates
            ax.set_xlim(reference[0], reference[0] + self.dimensions[0])
            ax.set_ylim(reference[1], reference[1] + self.dimensions[1])
        x_inch,y_inch = fig.get_size_inches()
        inches_per_line = max(x_inch/self.dimensions[0], y_inch/self.dimensions[1])
        new_size = tuple(np.array(self.dimensions[:2]) * inches_per_line)
        fig.set_size_inches(new_size)
        return fig
    
    def _draw(self, ax, outline:bool=False, color_iterator:Iterator|None = None, **kwargs):
        """Draw Deck on matplotlib axis"""
        bg_color = next(color_iterator) if isinstance(color_iterator,Iterator) else None
        ax.add_patch(plt.Rectangle(self.bottom_left_corner.coordinates, *self.dimensions[:2], alpha=0.25, color=bg_color, **kwargs))
        ax.add_patch(plt.Rectangle(self.bottom_left_corner.coordinates, *self.dimensions[:2], fill=False, **kwargs))
        
        for zone in self._zones.values():
            if isinstance(zone, Deck):
                zone._draw(ax, outline=True, color_iterator=color_iterator, **kwargs)
        if outline:
            return
        
        def draw_slots(ax, slots:dict[str, Slot|SimpleNamespace], **kwargs):
            for slot in slots.values():
                if isinstance(slot, Slot):
                    slot._draw(ax, **kwargs)
                elif isinstance(slot, SimpleNamespace):
                    draw_slots(ax, vars(slot), **kwargs)
            return
        draw_slots(ax, self._slots, **kwargs)
        # for slot in self._slots.values():
        #     if isinstance(slot, Slot):
        #         slot._draw(ax, **kwargs)
            
        return
    
    # Deprecated methods
    def isExcluded(self, coordinates:tuple[float]) -> bool:
        """
        Checks and returns whether the coordinates are in an excluded region.

        Args:
            coordinates (tuple[float]): target coordinates

        Returns:
            bool: whether the coordinates are in an excluded region
        """
        # coordinates = np.array(coordinates)
        # for key, value in self.exclusion_zones.items():
        #     l_bound, u_bound = value.min(1), value.max(1)
        #     if key == 'boundary':
        #         if any(np.less(coordinates, l_bound)) and any(np.greater(coordinates, u_bound)):
        #             print(f"Deck limits reached! {value}")
        #             return True
        #         continue
        #     if all(np.greater(coordinates, l_bound)) and all(np.less(coordinates, u_bound)):
        #         name = [k for k,v in self.names.items() if str(v)==key][0] if key in self.names.values() else f'Labware in Slot {key}'
        #         print(f"{name} is in the way! {value}")
        #         return True
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
        logger.warning("'get_slot()' method to be deprecated. Use 'getSlot()' instead.")
        return self.getSlot(index=index, name=name)
    
    def is_excluded(self, coordinates:tuple[float]) -> bool:
        """
        Checks and returns whether the coordinates are in an excluded region.

        Args:
            coordinates (tuple[float]): target coordinates

        Returns:
            bool: whether the coordinates are in an excluded region
        """
        logger.warning("'is_excluded()' method to be deprecated. Use 'isExcluded()' instead.")
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
        logger.warning("'load_labware()' method to be deprecated. Use 'loadLabware()' instead.")
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
        logger.warning("'load_layout()' method to be deprecated. Use 'loadLayout()' instead.")
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
        logger.warning("'remove_labware()' method to be deprecated. Use 'removeLabware()' instead.")
        return self.removeLabware(index=index, name=name)


@dataclass
class BoundingBox:
    reference: Position
    dimensions: Sequence[float]
    buffer: Sequence[Sequence[float]] = ((0,0,0),(0,0,0))
    
    def __post_init__(self):
        assert len(self.dimensions) == 3, "Please input x,y,z dimensions"
        assert len(self.buffer) == 2, "Please input lower and upper buffer"
        assert all([len(b) == 3 for b in self.buffer]), "Please input x,y,z buffer"
        return
    
    def __get__(self, instance, owner):
        bounds = np.array(self.reference.coordinates, self.reference.translate(self.dimensions).coordinates)
        return bounds + np.array(self.buffer)

__where__ = "misc.Position"
from .factory import include_this_module
include_this_module(get_local_only=True)