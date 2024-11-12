# -*- coding: utf-8 -*-
"""
This module contains classes and functions for dealing with positioning in a robotic set up.

Attributes:
    MTP_DIMENSIONS (tuple[float]): Microtiter plate dimensions in mm
    OBB_DIMENSIONS (tuple[float]): Optical Breadboard dimensions in mm

## Classes:
    `Position`: represents a 3D position with orientation
    `Well`: represents a single well in a Labware object
    `Labware`: represents a single Labware object
    `Slot`: represents a single Slot object on a Deck object or another Labware object (for stackable Labware)
    `Deck`: represents a Deck object
    `BoundingBox`: represents a 3D bounding box
    
## Functions:
    `get_transform`: get transformation matrix from initial to final points, with the first point in each set being the center of rotation

<i>Documentation last updated: 2022-11-12</i>
"""
# Standard library imports
from __future__ import annotations
from dataclasses import dataclass, field
import itertools
import json
import logging
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from pathlib import Path
from types import SimpleNamespace
from typing import Sequence, Any, Iterator

# Third party imports
import numpy as np
from scipy.spatial.transform import Rotation

# Local application imports
from .file_handler import read_config_file, resolve_repo_filepath

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

MTP_DIMENSIONS = (127.76,85.48,0)
"""Microtiter plate dimensions in mm"""
OBB_DIMENSIONS = (300,300,0)
"""Optical Breadboard dimensions in mm"""

def get_transform(initial_points: np.ndarray, final_points:np.ndarray) -> tuple[Position,float]:
    """
    Get transformation matrix from initial to final points, with the first point in each set being the center of rotation.

    Args:
        initial_points (numpy.ndarray): initial points
        final_points (numpy.ndarray): final points

    Returns:
        Position, float: transformation Position (i.e. vector and rotation) and scale factor
    """
    assert isinstance(initial_points, np.ndarray) and isinstance(final_points, np.ndarray), "Please input numpy arrays"
    assert initial_points.shape == final_points.shape, "Initial and final points must have the same shape"
    assert initial_points.shape[1] == 3, "Please input 3D points"
    assert initial_points.shape[0]%2 == 0, "Even number of points required"
    
    # align centroids
    initial_centroid = initial_points[0]
    final_centroid = final_points[0]
    translation = final_centroid - initial_centroid
    
    # center points
    initial_vectors = initial_points - initial_centroid
    final_vectors = final_points - final_centroid
    # align vectors
    rotation = Rotation.align_vectors(final_vectors, initial_vectors)[0]
    
    scale = np.linalg.norm(final_vectors) / np.linalg.norm(initial_vectors)
    return Position(translation, rotation), scale

