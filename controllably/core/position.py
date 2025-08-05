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
    `BoundingVolume`: represents a 3D bounding volume
    `BoundingBox`: represents a 3D bounding box
    
## Functions:
    `convert_to_position`: Convert a value to a `Position` object
    `get_transform`: Get transformation matrix from initial to final points, with the first point in each set being the center of rotation

<i>Documentation last updated: 2025-06-11</i>
"""
# Standard library imports
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
import itertools
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Sequence, Any, Iterator, Callable

# Third party imports
import matplotlib
from matplotlib.collections import PatchCollection
import matplotlib.colors as mcolors
import matplotlib.patches
import matplotlib.pyplot as plt
import numpy as np
import parse
from scipy.spatial.transform import Rotation

# Local application imports
from . import file_handler

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)
CustomLevelFilter().setModuleLevel(__name__, logging.INFO)

MTP_DIMENSIONS = (127.76,85.48,0)
"""Microtiter plate dimensions in mm"""
OBB_DIMENSIONS = (300,300,0)
"""Optical Breadboard dimensions in mm"""

def convert_to_position(value:Sequence|np.ndarray) -> Position:
    """
    Convert a value to a `Position` object

    Args:
        value (Sequence[float]|numpy.ndarray|Position): value to convert

    Returns:
        Position: converted `Position` object
    """
    if isinstance(value, Position):
        return value
    assert isinstance(value, (Sequence,np.ndarray)), "Please input a valid value to be converted to Position"
    
    if isinstance(value, np.ndarray):
        if len(value.shape) == 1:
            return Position(value)
        elif len(value.shape) == 2:
            return Position(value[0], Rotation.from_euler('zyx',value[1],degrees=True))
    
    if not isinstance(value[0], (Sequence,np.ndarray)):
        return Position(value)
    
    assert len(value) in (1,2), "Please input a valid value to be converted to Position, comprising at most 2 Sequences"
    if len(value) == 1:
        return Position(value[0])
    
    assert len(value[1]) in (3,4), "Please input a valid rotation using either euler angles or quaternion"
    rotation = Rotation.from_euler('zyx',value[1],degrees=True) if len(value[1]) == 3 else Rotation.from_quat(value[1])
    return Position(value[0], rotation)

def get_transform(initial_points: np.ndarray, final_points:np.ndarray) -> tuple[Position,float]:
    """
    Get transformation matrix from initial to final points, with the first point in each set being the center of rotation.

    Args:
        initial_points (numpy.ndarray): initial points
        final_points (numpy.ndarray): final points

    Returns:
        tuple[Position,float]: transformation Position (i.e. vector and rotation) and scale factor
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
        `rotation_type` (str, optional): preferred representation of rotation (quaternion, matrix, angle_axis, euler, mrp). Defaults to 'euler'.
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
        `fromJSON`: create a `Position` object from string
        `toJSON`: convert `Position` to string
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
        assert self.rotation_type in ['quaternion','matrix','angle_axis','euler','mrp'], f"Invalid rotation type: {self.rotation_type}"
        assert isinstance(self._coordinates,(Sequence,np.ndarray)) and len(self._coordinates) == 3, "Please input x,y,z coordinates"
        self._coordinates = tuple(self._coordinates)
        return
    
    def __str__(self):
        return f"{self.coordinates} | {self.rotation} ({self.rotation_type})"
    
    def __repr__(self):
        return f"{self.coordinates}|{self.rotation}"
    
    def __eq__(self, value: Position) -> bool:
        if not isinstance(value, Position):
            return False
        return np.allclose(self.coordinates, value.coordinates) and np.allclose(self.Rotation.as_quat(), value.Rotation.as_quat())
    
    @staticmethod
    def fromArray(value:Sequence|np.ndarray) -> Position:
        """
        Create a `Position` object from coordinates and rotation

        Args:
            value (Sequence[float]|numpy.ndarray): x,y,z coordinates or [x,y,z,rotation]

        Returns:
            Position: `Position` object
        """
        return convert_to_position(value)
    
    @staticmethod
    def fromJSON(value:str) -> Position:
        """
        Create a `Position` object from string

        Args:
            value (str): string representation of `Position`

        Returns:
            Position: `Position` object
        """
        assert isinstance(value, str), "Please input a valid string"
        coord_str, quat_str, order = parse.parse("Position(({}), ({}) [{}])", value)
        coord = tuple(map(float, coord_str.split(', ')))
        quat = tuple(map(float, quat_str.split(', ')))
        if order == 'wxyz':
            scalar_first = True
        elif order == 'xyzw':
            scalar_first = False
        else:
            raise ValueError(f"Invalid quaternion order: {order}")
        return Position(coord, Rotation.from_quat(quat, scalar_first=scalar_first))
    
    def toJSON(self, *, scalar_first: bool = False) -> str:
        order = 'wxyz' if scalar_first else 'xyzw'
        coord = tuple(map(float, self._coordinates))
        quat = tuple(map(float, self.Rotation.as_quat(scalar_first=scalar_first)))
        return f"Position({coord}, {quat} [{order}])"
        
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
    
    def apply(self, other:Position, inplace:bool = True) -> Position:
        """
        Apply self to other `Position`, first translating and then orientating

        Args:
            other (Position): other `Position`
            inplace (bool, optional): whether to update self in place. Defaults to True.

        Returns:
            Position: other `Position` transformed by self
        """
        return other.translate(self.coordinates, inplace=inplace).orientate(self.Rotation, inplace=inplace)
    
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
    
    def _draw(self, ax: plt.Axes, zoom_out:bool = False, **kwargs) -> matplotlib.patches.Patch|None:
        """
        Draw self on matplotlib axis

        Args:
            ax (matplotlib.pyplot.Axes): plot axes
            zoom_out (bool, optional): whether to use zoomed out view. Defaults to False.
            
        Returns:
            matplotlib.patches.Patch|None: matplotlib patch
        """
        if self.shape == 'circular':
            patch = plt.Circle(self.center, self.dimensions[0]/2, fill=False, **kwargs)
            # ax.add_patch(patch)
            return patch
        elif self.shape == 'rectangular':
            dimensions = self.reference.Rotation.apply(np.array([*self.dimensions,0]))
            corner = self.bottom - dimensions/2
            patch = plt.Rectangle(corner[:2], *dimensions[:2], fill=False, **kwargs)
            # ax.add_patch(plt.Rectangle(corner[:2], *dimensions[:2], fill=False, **kwargs))
            return patch
        else:
            logger.error(f"Invalid shape: {self.shape}")
        return


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
        `native` (Labware): native Labware object (i.e. without parent)
        `details` (dict[str, Any]): dictionary read from Labware file
        `parent` (Slot|None): parent `Slot` object
        `reference` (Position): reference point of `Slot`
        `x` (float): x offset
        `y` (float): y offset
        `z` (float): z offset
        `offset` (numpy.ndarray): Labware offset from Slot reference point
        `center` (numpy.ndarray): center of Labware
        `top` (numpy.ndarray): top of Labware
        `bottom_left_corner` (Position): bottom left corner of Labware
        `dimensions` (numpy.ndarray): size of Labware
        `exclusion_zone` (BoundingBox): exclusion zone to avoid
        `wells` (dict[str, Well]): wells by columns (alias for `wells_columns`)
        `wells_columns` (dict[str, Well]): wells by columns
        `wells_rows` (dict[str, Well]): wells by rows
        `columns` (dict[int, list[str]]): columns and wells in columns
        `rows` (dict[str, list[str]]): rows and wells in rows
        `at` (SimpleNamespace): namespace of all Wells
        `is_stackable` (bool): whether Labware is stackable
        `is_tiprack` (bool): whether Labware is a tiprack
        `slot_above` (Slot|None): Slot above (for stackable Labware)
    
    ### Methods:
        `fromConfigs`: factory method to load Labware details from dictionary
        `fromFile`: factory method to load Labware from file
        `fromTop`: offset from top of Labware
        `getAllPositions`: get all positions in Labware
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
    _is_stackable: bool = field(init=False, default=False)
    is_tiprack: bool = field(init=False, default=False)
    slot_above: Slot|None = field(init=False, default=None)
    
    def __post_init__(self):
        dimensions = self._details.get('dimensions',{})
        self.x = dimensions.get('xDimension', 0)/2
        self.y = dimensions.get('yDimension', 0)/2
        self.z = dimensions.get('zDimension', 0)/2
        self._dimensions = (self.x*2,self.y*2,self.z*2)
        self.is_tiprack = self._details.get('parameters',{}).get('isTiprack', False)
        self._ordering = self._details.get('ordering', [[]])
        self._wells = {name:Well(name=name, _details=details, parent=self) for name,details in self._details.get('wells',{}).items()}
        
        controllably_details = self._details.get('controllably', {})
        is_stackable = controllably_details.get('parameters',{}).get('isStackable', None) 
        is_stackable = self._details.get('parameters',{}).get('isStackable', False) if is_stackable is None else is_stackable
        self._is_stackable = is_stackable
        
        buffer = controllably_details.get('exclusionBuffer', None)
        buffer = self._details.get('exclusionBuffer', ((0,0,0),(0,0,0))) if buffer is None else buffer
        self.exclusion_zone = BoundingBox(
            reference=self.bottom_left_corner, 
            dimensions=self._dimensions, 
            buffer=buffer
        )
        
        if self.is_stackable:
            self._add_slot_above()
        return
    
    def __repr__(self) -> str:
        parent_info = "None" if self.parent is None else f"{self.parent.name} ({self.parent.__class__.__name__}:{id(self.parent)})"
        return f"{self.name} ({self.__class__.__name__}:{id(self)}) -> {parent_info}" 
    
    def __str__(self) -> str:
        parent_info = "" if self.parent is None else f"on {self.parent.name}"
        return f"{self.name} ({len(self._wells)}x) {parent_info}" 
    
    @classmethod
    def fromConfigs(cls, details:dict[str, Any], parent:Slot|None = None) -> Labware:
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
        filepath = Path(labware_file)
        filepath = filepath if filepath.is_absolute() else file_handler.resolve_repo_filepath(labware_file)
        assert filepath.is_file(), "Please input a valid Labware filepath"
        details = file_handler.read_config_file(filepath)
        details['labware_file'] = str(filepath)
        return cls.fromConfigs(details=details, parent=parent)
    
    # Properties
    @property
    def native(self) -> Labware:
        """Native Labware object (i.e. without parent)"""
        filepath = self._details.get('labware_file',None)
        return Labware.fromFile(file_handler.resolve_repo_filepath(filepath)) if filepath else deepcopy(self)
    
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
    def top(self) -> np.ndarray:
        """Top of Labware"""
        return self.center + np.array((0,0,self.z))
    
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
    def wells(self) -> dict[str, Well]:
        """Wells by columns (alias for `wells_columns`)"""
        return self._wells
    
    @property
    def wells_columns(self) -> dict[str, Well]:
        """Wells by columns"""
        return self._wells
    
    @property
    def wells_rows(self) -> dict[str, Well]:
        """Wells by rows"""
        return {name:self._wells[name] for row in self.listRows() for name in row}

    @property
    def at(self) -> SimpleNamespace:
        """Namespace of all wells"""
        return SimpleNamespace(**self._wells)
    
    @property
    def is_stackable(self) -> bool:
        """Whether Labware is stackable"""
        return self._is_stackable
    @is_stackable.setter
    def is_stackable(self, value:bool):
        old_value = self._is_stackable
        self._is_stackable = value
        try:
            _ = self._add_slot_above() if value else self._delete_slot_above()
        except AssertionError as e:
            self._is_stackable = old_value
            raise e
        return
    
    def fromTop(self, offset:Sequence[float]|np.ndarray) -> np.ndarray:
        """
        Offset from top of Labware

        Args:
            offset (Sequence[float]|numpy.ndarray): x,y,z offset

        Returns:
            tuple: top of Labware with offset
        """
        return self.top + np.array(offset)

    def getAllPositions(self) -> dict[str, tuple[float]|dict[str, tuple[float]|float]]:
        """
        Get all positions in Labware
        
        Returns:
            dict[str, tuple[float]: dictionary of all positions
        """
        positions = dict()
        positions['self'] = tuple(self.top)
        for well in self._wells.values():
            positions[well.name.replace(' ','_')] = dict(
                top = tuple(well.top), 
                bottom = tuple(well.bottom), 
                dimensions = well.dimensions,
                depth = well.depth
            )
        return positions

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
    
    def listWells(self, by:str = 'col') -> list[Well]:
        """
        List wells, by columns or rows
        
        Args:
            by (str, optional): 'columns' or 'rows'. Defaults to 'col'.
            
        Returns:
            list[Well]: list of `Well` objects
        """
        if by in ('c','col','cols','column','columns'):
            return list(self.wells_columns.values())
        elif by in ('r','row','rows'):
            return list(self.wells_rows.values())
        raise ValueError(f"Invalid argument: {by}")
    
    def _add_slot_above(self) -> Slot|None:
        """ 
        Add Slot above for stackable Labware
        
        Returns:
            Slot|None: Slot above
        """
        details_above = self._details.get('controllably',{}).get('slotAbove',None)
        details_above = self._details.get('slotAbove',{}) if details_above is None else details_above
        assert self.is_stackable, "Labware is not stackable"
        assert len(details_above) > 0, "No details for Slot above"
        below_name = self.parent.name if isinstance(self.parent, Slot) else 'slot'
        above_name = below_name[:-1] + chr(ord(below_name[-1]) + 1)
        if below_name[-1].isdigit() or below_name[-2] != '_':
            above_name = below_name + '_a'
        slot_above = Slot(
            name=above_name, 
            _details=details_above, 
            parent=self
        )
        slot_above.slot_below = self.parent
        self.slot_above = slot_above
        if isinstance(self.parent, Slot):
            self.parent._add_slot_above(slot_above)
        return slot_above
    
    def _delete_slot_above(self) -> Slot|None:
        """
        Delete Slot above for stackable Labware
        
        Returns:
            Slot|None: Slot above
        """
        if not isinstance(self.slot_above, Slot):
            return None
        assert isinstance(self.slot_above, Slot), "There is no Slot above to delete"
        assert not isinstance(self.slot_above.loaded_labware, Labware), "Labware is still loaded on the Slot above"
        slot_above = self.slot_above
        self.slot_above = None
        if isinstance(self.parent, Slot):
            self.parent._delete_slot_above()
        return slot_above
    
    def show(self, zoom_out:bool = False) -> tuple[plt.Figure, plt.Axes]:
        """
        Show Labware on matplotlib axis
        
        Args:
            zoom_out (bool, optional): whether to use zoomed out view. Defaults to False.
            
        Returns:
            tuple[matplotlib.pyplot.Figure, matplotlib.pyplot.Axes]: matplotlib figure, axes
        """
        fig, ax = plt.subplots()
        patches = self._draw(ax=ax, zoom_out=zoom_out)
        ax.add_collection(PatchCollection(patches, match_original=True))
        
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
        return fig,ax
        
    def _draw(self, ax:plt.Axes, zoom_out:bool = False, **kwargs) -> list[matplotlib.patches.Patch]:
        """
        Draw Labware on matplotlib axis
        
        Args:
            ax (matplotlib.pyplot.Axes): plot axes
            zoom_out (bool, optional): whether to use zoomed out view. Defaults to False.
        
        Returns:
            list[matplotlib.patches.Patch]: list of matplotlib patches
        """
        patches = []
        patch = plt.Rectangle(self.bottom_left_corner.coordinates, *self.dimensions[:2], fill=False, **kwargs)
        # ax.add_patch(patch)
        patches.append(patch)
        if isinstance(self.slot_above, Slot) and isinstance(self.slot_above.loaded_labware, Labware):
            return self.slot_above.loaded_labware._draw(ax=ax, zoom_out=zoom_out, **kwargs)
        
        for well in self._wells.values():
            patch = well._draw(ax, zoom_out=zoom_out, **kwargs)
            patches.append(patch)
        # ax.add_collection(PatchCollection(patches, match_original=True))
        return patches


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
        `fromCenter`: offset from center of Slot
        `getAllPositions`: get all positions in Slot
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
        
        labware_details = self._details.get('labware_file','')
        if isinstance(labware_details, str) and labware_details.strip() != '':
            labware_file = Path(labware_details)
            labware_file = file_handler.resolve_repo_filepath(labware_file) if not labware_file.is_absolute() else labware_file
            if labware_file.is_file():
                self.loadLabwareFromFile(labware_file=labware_file)
                assert isinstance(self.loaded_labware, Labware), "Labware not loaded"
        elif isinstance(labware_details, list):
            current_top_slot = self
            layers = 0
            for labware_file in labware_details:
                labware_file = Path(labware_file)
                labware_file = file_handler.resolve_repo_filepath(labware_file) if not labware_file.is_absolute() else labware_file
                if not labware_file.is_file():
                    logger.error(f"Labware file '{labware_file}' not found, skipping...")
                    continue
                else:
                    labware = Labware.fromFile(labware_file=labware_file, parent=current_top_slot)
                    current_top_slot.loadLabware(labware=labware)
                    assert isinstance(current_top_slot.loaded_labware, Labware), "Labware not loaded"
                    layers += 1
                    if current_top_slot.loaded_labware.is_stackable and isinstance(current_top_slot.slot_above, Slot):
                        current_top_slot = current_top_slot.slot_above
                    else:
                        logger.warning(f"'{current_top_slot.loaded_labware.name}' in '{current_top_slot.name}' is not stackable or has no defined Slot above")
                        logger.warning(f"Stopped stacking Labware in slot '{self.name}' at layer {layers}")
                        break 
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
        if not isinstance(self.loaded_labware, Labware):
            return None
        exclusion_zone = deepcopy(self.loaded_labware.exclusion_zone)
        if isinstance(self.slot_above, Slot):
            exclusion_zone += self.slot_above.exclusion_zone
        return exclusion_zone
    
    @property
    def stack(self) -> dict[str, Slot]:
        """Stack of Labware in Slot, including Slot above"""
        stack = {self.name: self}
        if isinstance(self.slot_above, Slot):
            stack.update(self.slot_above.stack)
        return stack
    
    def fromCenter(self, offset:Sequence[float]|np.ndarray) -> np.ndarray:
        """
        Offset from center of Slot

        Args:
            offset (Sequence[float]|numpy.ndarray): x,y,z offset

        Returns:
            tuple: center of Slot with offset
        """
        return self.center + np.array(offset)
    
    def getAllPositions(self) -> dict[str, tuple[float]|dict]:
        """
        Get all positions in Slot
        
        Returns:
            dict[str, tuple[float]]: dictionary of all positions
        """
        positions = dict()
        positions['self'] = tuple(self.center)
        if isinstance(self.loaded_labware, Labware):
            positions['labware'] = self.loaded_labware.getAllPositions()
        return positions

    def loadLabware(self, labware:Labware):
        """
        Load Labware in Slot

        Args:
            labware (Labware): `Labware` object
        """
        assert self.loaded_labware is None, "Labware already loaded in slot"
        labware.parent = self
        labware.is_stackable = labware.is_stackable
        self.loaded_labware = labware
        if isinstance(self.loaded_labware.slot_above, Slot):
            self._add_slot_above(self.loaded_labware.slot_above)
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
        labware.parent = None
        self.loaded_labware = None
        self._delete_slot_above()
        return labware
    
    def _add_slot_above(self, slot_above: Slot, directly:bool = True) -> Slot|None:
        """ 
        Add Slot above of stack
        
        Args:
            slot_above (Slot): Slot above
            directly (bool, optional): whether to add slot directly above itself. Defaults to True.
        
        Returns:
            Slot|None: Slot above
        """
        if directly:
            self.slot_above = slot_above
        if isinstance(self.parent, Deck):
            self.parent._slots[slot_above.name] = slot_above
        elif isinstance(self.parent, Labware):
            self.slot_below._add_slot_above(slot_above, directly=False)
        return slot_above
    
    def _delete_slot_above(self, slot_above: Slot|None = None, directly:bool = True) -> Slot|None:
        """
        Delete Slot above of stack
        
        Args:
            slot_above (Slot|None, optional): Slot above. Defaults to None.
            directly (bool, optional): whether to delete slot directly above itself. Defaults to True.
        
        Returns:
            Slot|None: Slot above
        """
        slot_above = self.slot_above if slot_above is None else slot_above
        if isinstance(self.parent, Deck) and isinstance(slot_above, Slot):
            self.parent._slots.pop(slot_above.name, None)
        elif isinstance(self.parent, Labware):
            self.slot_below._delete_slot_above(slot_above, directly=False)
        if directly:
            self.slot_above = None
        return slot_above

    def _draw(self, ax:plt.Axes, zoom_out:bool = False, **kwargs) -> list[matplotlib.patches.Patch]:
        """
        Draw Slot on matplotlib axis
        
        Args:
            ax (matplotlib.pyplot.Axes): plot axes
            zoom_out (bool, optional): whether to use zoomed out view. Defaults to False.
            
        Returns:
            list[matplotlib.patches.Patch]: list of matplotlib patches
        """
        patches = []
        patch = plt.Rectangle(self.bottom_left_corner.coordinates, *self.dimensions[:2], fill=False, linestyle="--", **kwargs)
        # ax.add_patch(patch)
        patches.append(patch)
        
        if isinstance(self.loaded_labware, Labware):
            _patches = self.loaded_labware._draw(ax, zoom_out=zoom_out,**kwargs)
            patches.extend(_patches)
        # ax.add_collection(PatchCollection(patches, match_original=True))
        if not isinstance(self.loaded_labware, Labware) and not zoom_out:
            ax.text(
                *self.center[:2], self.name, 
                ha='center', va='center', 
                rotation=self.bottom_left_corner.rotation[0], 
                fontsize=8, color='black', alpha=0.25
            )
        return patches


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
        `native` (Deck): native Deck object (i.e. without parent)
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
        `entry_waypoints` (list[Position]): entry waypoints for Deck
        `at` (SimpleNamespace): namespace of all Slots
        `on` (SimpleNamespace): namespace of all nested Decks
        
    ### Methods:
        `fromConfigs`: factory method to load Deck details from dictionary
        `fromFile`: factory method to load Deck from file
        `getAllPositions`: get all positions in Deck
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
    entry_waypoints: list[Position] = field(init=False, default_factory=list)
    
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
            deck_file = file_handler.resolve_repo_filepath(deck_file) if not deck_file.is_absolute() else deck_file
            if deck_file.is_file():
                parent_lineage = self.parent._nesting_lineage if isinstance(self.parent,Deck) else self._nesting_lineage
                if deck_file in parent_lineage:
                    parent_str = '\n+ '.join([p.as_uri() for p in parent_lineage if p is not None])
                    logger.error(f"Nested deck lineage:\n{parent_str}")
                    raise ValueError(f"Deck '{deck_file}' is already in the nested deck lineage")
                else:
                    self.loadNestedDeck(name=f"zone_{name}", details=details)
        self.entry_waypoints = [convert_to_position(wp) for wp in self._details.get('entry_waypoints',[])]
        return
    
    def __repr__(self) -> str:
        slots_ref = '\n'.join([f"\\__ {slot!r}" for slot in self.slots.values() if isinstance(slot, Slot)])
        zones_ref = '\n'.join([f"\\__ {zone!r}" for zone in self.zones.values()])
        return f"{self.name} ({self.__class__.__name__}:{id(self)})\n{slots_ref}\n\n{zones_ref}" 
    
    def __str__(self) -> str:
        slots_name = '\n'.join([f"+ {slot!s}" for slot in self.slots.values()])
        zones_name = '\n'.join([f"+ {zone!s}" for zone in self.zones.values()])
        return f"{self.name} comprising:\n{slots_name}\n{zones_name}"
    
    @classmethod
    def fromConfigs(cls, details:dict[str, Any], parent:Deck|None = None, _nesting_lineage:Sequence[Path|None]=(None,)) -> Deck:
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
    def fromFile(cls, deck_file:str, parent:Deck|None = None, from_repo:bool = True) -> Deck:
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
        filepath = Path(deck_file)
        filepath = filepath if filepath.is_absolute() else file_handler.resolve_repo_filepath(deck_file)
        assert filepath.is_file(), "Please input a valid Deck filepath"
        details = file_handler.read_config_file(filepath)
        details['deck_file'] = str(filepath)
        return cls.fromConfigs(details=details, parent=parent, _nesting_lineage=(filepath,))
    
    # Properties
    @property
    def native(self) -> Deck:
        """Native Deck object (i.e. without parent)"""
        filepath = self._details.get('deck_file',None)
        return Deck.fromFile(file_handler.resolve_repo_filepath(filepath)) if filepath else deepcopy(self)
    
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
    
    def getAllPositions(self) -> dict[str, tuple[float]|dict]:
        """
        Get all positions in Deck
        
        Returns:
            dict[str, tuple[float]]: dictionary of all positions
        """
        positions = dict()
        positions['self'] = tuple(self.center)
        for slot in self._slots.values():
            if isinstance(slot, Slot):
                positions[slot.name.replace(' ','_')] = slot.getAllPositions()
        for zone in self._zones.values():
            positions[zone.name.replace(' ','_')] = zone.getAllPositions()
        return positions
    
    def getSlot(self, value:int|str) -> Slot|None:
        """
        Get Labware in slot using slot id or name
        
        Args:
            value (int|str): slot id or name
            
        Returns:
            Slot: `Slot` object
        """
        if not isinstance(value, str):
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
        deck_file = Path(details.get('deck_file',''))
        deck_file = file_handler.resolve_repo_filepath(deck_file) if not deck_file.is_absolute() else deck_file
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
    
    def show(self, zoom_out:bool = False) -> tuple[plt.Figure, plt.Axes]:
        """
        Show Deck on matplotlib axis
        
        Args:
            zoom_out (bool, optional): whether to use zoomed out view. Defaults to False.
            
        Returns:
            tuple[matplotlib.pyplot.Figure, matplotlib.pyplot.Axes]: matplotlib figure, axes
        """
        fig, ax = plt.subplots()
        color_map = {v:k for k,v in mcolors.get_named_colors_mapping().items()}
        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        color_iterator = iter([color_map[c] for c in colors])
        color_iterator = itertools.chain(['none'], color_iterator, itertools.cycle(['black']))
        patches = self._draw(ax=ax, zoom_out=zoom_out, color_iterator=color_iterator)
        ax.add_collection(PatchCollection(patches, match_original=True))
        
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
        return fig,ax
    
    def _draw(self, ax: plt.Axes, zoom_out:bool = False, *, color_iterator:Iterator|None = None, **kwargs) -> list[matplotlib.patches.Patch]:
        """
        Draw Deck on matplotlib axis
        
        Args:
            ax (matplotlib.pyplot.Axes): plot axes
            zoom_out (bool, optional): whether to use zoomed out view. Defaults to False.
            color_iterator (Iterator|None, optional): iterator for colors. Defaults to None.
            
        Returns:
            list[matplotlib.patches.Patch]: list of matplotlib patches
        """
        patches = []
        bg_color = next(color_iterator) if isinstance(color_iterator,Iterator) else None
        patch_color = plt.Rectangle(self.bottom_left_corner.coordinates, *self.dimensions[:2], alpha=0.5, color=bg_color, **kwargs)
        patch_outline = plt.Rectangle(self.bottom_left_corner.coordinates, *self.dimensions[:2], fill=False, **kwargs)
        # ax.add_patch(patch_color)
        # ax.add_patch(patch_outline)
        patches.extend([patch_color, patch_outline])
        
        logger.info(f"{bg_color.replace('tab:','')} -> {self.name.replace('_sub','.')}")
        for zone in self._zones.values():
            if isinstance(zone, Deck):
                _patches = zone._draw(ax, zoom_out=zoom_out, color_iterator=color_iterator, **kwargs)
                patches.extend(_patches)
        
        for slot in self.slots.values():
            if isinstance(slot, Slot):
                _patches = slot._draw(ax, zoom_out=zoom_out, **kwargs)
                patches.extend(_patches)
        return patches