@dataclass
class Position:
    """
    `Position` represents a 3D position with orientation

    ### Constructor:
        `_coordinates` (Sequence[float]|numpy.ndarray, optional): X,Y,Z coordinates. Defaults to (0,0,0).
        `Rotation` (Rotation, optional): scipy.spatial.transform.Rotation object. Defaults to Rotation.from_euler('zyx',(0,0,0),degrees=True).
        `rotation_type` (str, optional): preferred representation of rotation (quaternion, matrix, angle_axis, euler, mrp, davenport). Defaults to 'euler'.
        `degrees` (bool, optional): whether to use degrees for euler angles. Defaults to True.

    ### Attributes and properties:
        `coordinates` (numpy.ndarray): X,Y,Z coordinates
        `degrees` (bool): whether to use degrees for euler angles
        `Rotation` (Rotation): scipy.spatial.transform.Rotation object
        `rotation` (numpy.ndarray): rotation in preferred representation
        `rotation_type` (str): preferred representation of rotation
        `rot_matrix` (numpy.ndarray): rotation matrix
        `x` (float): X coordinate
        `y` (float): Y coordinate
        `z` (float): Z coordinate
        `a` (float): euler angle a (rotation about x-axis)
        `b` (float): euler angle b (rotation about y-axis)
        `c` (float): euler angle c (rotation about z-axis)
    
    ### Methods:
        `apply`: apply `Position` to another `Position`
        `invert`: invert vector and rotation
        `orientate`: orientate self by a rotation
        `translate`: translate self by a vector
    """
    
    _coordinates: Sequence[float]|np.ndarray = (0,0,0)
    Rotation: Rotation = Rotation.from_euler('zyx',(0,0,0),degrees=True)
    rotation_type: str = 'euler'
    degrees: bool = True
    
    def __post_init__(self):
        assert isinstance(self.Rotation, Rotation), "Please input a Rotation object"
        assert self.rotation_type in ['quaternion','matrix','angle_axis','euler','mrp','davenport'], f"Invalid rotation type: {self.rotation_type}"
        assert isinstance(self._coordinates,(Sequence,np.ndarray)) and len(self._coordinates) == 3, "Please input x,y,z coordinates"
        self._coordinates = tuple(self._coordinates)
        return
    
    def __repr__(self):
        return f"Position {self._coordinates} with ({self.rotation_type}) rotation\n{self.rotation}"
    
    @property
    def coordinates(self) -> np.ndarray[float]:
        """X,Y,Z coordinates"""
        return np.array(self._coordinates)
    @coordinates.setter
    def coordinates(self, value: Sequence[float]|np.ndarray[float]):
        assert isinstance(value, (Sequence,np.ndarray)) and len(value) == 3, "Please input x,y,z coordinates"
        self._coordinates = tuple(value)
        return
    
    @property
    def rotation(self) -> np.ndarray:
        """Rotation in preferred representation"""
        if self.rotation_type == 'quaternion':
            return self.Rotation.as_quat()
        elif self.rotation_type == 'matrix':
            return self.Rotation.as_matrix()
        elif self.rotation_type == 'angle_axis':
            return self.Rotation.as_rotvec()
        elif self.rotation_type == 'euler':
            return self.Rotation.as_euler('zyx', degrees=self.degrees)
        elif self.rotation_type == 'mrp':
            return self.Rotation.as_mrp()
        elif self.rotation_type == 'davenport':
            return self.Rotation.as_davenport()
        raise ValueError(f"Invalid rotation type: {self.rotation_type}")
    @rotation.setter
    def rotation(self, value: Rotation):
        assert isinstance(value, Rotation), "Please input a Rotation object"
        self.Rotation = value
        return
    
    @property
    def rot_matrix(self) -> np.ndarray:
        """Rotation matrix"""
        return self.Rotation.as_matrix()
    
    @property
    def x(self) -> float:
        """X coordinate"""
        return self.coordinates[0]
    
    @property
    def y(self) -> float:
        """Y coordinate"""
        return self.coordinates[1]
    
    @property
    def z(self) -> float:
        """Z coordinate"""
        return self.coordinates[2]
    
    @property
    def a(self) -> float:
        """Euler angle a (rotation about x-axis)"""
        rotation = self.Rotation.as_euler('zyx', degrees=self.degrees)
        return rotation[2]
    
    @property
    def b(self) -> float:
        """Euler angle b (rotation about y-axis)"""
        rotation = self.Rotation.as_euler('zyx', degrees=self.degrees)
        return rotation[1]
    
    @property
    def c(self) -> float:
        """Euler angle c (rotation about z-axis)"""
        rotation = self.Rotation.as_euler('zyx', degrees=self.degrees)
        return rotation[0]
    
    def apply(self, other:Position) -> Position:
        """
        Apply self to other `Position`, first translating and then orientating

        Args:
            on (Position): other `Position`

        Returns:
            Position: other `Position` transformed by self
        """
        return other.translate(self.coordinates).orientate(self.Rotation)
    
    def invert(self) -> Position:
        """
        Invert vector and rotation

        Returns:
            Position: inverted `Position`
        """
        return Position(-self.coordinates, self.Rotation.inv())
    
    def orientate(self, by:Rotation, inplace:bool = True) -> Position:
        """
        Orientate self by a rotation
        
        Args:
            by (Rotation): rotation to orientate by
            inplace (bool, optional): whether to update self in place. Defaults to True.
            
        Returns:
            Position: updated `Position`, self if `inplace=True`
        """
        if inplace:
            self.Rotation = by*self.Rotation
            return self
        rotation = by*self.Rotation
        return Position(self.coordinates, rotation)
    
    def translate(self, by:Sequence[float], inplace:bool = True) -> Position:
        """
        Translate self by a vector
        
        Args:
            by (Sequence[float]): translation vector
            inplace (bool, optional): whether to update self in place. Defaults to True.
            
        Returns:
            Position: updated `Position`, self if `inplace=True`
        """
        if inplace:
            self.coordinates = self.coordinates + np.array(by)
            return self
        coordinates = self.coordinates + np.array(by)
        return Position(coordinates, self.Rotation)
    

@dataclass
class Well:
    """
    `Well` represents a single well in a `Labware` object
    
    ### Constructor:
        `name` (str): name of well
        `_details` (dict[str, float|tuple[float]]): well details
        `parent` (Labware): parent `Labware` object
        
    ### Attributes and properties:
        `name` (str): name of well
        `details` (dict[str, str|float|tuple[float]]): dictionary read from `Labware` file
        `parent` (Labware): parent `Labware` object
        `reference` (Position): reference point of Labware
        `x` (float): x offset
        `y` (float): y offset
        `z` (float): z offset
        `offset` (numpy.ndarray): well offset from Labware reference point
        `center` (numpy.ndarray): center of well base
        `bottom` (numpy.ndarray): bottom of well
        `middle` (numpy.ndarray): middle of well
        `top` (numpy.ndarray): top of well
        `shape` (str): shape of well
        `depth` (float): well depth
        `volume` (float): volume of contents in well
        `capacity` (float): total liquid capacity
        `dimensions` (tuple[float]): dimensions of base in mm
        `base_area` (float): base area of well in mm^2
        `level` (float): height level of contents in well
        
    ### Methods:
        `fromBottom`: offset from bottom of well
        `fromMiddle`: offset from middle of well
        `fromTop`: offset from top of well
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
        if self.shape == 'circular':
            self.dimensions = (self._details.get('diameter', 0),)
        elif self.shape == 'rectangular':    
            self.dimensions = (self._details.get('xDimension',0), self._details.get('yDimension',0))
        else:
            logger.error(f"Invalid shape: {self.shape}")
        return
    
    def __repr__(self) -> str:
        return f"{self.name} ({self.__class__.__name__}:{id(self)}) -> {self.parent!r}" 
    
    def __str__(self) -> str:
        return f"{self.name} in {self.parent!s}" 
    
    # Properties
    @property
    def details(self) -> dict[str, str|float|tuple[float]]:
        """Dictionary read from Labware file"""
        return self._details
    
    @property
    def reference(self) -> Position:
        """Reference point of Labware"""
        return self.parent.bottom_left_corner
    
    @property
    def offset(self) -> np.ndarray:
        """Well offset from Labware reference point"""
        return np.array((self.x,self.y,self.z))
    
    @property
    def center(self) -> np.ndarray:
        """Center of well base"""
        return self.reference.coordinates + self.reference.Rotation.apply(self.offset)
     
    @property
    def bottom(self) -> np.ndarray:
        """Bottom of well"""
        return self.center
    
    @property
    def middle(self) -> np.ndarray:
        """Middle of well"""
        return self.center + np.array((0,0,self.depth/2))
        
    @property
    def top(self) -> np.ndarray:
        """Top of well"""
        return self.center + np.array((0,0,self.depth))
    
    @property
    def base_area(self) -> float:
        """Base area in mm^2"""
        area = 0
        if self.shape == 'circular':
            area = np.pi/4 * self.dimensions[0]**2
        elif self.shape == 'rectangular':
            dimensions = self.dimensions
            area =  dimensions[0]*dimensions[1]
        else:   
            logger.error(f"Invalid shape: {self.shape}")
        assert area > 0, f"Invalid base area: {area}"
        return area
    
    @property
    def level(self) -> float:
        """Height level of contents in well"""
        return self.volume / self.base_area
        
    def fromBottom(self, offset:Sequence[float]|np.ndarray) -> np.ndarray:
        """
        Offset from bottom of well

        Args:
            offset (Sequence[float]|numpy.ndarray): x,y,z offset

        Returns:
            tuple: bottom of well with offset
        """
        return self.bottom + np.array(offset)
    
    def fromMiddle(self, offset:Sequence[float]|np.ndarray) -> np.ndarray:
        """
        Offset from middle of well

        Args:
            offset (Sequence[float]|numpy.ndarray): x,y,z offset

        Returns:
            tuple: middle of well with offset
        """
        return self.middle + np.array(offset)
    
    def fromTop(self, offset:Sequence[float]|np.ndarray) -> np.ndarray:
        """
        Offset from top of well

        Args:
            offset (Sequence[float]|numpy.ndarray): x,y,z offset

        Returns:
            tuple: top of well with offset
        """
        return self.top + np.array(offset)
    
    def _draw(self, ax: plt.Axes, zoom_out:bool = False, **kwargs):
        """
        Draw self on matplotlib axis

        Args:
            ax (matplotlib.pyplot.Axes): plot axes
            zoom_out (bool, optional): whether to use zoomed out view. Defaults to False.
        """
        if self.shape == 'circular':
            ax.add_patch(plt.Circle(self.center, self.dimensions[0]/2, fill=False, **kwargs))
        elif self.shape == 'rectangular':
            dimensions = self.reference.Rotation.apply(np.array([*self.dimensions,0]))
            corner = self.bottom - dimensions/2
            print(corner, dimensions)
            ax.add_patch(plt.Rectangle(corner[:2], *dimensions[:2], fill=False, **kwargs))
        else:
            logger.error(f"Invalid shape: {self.shape}")
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
    `Labware` represents a single Labware object
    
    ### Constructor:
        `name` (str): name of Labware
        `_details` (dict[str, Any]): dictionary read from Labware file
        `parent` (Slot|None, optional): parent `Slot` object. Defaults to None.
        
    ### Attributes and properties:
        `name` (str): name of Labware
        `details` (dict[str, Any]): dictionary read from Labware file
        `parent` (Slot|None): parent `Slot` object
        `reference` (Position): reference point of `Slot`
        `x` (float): x offset
        `y` (float): y offset
        `z` (float): z offset
        `offset` (numpy.ndarray): Labware offset from Slot reference point
        `center` (numpy.ndarray): center of Labware
        `bottom_left_corner` (Position): bottom left corner of Labware
        `dimensions` (numpy.ndarray): size of Labware
        `exclusion_zone` (BoundingBox): exclusion zone to avoid
        `wells_columns` (dict[str, Well]): wells by columns
        `wells_rows` (dict[str, Well]): wells by rows
        `columns` (dict[int, list[str]]): columns and wells in columns
        `rows` (dict[str, list[str]]): rows and wells in rows
        `at` (SimpleNamespace): namespace of all Wells
        `is_stackable` (bool): whether Labware is stackable
        `is_tiprack` (bool): whether Labware is a tiprack
        `slot_above` (Slot|None): Slot above (for stackable Labware)
    
    ### Class methods:
        `fromConfigs`: factory method to load Labware details from dictionary
        `fromFile`: factory method to load Labware from file
    
    ### Methods:
        `getWell`: get `Well` using its name
        `listColumns`: list wells by columns
        `listRows`: list  wells by rows
        `listWells`: list wells, by columns or rows
        `show`: show Labware on matplotlib axis
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
        self.exclusion_zone = BoundingBox(self.bottom_left_corner, self._dimensions, buffer)
        
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
        Factory method to load Labware details from dictionary

        Args:
            details (dict): dictionary read from Labware file
            parent (Slot|None, optional): parent `Slot` object. Defaults to None.
            
        Returns:
            Labware: `Labware` object
        """
        name = details.get('metadata',{}).get('displayName', '')
        return cls(name=name, _details=details, parent=parent)
    
    @classmethod
    def fromFile(cls, labware_file:str|Path, parent:Slot|None = None, from_repo:bool = True):
        """
        Factory method to load Labware from file

        Args:
            labware_file (str|Path): filepath of Labware file
            parent (Slot|None, optional): parent `Slot` object. Defaults to None.
            from_repo (bool, optional): whether to load from repo. Defaults to True.
        """
        assert isinstance(labware_file,(str,Path)), "Please input a valid filepath"
        filepath = Path(labware_file) if not from_repo else resolve_repo_filepath(labware_file)
        assert filepath.is_file(), "Please input a valid Labware filepath"
        details = read_config_file(filepath)
        return cls.fromConfigs(details=details, parent=parent)
    
    # Properties
    @property
    def details(self) -> dict[str, str|float|tuple[float]]:
        """Dictionary read from Labware file"""
        return self._details
    
    @property
    def reference(self) -> Position:
        """Reference point of `Slot`"""
        return self.parent.bottom_left_corner if isinstance(self.parent, Slot) else Position()
        
    @property
    def offset(self) -> np.ndarray:
        """Labware offset from Slot reference point"""
        return np.array((self.x,self.y,self.z))
    
    @property
    def center(self) -> np.ndarray:
        """Center of Labware"""
        return self.bottom_left_corner.coordinates + self.bottom_left_corner.Rotation.apply(self.offset)
    
    @property
    def bottom_left_corner(self) -> Position:
        """Bottom left corner of Labware"""
        return self.reference
    
    @property
    def dimensions(self) -> np.ndarray:
        """Size of Labware"""
        return self.bottom_left_corner.Rotation.apply(self._dimensions)
    
    @property
    def columns(self) -> dict[int, list[str]]:
        """Columns and wells in columns"""
        return {i+1: ordering for i,ordering in enumerate(self._ordering)}
    
    @property
    def rows(self) -> dict[str, list[str]]:
        """Rows and wells in rows"""
        first_column = self._ordering[0]
        rows_list = self.listRows()
        return {name[0]: rows_list[r] for r,name in enumerate(first_column)}
       
    @property
    def wells_columns(self) -> dict[str, list[Well]]:
        """Wells by columns"""
        return self._wells
    
    @property
    def wells_rows(self) -> dict[str, list[Well]]:
        """Wells by rows"""
        return {name:self._wells[name] for row in self.listRows() for name in row}

    @property
    def at(self) -> SimpleNamespace:
        """Namespace of all wells"""
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
        """List wells by columns"""
        return self._ordering
    
    def listRows(self) -> list[list[str]]:
        """List wells by rows"""
        return [list(r) for r in zip(*self._ordering)]
    
    def listWells(self, by:str) -> list[Well]:
        """
        List wells, by columns or rows
        
        Args:
            by (str): 'columns' or 'rows'
            
        Returns:
            list[Well]: list of `Well` objects
        """
        if by in ('c','col','cols','column','columns'):
            return self.wells_columns
        elif by in ('r','row','rows'):
            return self.wells_rows
        raise ValueError(f"Invalid argument: {by}")
    
    def show(self, zoom_out:bool = False) -> plt.Figure:
        """
        Show Labware on matplotlib axis
        
        Args:
            zoom_out (bool, optional): whether to use zoomed out view. Defaults to False.
            
        Returns:
            matplotlib.pyplot.Figure: matplotlib figure
        """
        fig, ax = plt.subplots()
        self._draw(ax=ax, zoom_out=zoom_out)
        
        reference = self.bottom_left_corner.coordinates
        lower_buffer = self.dimensions if zoom_out else np.array((0,0,0))
        upper_buffer = 2*self.dimensions if zoom_out else self.dimensions
        lower_bounds = reference - lower_buffer
        upper_bounds = reference + upper_buffer
        ax.set_xlim(min(lower_bounds[0],upper_bounds[0]), max(lower_bounds[0],upper_bounds[0]))
        ax.set_ylim(min(lower_bounds[1],upper_bounds[1]), max(lower_bounds[1],upper_bounds[1]))
        
        x_inch,y_inch = fig.get_size_inches()
        inches_per_line = max(x_inch/self.dimensions[0], y_inch/self.dimensions[1])
        new_size = tuple(abs(np.array(self.dimensions[:2]) * inches_per_line))
        fig.set_size_inches(new_size)
        return fig
        
    def _draw(self, ax:plt.Axes, zoom_out:bool = False, **kwargs):
        """
        Draw Labware on matplotlib axis
        
        Args:
            ax (matplotlib.pyplot.Axes): plot axes
            zoom_out (bool, optional): whether to use zoomed out view. Defaults to False.
        """
        ax.add_patch(plt.Rectangle(self.bottom_left_corner.coordinates, *self.dimensions[:2], fill=False, **kwargs))
        for well in self._wells.values():
            well._draw(ax, zoom_out=zoom_out, **kwargs)
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
    """
    `Slot` represents a single Slot object on a `Deck` object or another `Labware` object (for stackable Labware)

    ### Constructor:
        `name` (str): name of Slot
        `_details` (dict[str, Any]): dictionary read from Deck file
        `parent` (Deck|Labware): parent `Deck` or `Labware` object
        
    ### Attributes and properties:
        `name` (str): name of Slot
        `details` (dict[str, Any]): dictionary read from Slot file
        `parent` (Deck|Labware): parent `Deck` or `Labware` object
        `reference` (Position): reference point of parent `Deck` or `Labware`
        `x` (float): x offset
        `y` (float): y offset
        `z` (float): z offset
        `offset` (numpy.ndarray): Slot offset from parent reference point
        `center` (numpy.ndarray): center of Slot
        `bottom_left_corner` (Position): bottom left corner of Slot
        `dimensions` (numpy.ndarray): size of Slot
        `exclusion_zone` (BoundingBox): exclusion zone of loaded Labware to avoid
        `loaded_labware` (Labware|None): Labware loaded in Slot
        `slot_above` (Slot|None): Slot above
        `slot_below` (Slot|None): Slot below
        
    ### Methods:
        `loadLabware`: load Labware in Slot
        `loadLabwareFromConfigs`: load Labware from dictionary
        `loadLabwareFromFile`: load Labware from file
        `removeLabware`: remove Labware from Slot
    """
    
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
        new_corner_offset = self.reference.coordinates + self.reference.Rotation.apply(corner_offset)
        orientation = self._details.get('orientation',(0,0,0))
        bottom_left_corner = Position(new_corner_offset, Rotation.from_euler('zyx',orientation,degrees=True))
        self.bottom_left_corner = bottom_left_corner.orientate(self.reference.Rotation)
        
        dimensions = np.array(self._details.get('dimensions',self._dimensions))
        self.x,self.y,self.z = dimensions/2
        self._dimensions = tuple(dimensions)
        
        labware_file = Path(self._details.get('labware_file',''))
        labware_file = resolve_repo_filepath(labware_file) if not labware_file.is_absolute() else labware_file
        if labware_file.is_file():
            self.loadLabwareFromFile(labware_file=labware_file)
            assert isinstance(self.loaded_labware, Labware), "Labware not loaded"
            self.loaded_labware.exclusion_zone = BoundingBox(
                self.loaded_labware.bottom_left_corner, 
                self.loaded_labware._dimensions, 
                self._details.get('labware_boundary_buffer', ((0,0,0),(0,0,0)))
            )
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
    
    # Properties
    @property
    def details(self) -> dict[str, str|float|tuple[float]]:
        """Dictionary read from Deck file"""
        return self._details
    
    @property
    def reference(self) -> Position:
        """Reference point of parent `Deck` or `Labware`"""
        return self.parent.bottom_left_corner
    
    @property
    def offset(self) -> np.ndarray:
        """Slot offset from parent reference point"""
        return np.array((self.x,self.y,self.z))
    
    @property
    def center(self) -> np.ndarray:
        """Center of Slot"""
        return self.bottom_left_corner.coordinates + self.bottom_left_corner.Rotation.apply(self.offset)
    
    @property
    def dimensions(self) -> np.ndarray:
        """Size of Slot"""
        return self.bottom_left_corner.Rotation.apply(self._dimensions)
    
    @property
    def exclusion_zone(self) -> BoundingBox|None:
        """Exclusion zone of loaded Labware to avoid"""
        return self.loaded_labware.exclusion_zone if isinstance(self.loaded_labware, Labware) else None

    def loadLabware(self, labware:Labware):
        """
        Load Labware in Slot

        Args:
            labware (Labware): `Labware` object
        """
        assert self.loaded_labware is None, "Labware already loaded in slot"
        labware.parent = self
        self.loaded_labware = labware
        self.slot_above = self.loaded_labware.slot_above
        return
    
    def loadLabwareFromConfigs(self, details:dict[str, Any]):
        """
        Load Labware from dictionary
        
        Args:
            details (dict): dictionary read from Labware file
        """
        labware = Labware.fromConfigs(details=details, parent=self)
        return self.loadLabware(labware=labware)
        
    def loadLabwareFromFile(self, labware_file:str, from_repo:bool = True):
        """
        Load Labware from file
        
        Args:
            labware_file (str): filepath of Labware file
            from_repo (bool, optional): whether to load from repo. Defaults to True.
        """
        labware = Labware.fromFile(labware_file=labware_file, parent=self, from_repo=from_repo)
        return self.loadLabware(labware=labware)
        
    def removeLabware(self) -> Labware:
        """
        Remove Labware from Slot
        
        Returns:
            Labware: `Labware` object
        """
        assert self.loaded_labware is not None, "No Labware loaded in slot"
        if self.loaded_labware.is_stackable:
            assert self.loaded_labware.slot_above.loaded_labware is None, "Another Labware is stacked above"
            self.loaded_labware.slot_above.slot_below = None
        labware = self.loaded_labware
        self.loaded_labware = None
        self.slot_above = None
        return labware

    def _draw(self, ax:plt.Axes, zoom_out:bool = False, **kwargs):
        """
        Draw Slot on matplotlib axis
        
        Args:
            ax (matplotlib.pyplot.Axes): plot axes
            zoom_out (bool, optional): whether to use zoomed out view. Defaults to False.
        """
        ax.add_patch(plt.Rectangle(self.bottom_left_corner.coordinates, *self.dimensions[:2], fill=False, linestyle=":", **kwargs))
        if  isinstance(self.loaded_labware, Labware):
            self.loaded_labware._draw(ax, zoom_out=zoom_out,**kwargs)
        elif not zoom_out:
            ax.text(
                *self.center[:2], self.name, 
                ha='center', va='center', 
                rotation=self.bottom_left_corner.rotation[0], 
                fontsize=8, color='black', alpha=0.25
            )
        return

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