@dataclass(kw_only=True)
class BoundingVolume:
    """
    `BoundingVolume` represents a single BoundingVolume object

    ### Constructor:
        `parametric_function` (dict[str, Callable[[Sequence[float],Any], bool]): name, parametric function
        
    ### Attributes and properties:
        `parametric_function` (dict[str, Callable[[Sequence[float],Any], bool]): name, parametric function
        
    ### Methods:
        `contains`: check if point is within BoundingVolume
    """
    
    parametric_function: dict[str, Callable[[Sequence[float],Any], bool]]
    
    def __post_init__(self):
        assert isinstance(self.parametric_function, dict) and len(self.parametric_function) >= 1, "Please input at least one parametric function"
        func = list(self.parametric_function.values())[0]
        assert callable(func), "Please input a valid parametric function"
        # signature = inspect.signature(func)
        # ... # check if signature is valid
        return
    
    def __contains__(self, point:Sequence[float]) -> bool:
        return self.contains(point=point)
    
    def __add__(self, other:BoundingVolume|None) -> BoundingVolume:
        """
        Add two BoundingVolumes together
        
        Args:
            other (BoundingVolume|None): another `BoundingVolume` object
            
        Returns:
            BoundingVolume: new `BoundingVolume` object
        """
        if other is None:
            return self
        assert isinstance(other, BoundingVolume), "Please input a valid BoundingVolume object"
        new_function = {}
        new_function.update(self.parametric_function)
        new_function.update(other.parametric_function)
        return BoundingVolume(parametric_function=new_function)
    
    def contains(self, point:Sequence[float]|np.ndarray) -> bool:
        """
        Check if point is within BoundingVolume
        
        Args:
            point (Sequence[float]|numpy.ndarray): x,y,z coordinates
            
        Returns:
            bool: whether point is within BoundingVolume
        """
        assert len(point) == 3, "Please input x,y,z coordinates"
        return any(func(point) for func in self.parametric_function.values())  # check if point is within any of the parametric functions

    