@dataclass
class Deck:
    """
    `Deck` represents a single Deck object
    
    ### Constructor:
        `name` (str): name of Deck
        `_details` (dict[str, Any]): dictionary read from Deck file
        `parent` (Deck|None, optional): parent `Deck` object. Defaults to None.
        `_nesting_lineage` (tuple[Path]): lineage of nested decks
        
    ### Attributes and properties:
        `name` (str): name of Deck
        `details` (dict[str, Any]): dictionary read from Deck file
        `parent` (Deck|None): parent `Deck` object
        `reference` (Position): reference point of `Deck`
        `x` (float): x offset
        `y` (float): y offset
        `z` (float): z offset
        `offset` (numpy.ndarray): Deck offset from parent `Deck` reference point
        `center` (numpy.ndarray): center of Deck
        `bottom_left_corner` (Position): bottom left corner of Deck
        `dimensions` (numpy.ndarray): size of Deck
        `exclusion_zone` (dict[str, BoundingBox]): exclusion zones to avoid
        `slots` (dict[str, Slot]): contained `Slot` objects
        `zones` (dict[str, Deck]): nested `Deck` objects
        `at` (SimpleNamespace): namespace of all Slots
        `on` (SimpleNamespace): namespace of all nested Decks
        
    ### Class methods:
        `fromConfigs`: factory method to load Deck details from dictionary
        `fromFile`: factory method to load Deck from file
        
    ### Methods:
        `getSlot`: get `Slot` using its name or index
        `isExcluded`: checks and returns whether the coordinates are in an excluded region
        `loadNestedDeck`: load nested `Deck` object from dictionary
        `loadLabware`: load `Labware` into `Slot`
        `removeLabware`: remove Labware from `Slot` using its name or index
        `transferLabware`: transfer Labware between Slots
        `show`: show Deck on matplotlib axis
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
        new_corner_offset = self.reference.coordinates + self.reference.Rotation.apply(corner_offset)
        orientation = self._details.get('orientation',(0,0,0))
        bottom_left_corner = Position(new_corner_offset, Rotation.from_euler('zyx',orientation,degrees=True))
        self.bottom_left_corner = bottom_left_corner.orientate(self.reference.Rotation)
        
        self._slots = {f"slot_{int(idx):02}":Slot(name=f"slot_{int(idx):02}", _details=details, parent=self) for idx,details in self._details.get('slots',{}).items()}
        for name,details in self._details.get('zones',{}).items():
            deck_file = Path(details.get('deck_file',''))
            deck_file = resolve_repo_filepath(deck_file) if not deck_file.is_absolute() else deck_file
            if deck_file.is_file():
                parent_lineage = self.parent._nesting_lineage if isinstance(self.parent,Deck) else self._nesting_lineage
                if deck_file in parent_lineage:
                    parent_str = '\n+ '.join([p.as_uri() for p in parent_lineage if p is not None])
                    logger.error(f"Nested deck lineage:\n{parent_str}")
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
    def fromConfigs(cls, details:dict[str, Any], parent:Deck|None = None, _nesting_lineage:Sequence[Path|None]=(None,)):
        """
        Factory method to load Deck details from dictionary
        
        Args:
            details (dict): dictionary read from Deck file
            parent (Deck|None, optional): parent `Deck` object. Defaults to None.
            _nesting_lineage (Sequence[Path|None], optional): lineage of nested decks. Defaults to (None,).
            
        Returns:
            Deck: `Deck` object
        """
        name = details.get('name',None)
        name = details.get('metadata',{}).get('displayName', '') if name is None else name
        return cls(name=name, _details=details, parent=parent, _nesting_lineage=tuple(_nesting_lineage))
    
    @classmethod
    def fromFile(cls, deck_file:str, parent:Deck|None = None, from_repo:bool = True):
        """
        Factory method to load Deck from file
        
        Args:
            deck_file (str): filepath of Deck file
            parent (Deck|None, optional): parent `Deck` object. Defaults to None.
            from_repo (bool, optional): whether to load from repo. Defaults to True.
            
        Returns:
            Deck: `Deck` object
        """
        assert isinstance(deck_file,(str,Path)), "Please input a valid filepath"
        filepath = Path(deck_file) if not from_repo else resolve_repo_filepath(deck_file)
        assert filepath.is_file(), "Please input a valid Deck filepath"
        details = read_config_file(filepath)
        return cls.fromConfigs(details=details, parent=parent, _nesting_lineage=(filepath,))
    
    # Properties
    @property
    def reference(self) -> Position:
        """Reference point of `Deck`"""
        return self.parent.bottom_left_corner if isinstance(self.parent, Deck) else Position()
    
    @property
    def offset(self) -> np.ndarray:
        """Deck offset from parent `Deck` reference point"""
        return np.array((self.x,self.y,self.z))
    
    @property
    def center(self) -> np.ndarray:
        """Center of Deck"""
        return self.bottom_left_corner.coordinates + self.bottom_left_corner.Rotation.apply(self.offset)
    
    @property
    def dimensions(self) -> np.ndarray:
        """Size of Deck"""
        return self.bottom_left_corner.Rotation.apply(self._dimensions)
    
    @property
    def exclusion_zone(self) -> dict[str, BoundingBox]:
        """Exclusion zones to avoid"""
        bounds = dict()
        for slot in self._slots.values():
            if not isinstance(slot, Slot):
                continue
            if not isinstance(slot.loaded_labware, Labware):
                continue
            bounds[slot.name] = slot.loaded_labware.exclusion_zone
        for zone_name, zone in self._zones.items():
            for name,bound in zone.exclusion_zone.items():
                bounds[f"{zone_name}_{name}"] = bound
        return bounds
    
    @property
    def slots(self) -> dict[str, Slot]:
        """Contained `Slot` objects"""
        return self._slots
    
    @property
    def zones(self) -> dict[str, Deck]:
        """Nested `Deck` objects"""
        return self._zones
    
    @property
    def at(self) -> SimpleNamespace:
        """Namespace of all Slots"""
        return SimpleNamespace(**self._slots)
    
    @property
    def on(self) -> SimpleNamespace:
        """Namespace of all nested Decks"""
        return SimpleNamespace(**self._zones)
    
    def getSlot(self, value:int|str) -> Slot|None:
        """
        Get Labware in slot using slot id or name
        
        Args:
            value (int|str): slot id or name
            
        Returns:
            Slot: `Slot` object
        """
        if isinstance(value, int):
            value = f"slot_{value:02}"
        return self._slots.get(value, None)
    
    def isExcluded(self, coordinates:Sequence[float]|np.ndarray) -> bool:
        """
        Checks and returns whether the coordinates are in an excluded region
        
        Args:
            coordinates (Sequence[float]|numpy.ndarray): x,y,z coordinates
            
        Returns:
            bool: whether coordinates are in an excluded region
        """
        assert len(coordinates) == 3, "Please input valid x,y,z coordinates"
        collides_with = []
        for name,bounds in self.exclusion_zone.items():
            if coordinates in bounds:
                collides_with.append(name)
        if len(collides_with) == 0:
            return False
        logger.warning(f"Coordinates {tuple(coordinates)} collides with {collides_with}")
        return True
    
    def loadNestedDeck(self, name:str, details:dict[str, Any]):
        """
        Load nested `Deck` object from dictionary
        
        Args:
            name (str): name of nested `Deck`
            details (dict): dictionary read from Deck file
        """
        deck_file = Path(details.pop('deck_file',''))
        deck_file = resolve_repo_filepath(deck_file) if not deck_file.is_absolute() else deck_file
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
        """
        Show Deck on matplotlib axis
        
        Args:
            zoom_out (bool, optional): whether to use zoomed out view. Defaults to False.
            
        Returns:
            matplotlib.pyplot.Figure: matplotlib figure
        """
        fig, ax = plt.subplots()
        color_map = {v:k for k,v in mcolors.get_named_colors_mapping().items()}
        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        color_iterator = iter([color_map[c] for c in colors])
        color_iterator = itertools.chain(['none'], color_iterator, itertools.cycle(['black']))
        self._draw(ax=ax, zoom_out=zoom_out, color_iterator=color_iterator)
        
        reference = self.bottom_left_corner.coordinates
        lower_buffer = self.dimensions if zoom_out else np.array((0,0,0))
        upper_buffer = 2*self.dimensions if zoom_out else self.dimensions
        lower_bounds = reference - lower_buffer
        upper_bounds = reference + upper_buffer
        ax.set_xlim(min(lower_bounds[0],upper_bounds[0]), max(lower_bounds[0],upper_bounds[0]))
        ax.set_ylim(min(lower_bounds[1],upper_bounds[1]), max(lower_bounds[1],upper_bounds[1]))
        x_inch,y_inch = fig.get_size_inches()
        inches_per_line = max(x_inch/self.dimensions[0], y_inch/self.dimensions[1])
        new_size = tuple(abs(np.array(self.dimensions[:2]) * inches_per_line))
        fig.set_size_inches(new_size)
        return fig
    
    def _draw(self, ax: plt.Axes, zoom_out:bool = False, *, color_iterator:Iterator|None = None, **kwargs):
        """
        Draw Deck on matplotlib axis
        
        Args:
            ax (matplotlib.pyplot.Axes): plot axes
            zoom_out (bool, optional): whether to use zoomed out view. Defaults to False.
            color_iterator (Iterator|None, optional): iterator for colors. Defaults to None.
        """
        bg_color = next(color_iterator) if isinstance(color_iterator,Iterator) else None
        ax.add_patch(plt.Rectangle(self.bottom_left_corner.coordinates, *self.dimensions[:2], alpha=0.5, color=bg_color, **kwargs))
        ax.add_patch(plt.Rectangle(self.bottom_left_corner.coordinates, *self.dimensions[:2], fill=False, **kwargs))
        print(f"{bg_color.replace('tab:','')} -> {self.name.replace('_sub','.')}")
        for zone in self._zones.values():
            if isinstance(zone, Deck):
                zone._draw(ax, zoom_out=zoom_out, color_iterator=color_iterator, **kwargs)
        
        def draw_slots(ax, slots:dict[str, Slot|SimpleNamespace], **kwargs):
            for slot in slots.values():
                if isinstance(slot, Slot):
                    slot._draw(ax, zoom_out=zoom_out, **kwargs)
            return
        draw_slots(ax, self._slots, **kwargs)
        return
    
    def loadLabware(self, dst_slot: Slot, labware:Labware):
        """
        Load `Labware` into `Slot`
        
        Args:
            dst_slot (Slot): destination `Slot` object
            labware (Labware): `Labware` object
        """
        assert isinstance(dst_slot, Slot), "Please input a valid slot"
        dst_slot.loadLabware(labware=labware)
        return
    
    def removeLabware(self, src_slot:Slot) -> Labware:
        """
        Remove Labware from `Slot` using its name or index
        
        Args:
            src_slot (Slot): source `Slot` object
            
        Returns:
            Labware: `Labware` object
        """
        assert isinstance(src_slot, Slot), "Please input a valid slot"
        return src_slot.removeLabware()
    
    def transferLabware(self, src_slot:Slot, dst_slot:Slot):
        """
        Transfer Labware between Slots
        
        Args:
            src_slot (Slot): source `Slot` object
            dst_slot (Slot): destination `Slot` object
        """
        assert isinstance(src_slot, Slot), "Please input a valid source slot"
        assert isinstance(dst_slot, Slot), "Please input a valid destination slot"
        labware = src_slot.removeLabware()
        dst_slot.loadLabware(labware=labware)
        return
    
    
    
    # Deprecated methods
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
        raise DeprecationWarning("Method to be deprecated.")
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
        raise DeprecationWarning("Method to be deprecated.")
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
        raise DeprecationWarning("Method to be deprecated.")
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
        raise DeprecationWarning("Method to be deprecated.")
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
    """
    `BoundingBox` represents a single BoundingBox object

    ### Constructor:
        `reference` (Position, optional): reference point. Defaults to Position().
        `dimensions` (Sequence[float]|numpy.ndarray, optional): x,y,z dimensions. Defaults to (0,0,0).
        `buffer` (Sequence[Sequence[float]]|numpy.ndarray, optional): lower and upper buffer. Defaults to ((0,0,0),(0,0,0)).
        
    ### Attributes and properties:
        `reference` (Position): reference point
        `dimensions` (numpy.ndarray): x,y,z dimensions
        `buffer` (numpy.ndarray): lower and upper buffer
        `bounds` (numpy.ndarray): lower and upper bounds
        
    ### Methods:
        `contains`: check if point is within BoundingBox
    """
    
    reference: Position = field(default_factory=Position)
    dimensions: Sequence[float]|np.ndarray = (0,0,0)
    buffer: Sequence[Sequence[float]]|np.ndarray = ((0,0,0),(0,0,0))
    
    def __post_init__(self):
        assert isinstance(self.reference, Position), "Please input a valid reference position of type `Position`"
        assert isinstance(self.dimensions, (Sequence,np.ndarray)), "Please input Sequence or numpy.ndarray for x,y,z dimensions"
        assert isinstance(self.buffer, (Sequence,np.ndarray)), "Please input Sequence or numpy.ndarray lower and upper buffer"
        
        assert len(self.dimensions) == 3, "Please input x,y,z dimensions"
        assert len(self.buffer) == 2, "Please input lower and upper buffer"
        assert all([len(b) == 3 for b in self.buffer]), "Please input x,y,z buffer"
        self.dimensions = np.array(self.dimensions)
        self.buffer = np.array(self.buffer)
        return
    
    def __contains__(self, point:Sequence[float]) -> bool:
        return self.contains(point=point)
    
    @property
    def bounds(self):
        """Lower and upper bounds"""
        dimensions = self.reference.Rotation.apply(self.dimensions)
        other_corner = self.reference.coordinates + dimensions
        bounds = np.array([self.reference.coordinates, other_corner])
        return bounds + self.reference.Rotation.apply(self.buffer)
    
    def contains(self, point:Sequence[float]|np.ndarray) -> bool:
        """
        Check if point is within BoundingBox
        
        Args:
            point (Sequence[float]|numpy.ndarray): x,y,z coordinates
            
        Returns:
            bool: whether point is within BoundingBox
        """
        assert len(point) == 3, "Please input x,y,z coordinates"
        return all([min(b) <= p <= max(b) for b,p in zip(list(zip(*self.bounds)), point)])