@dataclass(kw_only=True)
class BoundingBox(BoundingVolume):
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
    
    parametric_function: dict[str, Callable[[Sequence[float],Any], bool]] = field(init=False, default_factory=dict)
    
    def __post_init__(self):
        assert isinstance(self.reference, Position), "Please input a valid reference position of type `Position`"
        assert isinstance(self.dimensions, (Sequence,np.ndarray)), "Please input Sequence or numpy.ndarray for x,y,z dimensions"
        assert isinstance(self.buffer, (Sequence,np.ndarray)), "Please input Sequence or numpy.ndarray lower and upper buffer"
        
        assert len(self.dimensions) == 3, "Please input x,y,z dimensions"
        assert len(self.buffer) == 2, "Please input lower and upper buffer"
        assert all([len(b) == 3 for b in self.buffer]), "Please input x,y,z buffer"
        self.dimensions = np.array(self.dimensions)
        self.buffer = np.array(self.buffer)
        
        self.parametric_function['box'] = lambda p: all([min(b) <= p[i] <= max(b) for i,b in enumerate(list(zip(*self.bounds)))])
        return
    
    def __add__(self, other:BoundingVolume|BoundingBox|None) -> BoundingVolume|BoundingBox:
        """
        Add two BoundingVolumes together
        
        Args:
            other (BoundingVolume|BoundingBox|None): another `BoundingVolume` or `BoundingBox` object
            
        Returns:
            BoundingVolume|BoundingBox: new `BoundingVolume` or `BoundingBox` object
        """
        if other is None:
            return self
        assert isinstance(other, BoundingVolume), "Please input a valid BoundingVolume object"
        if not isinstance(other, BoundingBox):
            return super().__add__(other)
        if not sum([int(np.isclose(sd,od)) for sd,od in zip(self.dimensions, other.dimensions)]) >= 2:
            return super().__add__(other)
        if not sum([int(np.isclose(self.reference.coordinates[i], other.reference.coordinates[i])) for i in range(3)]) >= 2:
            return super().__add__(other)
        if not np.allclose(self.reference.Rotation.as_quat(), other.reference.Rotation.as_quat()):
            return super().__add__(other)
        
        bottom_left_corner = np.min([self.reference.coordinates, other.reference.coordinates], axis=0)
        reference = Position(_coordinates=bottom_left_corner, Rotation=self.reference.Rotation)
        buffer = [[0,0,0], [0,0,0]]
        dimensions = [0,0,0]
        for i,(s_ref,o_ref) in enumerate(zip(self.reference.coordinates, other.reference.coordinates)):
            if np.isclose(s_ref, o_ref):
                dimensions[i] = max(self.dimensions[i], other.dimensions[i])
                buffer[0][i] = min(self.buffer[0][i], other.buffer[0][i])
                buffer[1][i] = max(self.buffer[1][i], other.buffer[1][i])
            else:
                dimensions[i] = self.dimensions[i] + other.dimensions[i]
                buffer[0][i] = self.buffer[0][i] if s_ref < o_ref else other.buffer[0][i]
                buffer[1][i] = other.buffer[1][i] if s_ref < o_ref else self.buffer[1][i]
        return BoundingBox(reference=reference, dimensions=dimensions, buffer=buffer)
    
    @property
    def bounds(self):
        """Lower and upper bounds"""
        dimensions = self.reference.Rotation.apply(self.dimensions)
        other_corner = self.reference.coordinates + dimensions
        bounds = np.array([self.reference.coordinates, other_corner])
        return bounds + self.reference.Rotation.apply(self.buffer)
    