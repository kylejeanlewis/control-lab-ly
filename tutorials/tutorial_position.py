
# %% [markdown]
# # Locating with `core.position`
# This tutorial demonstrates how to use the various classes from the 
# `controllably.core.position` module to manage coordinate systems in your 
# automated workflows.
# 
# We start with the fundamental `Position` class, which provides a convenient 
# way to handle positions (3D coordinates and orientations) in a Cartesian 
# coordinate system.
# 
# Here are some ways of creating a `Position` object:

# %%
from controllably.core.position import Position
from scipy.spatial.transform import Rotation

rotation = Rotation.from_euler('zyx', [20, 0, 0], degrees=True)
p0 = Position()
p1 = Position((1, 2, 3))
p2 = Position(Rotation=Rotation.from_euler('zyx', [30, 45, 60], degrees=True))
p3 = Position((4, 5, 6), rotation)

# %% [markdown]
# The `Position` class can be used to represent points in space,
# orientations, or both. The `Position` class also provides methods to
# convert between different representations, using the `rotation_type` and 
# `degrees` parameters to specify the preferred rotation representation 
# and whether the angles are in degrees or radians.
# 
# `Position` objects can be created from various inputs, such as tuples,
# lists, or NumPy arrays. They can also be serialized to strings and read back.

# %%
p4 = Position.fromArray([[7, 8, 9], [10, 11, 12]])
p4_string = p4.toJSON()
print(f'{p4_string=}')
p4 == Position.fromJSON(p4_string)

# %% [markdown]
# Attributes of the `Position` class include:
# - `coordinates`: `numpy.ndarray` representing the position in 3D space.
# - `rotation`: `numpy.ndarray` representing the rotation in Euler angles.
# - `rot_matrix`: `numpy.ndarray` representing the rotation matrix.
# - `Rotation`: `Rotation` object representing the orientation. (note the capital 'R')
# - `x`, `y`, `z`: Individual coordinates of the position.
# - `a`, `b`, `c`: Individual Euler angles along xy-plane (Rz), xz-plane (Ry), yz-plane (Rx).

# %%
print(f'{p4.coordinates=}')
print(f'{p4.rotation=}')
print(f'{p4.x=},{p4.y=},{p4.z=}')
print(f'{p4.a=},{p4.b=},{p4.c=}')
print(f'{p4.rot_matrix=}')

# %% [markdown]
# Methods of the `Position` class include:
# - `translate`: Translate the position by a given vector.
# - `orientate`: Orientate the position by a given rotation.
# - `apply`: Apply a transformation to the position. \
#   (i.e. `A.apply(B) == B.translate(A.coordinates).orientate(A.Rotation)`)
# - `invert`: Invert the position. (i.e. negate the coordinates and rotation)

# %%
print(f'{p3=}')
print(f'{p4=}')
print(f'{p4.translate((4, 5, 6), inplace=False)=}')
print(f'{p4.orientate(rotation, inplace=False)=}')
print(f'{p4.apply(p3, inplace=False)=}')
print(f'{p3.apply(p4, inplace=False)=}')
print(f'{p4.invert()=}')
print(f'{p3.invert()=}')

# %% [markdown]
# Next, we introduce the `Well` and `Labware` classes, which are used to represent
# positions in a laboratory setting. The `Labware` class represents a piece of 
# lab equipment with defined positions such as a microtiter plate or a tube rack, while
# the `Well` class represents a well in a Labware (e.g. microtiter plate).
# 
# The `Labware` class can be created from a JSON file from the Opentrons Labware Library
# that defines the labware's geometry, such as the number of wells, their dimensions, and 
# their arrangement. 
# 
# `Labware` objects can be created using the `fromFile` method with the path to a JSON file, 
# or using the `fromConfigs` method with a configuration dictionary, and can be displayed
# using the `show()` method.

# %%
from controllably.core.position import Well, Labware
from controllably.core.file_handler import read_config_file, resolve_repo_filepath

wellplate = Labware.fromFile('control-lab-ly/tutorials/library/labware/corning_12_wellplate_6900ul edited.json')
tiprack_config = read_config_file(resolve_repo_filepath('control-lab-ly/tutorials/library/labware/opentrons_96_filter_tiprack_1000ul.json'))
tiprack = Labware.fromConfigs(tiprack_config)
wellplate.show()

# %% [markdown]
# Attributes of the `Labware` class include:
# - `bottom_left_corner`: position of the bottom left corner of the labware, which is it reference point \
#   (i.e. coordinates and orientation).
# - `center`: coordinates of the center of the labware.
# - `offset`: offset of the labware from the reference point. \
#   (i.e. the vector from the reference to the center; midpoint of the labware).
# - `dimensions`: dimensions of the labware in the x, y, and z directions.
# - `top`: coordinates of the top surface of the labware. \
#   (offset from top of Labware can be calculated using `Labware.fromTop()` method)

# %%
print(f'{wellplate.reference==wellplate.bottom_left_corner=}')
print(f'{wellplate.reference=}')
print(f'{wellplate.center=}')
print(f'{wellplate.offset=}')
print(f'{wellplate.dimensions=}')
print(f'{wellplate.top=}')
print(f'{wellplate.fromTop((1,2,3))=}')

# %% [markdown]
# The name of the `Well` objects can be accessed from the `Labware` object using several ways:
# - `columns`: a dictionary of column names (e.g. 'A', 'B', 'C') to lists of well names in that column.
# - `rows`: a dictionary of row names (e.g. 1, 2, 3) to lists of well names in that row.
# - `listColumns()`: a list of well names grouped by columns.
# - `listRows()`: a list of well names grouped by rows.

# %%
print(f'{wellplate.columns=}')
print(f'{wellplate.listColumns()=}\n')
print(f'{wellplate.rows=}')
print(f'{wellplate.listRows()=}\n')

# %% [markdown]
# The `Well` objects can be accessed from the `Labware` object using several ways:
# - `wells`: a dictionary of `Well` objects, indexed by their well names (e.g. 'A1', 'B2').
# - `wells_columns`: a dictionary of `Well` objects, indexed by their column names (e.g. 'A', 'B').
# - `wells_rows`: a dictionary of `Well` objects, indexed by their row names (e.g. 1, 2).
# - `listWells()`: a list of `Well` objects, optionally grouped by columns or rows.

# %%
print(f'{wellplate.wells=}')
print(f'{wellplate.listWells()=}\n')
print(f'{wellplate.wells_columns=}')
print(f'{wellplate.listWells(by='col')=}\n')
print(f'{wellplate.wells_rows=}')
print(f'{wellplate.listWells(by='row')=}\n')

# %% [markdown]
# Specific `Well` objects can be accessed using their names, such as 'A1', 'B2', etc.
# The `getWell()` method returns the `Well` object for a given well name,
# while the `at` property provides a convenient way to access wells using dot notation.

# %%
print(f'{wellplate.wells['A1']=}')
print(f'{wellplate.getWell('A1')=}')
print(f'{wellplate.at.A1=}')
well_a1 = wellplate.getWell('A1')  
print(f'{type(well_a1)==Well=}')

# %% [markdown]
# The `Well` class has several attributes and methods:
# - `reference`: the reference position of the well, which is its bottom left corner of its parent Labware.
# - `center`: coordinates of the center of the well bottom. (i.e. `Well.bottom`)
# - `bottom`: coordinates of the bottom surface of the well. \
#   (offset from bottom of well can be calculated using `Well.fromTop()` method)
# - `middle`: coordinates of the middle of the well. \
#   (offset from middle of well can be calculated using `Well.fromTop()` method)
# - `top`: coordinates of the top surface of the well. \
#   (offset from top of well can be calculated using `Well.fromTop()` method)
# - `offset`: offset of the well bottom from the reference point. \
#   (i.e. the vector from the reference to the center of the well bottom).
# - `dimensions`: dimensions of well cross-section ((diameter,) if circular, (x,y) if rectangular).
# - `base_area`: area of the well bottom cross-section.
# - `level`: the height of the liquid in well from the bottom \
#   (i.e. `Well.volume / Well.base_area`).

# %%
print(f'{well_a1.reference=}')
print(f'{well_a1.center=}')
print(f'{well_a1.bottom=}')
print(f'{well_a1.middle=}')
print(f'{well_a1.top=}')
print(f'{well_a1.offset=}')
print(f'{well_a1.dimensions=}')
print(f'{well_a1.base_area=}')
print(f'{well_a1.level=}')

# %% [markdown]
# Further, we introduce the `Slot` and `Deck` classes, which are used to represent
# positions in a workspace. The `Deck` class represents the workspace, the `Slot` class 
# represents a slot in a `Deck`.
# 
# The `Deck` class can be created from a JSON file, which is structurally similar to the 
# Labware JSON file, that defines the decks's geometry, such as the number of slots, their dimensions, and 
# their arrangement. 
# 
# `Deck` objects can be created using the `fromFile` method with the path to a JSON file, 
# or using the `fromConfigs` method with a configuration dictionary, and can be displayed
# using the `show()` method.

# %%
from controllably.core.position import Slot, Deck
from controllably.core.file_handler import read_config_file, resolve_repo_filepath

deck = Deck.fromFile('control-lab-ly/tutorials/library/layouts/opentrons_deck_v2.json')
board_config = read_config_file(resolve_repo_filepath('control-lab-ly/tutorials/library/layouts/optical_breadboard.json'))
board = Deck.fromConfigs(board_config)
deck.show()

# %% [markdown]
# Attributes of the `Deck` class include:
# - `bottom_left_corner`: position of the bottom left corner of the deck, which is it reference point \
#   (i.e. coordinates and orientation).
# - `center`: coordinates of the center of the deck.
# - `offset`: offset of the deck from the reference point. \
#   (i.e. the vector from the reference to the center; midpoint of the deck).
# - `dimensions`: dimensions of the deck in the x, y, and z directions.

# %%
print(f'{deck.reference==deck.bottom_left_corner=}')
print(f'{deck.reference=}')
print(f'{deck.center=}')
print(f'{deck.offset=}')
print(f'{deck.dimensions=}')

# %% [markdown]
# `Deck`s can also be nested, meaning that a `Deck` can contain other `Deck`s.
# These nested `Deck`s are referred to as zones, and they can be accessed using 
# the `zones` attribute, or the `on` property.

# %%
layout = Deck.fromFile('control-lab-ly/tutorials/library/layouts/layout.json')
layout.show()
print(f'\n{layout.zones=}\n')
zone_A = layout.zones['zone_A']
print(f'{type(zone_A)==Deck=}')
print(f'{layout.on.zone_A==zone_A=}')

# %% [markdown]
# Specific `Slot` objects can be accessed using their names, 
# such as 'slot_01', 'slot_02', etc.
# The `getSlot()` method returns the `Slot` object for a given slot name,
# while the `at` property provides a convenient way to access slots using dot notation.

# %%
print(f'{zone_A.slots['slot_01']=}')
print(f'{zone_A.getSlot('slot_01')=}')
print(f'{zone_A.at.slot_01=}')
slot_01 = zone_A.getSlot('slot_01') 
print(f'{type(slot_01)==Slot=}')

# %% [markdown]
# The `at` property of the `Deck` class can be used to access the slots in the nested
# `Deck` objects in a more intuitive way, using the deck and slot names as attributes.

# %%
print(f'{layout.at.zone_A.slot_01==zone_A.at.slot_01=}')
layout.at

# %% [markdown]
# Methods of the `Deck` class include:
# - `loadLabware`: Load an existing `Labware` object into a specific slot in the deck.
# - `removeLabware`: Remove a `Labware` object from a specific slot in the deck.
# - `transferLabware`: Transfer a `Labware` object from one slot to another in the deck.

# %%
source_slot = layout.at.zone_A.slot_01
middle_slot = layout.at.slot_01
target_slot = layout.at.zone_B.slot_02

# %%
layout.loadLabware(source_slot, wellplate)
print(f'{wellplate.parent=}')
print(f'{wellplate.parent==source_slot=}')
layout.show()

# %%
layout.transferLabware(source_slot, middle_slot)
print(f'{wellplate.parent=}')
print(f'{wellplate.parent==middle_slot=}')
layout.show()

# %%
layout.transferLabware(middle_slot, target_slot)
print(f'{wellplate.parent=}')
print(f'{wellplate.parent==target_slot=}')
layout.show()

# %%
removed_labware = layout.removeLabware(target_slot)
print(f'{wellplate.parent=}')
print(f'{removed_labware==wellplate=}')
layout.show()

# %%
# Attributes of the `Slot` class include:
# - `reference`: the reference position of the slot, which is its bottom left corner of its parent deck.
# - `center`: coordinates of the center of the slot.
# - `offset`: offset of the center from the reference point. \
#   (i.e. the vector from the reference to the center of the well bottom).
# - `dimensions`: dimensions of slot.
# - `loaded_labware`: the `Labware` object loaded in the slot, if any.

# %%
print(f'{slot_01=}')
print(f'{slot_01.reference=}')
print(f'{slot_01.center=}')
print(f'{slot_01.offset=}')
print(f'{slot_01.dimensions=}')
print(f'{slot_01.loaded_labware=}')

# %% [markdown]
# Methods of the `Deck` class include:
# - `loadLabware`: Load an existing `Labware` object into a specific slot in the deck.
# - `removeLabware`: Remove a `Labware` object from a specific slot in the deck.
# - `loadLabwareFromConfigs`: Load a **new** `Labware` object from a configuration dictionary into a specific slot in the deck.
# - `loadLabwareFromFile`: Load a **new** `Labware` object from a JSON file into a specific slot in the deck.

# %%
slot_01.loadLabware(tiprack)
print(f'{tiprack.parent=}')
print(f'{tiprack.parent==slot_01=}')
layout.show()

slot_01.removeLabware()
print(f'{tiprack.parent=}')
print(f'{tiprack.parent==slot_01=}')
layout.show()

# %%
slot_01.loadLabwareFromConfigs(tiprack_config)
tiprack_1 = slot_01.loaded_labware
print(f'{tiprack_1=}')
print(f'{tiprack_1==tiprack=}')
print(f'{tiprack_1.parent==slot_01=}')
layout.show()

slot_01.removeLabware()
print(f'{tiprack.parent=}')
print(f'{tiprack.parent==slot_01=}')
layout.show()

# %%
slot_01.loadLabwareFromFile('control-lab-ly/tutorials/library/labware/opentrons_96_filter_tiprack_1000ul.json')
tiprack_2 = slot_01.loaded_labware
print(f'{tiprack_2=}')
print(f'{tiprack_2==tiprack=}')
print(f'{tiprack_2==tiprack_1=}')
print(f'{tiprack_2.parent==slot_01=}')
layout.show()

slot_01.removeLabware()
print(f'{tiprack.parent=}')
print(f'{tiprack.parent==slot_01=}')
layout.show()

# %%
# `Labware` objects can also be stackable, meaning that multiple `Labware` 
# objects can be loaded on top of each other.
# The `Labware` class has a `stackable` attribute that indicates whether the
# labware is stackable, and a `slot_above` attribute that represents the 
# slot above the current labware, if it is stackable.
# 
# The `Slot` object has a `stack` attribute that represents the stack of
# `Labware` objects loaded in the slot, if any.
# The stacked Labware needs to be removed in reverse order, starting from the top.

# %%
wellplate_1 = Labware.fromFile('control-lab-ly/tutorials/library/labware/corning_12_wellplate_6900ul edited.json')
wellplate_2 = Labware.fromFile('control-lab-ly/tutorials/library/labware/corning_12_wellplate_6900ul edited.json')
wellplate_3 = Labware.fromFile('control-lab-ly/tutorials/library/labware/corning_12_wellplate_6900ul edited.json')

# %%
slot_01.loadLabware(wellplate)
wellplate.slot_above.loadLabware(wellplate_1)
wellplate_1.slot_above.loadLabware(wellplate_2)
wellplate_2.slot_above.loadLabware(wellplate_3)
layout.show()
slot_01.stack

# %%
removed_wellplate = slot_01.slot_above.slot_above.slot_above.removeLabware()
removed_wellplate_1 = slot_01.slot_above.slot_above.removeLabware()
removed_wellplate_2 = slot_01.slot_above.removeLabware()
removed_wellplate_3 = slot_01.removeLabware()
layout.show()
slot_01.stack

# %%
print(f'{removed_wellplate==wellplate_3=}')
print(f'{removed_wellplate_1==wellplate_2=}')
print(f'{removed_wellplate_2==wellplate_1=}')
print(f'{removed_wellplate_3==wellplate=}')

# %% [markdown]
# Lastly, the `BoundingVolume` and `BoundingBox` classes are used to represent
# bounding volumes and boxes in 3D space. These classes are useful for defining
# the spatial limits of objects in a coordinate system, such as the dimensions of a
# labware or the workspace. It can also be used to define the exclusion zone for 
# a robot arm to avoid collisions with other objects in the workspace.
# 
# The `BoundingVolume` class can be created using a parametric function that defines
# the conditions for being inside or outside the volume. The `parametric_function`
# parameter is a dictionary that can contain keys like 'positive' or 'negative',
# each mapping to a function that takes a point in space and returns a boolean.

# %%
from controllably.core.position import BoundingVolume, BoundingBox

def less_than_zero(point):
    return any(a < 0 for a in point)
vol = BoundingVolume(parametric_function={"negative": less_than_zero})

# %% [markdown]
# The volume has the `contains` method that checks if a point is inside the volume.
# The `contains` method takes a point as input and returns a boolean indicating whether
# the point is inside the volume. It can also be used with the `in` operator to check
# if a point is inside the volume.

# %%
inside_point = (-1, -2, -3)
outside_point = (0.001, 0.02, 0.3)

print(f'{vol.contains(inside_point)=}')
print(f'{vol.contains(outside_point)=}')
print(f'{outside_point in vol=}')

# %% [markdown]
# The `BoundingBox` class is a subclass of `BoundingVolume` that represents a
# rectangular bounding box in 3D space. It is defined by its reference position 
# (i.e. bottom left corner), dimensions (length, width, height), and an optional buffer
# (padding) around the box. The buffer can be specified as a tuple of three values
# to define the padding in each direction.

# %%
box_1 = BoundingBox(
    reference=Position((0, 0, 0)),
    dimensions=(10, 20, 30),
)
box_1b = BoundingBox(
    reference=Position((0, 0, 0)),
    dimensions=(10, 20, 30),
    buffer=((-1, -2, -3), (1, 2, 3))
)
print(f'{(0,0,0) in box_1=}')       # True, on the edge of the box
print(f'{(-1,-2,-3) in box_1=}')    # False, outside the box
print(f'{(-1,-2,-3) in box_1b=}')   # True, inside the box with buffer
print(f'{(-1,-2,-4) in box_1b=}')   # False, outside the box with buffer
print(f'{(10,20,30) in box_1=}')    # True, on the edge of the box
print(f'{(11,22,33) in box_1=}')    # False, outside the box
print(f'{(11,22,33) in box_1b=}')   # True, inside the box with buffer
print(f'{(12,22,33) in box_1b=}')   # False, outside the box with buffer

# %% [markdown]
# These `BoundingBox` objects can be added together using the `+` operator,
# which combines their dimensions and buffers to create a new bounding box that
# encompasses both boxes. The resulting box will have a reference position at the
# bottom left corner of the overall volume, and its dimensions will be the maximum
# dimensions of the two boxes, taking into account the buffers.

# %%
boxes_11b = box_1 + box_1b
print(f'{type(boxes_11b)==BoundingBox=}')
print(f'{(0,0,0) in boxes_11b=}')       # True, on the edge of the box
print(f'{(-1,-2,-3) in boxes_11b=}')    # True, inside the box with buffer
print(f'{(-1,-2,-4) in boxes_11b=}')    # False, outside the box with buffer
print(f'{(10,20,30) in boxes_11b=}')    # True, on the edge of the box
print(f'{(11,22,33) in boxes_11b=}')    # True, inside the box with buffer
print(f'{(12,22,33) in boxes_11b=}')    # False, outside the box with buffer

# %% [markdown]
# When the `BoundingBox` objects are added together, the resulting volume will be 
# a `BoundingBox` if the boxes are aligned along one of the axes. If the boxes are not 
# aligned, the resulting volume will be a `BoundingVolume` that encompasses both boxes.

# %%
box_2x = BoundingBox(
    reference=Position((10, 0, 0)),
    dimensions=(10, 20, 30)
)
boxes_12x = box_1 + box_2x
print(f'{type(boxes_12x)==BoundingBox=}')
print(f'{(0,0,0) in boxes_12x=}')       # True, on the edge of the box
print(f'{(-1,-2,-3) in boxes_12x=}')    # False, outside the combined box
print(f'{(10,20,30) in boxes_12x=}')    # True, inside combined box
print(f'{(20,20,30) in boxes_12x=}')    # True, inside the combined box
print(f'{(21,20,30) in boxes_12x=}')    # False, outside the combined box

# %%
box_2y_y = BoundingBox(
    reference=Position((0, 20, 0)),
    dimensions=(10, 40, 30)
)
boxes_12y_y = box_1 + box_2y_y
print(f'{type(boxes_12y_y)==BoundingBox=}')
print(f'{(0,0,0) in boxes_12y_y=}')       # True, on the edge of the box
print(f'{(-1,-2,-3) in boxes_12y_y=}')    # False, outside the combined box
print(f'{(10,20,30) in boxes_12y_y=}')    # True, inside combined box
print(f'{(10,60,30) in boxes_12y_y=}')    # True, inside the combined box
print(f'{(10,61,30) in boxes_12y_y=}')    # False, outside the combined box

# %%
box_2xy = BoundingBox(
    reference=Position((10, 20, 0)),
    dimensions=(10, 20, 30)
)
boxes_12xy = box_1 + box_2xy
print(f'{type(boxes_12xy)==BoundingBox=}')
print(f'{type(boxes_12xy)==BoundingVolume=}')

# %%
box_2y_x = BoundingBox(
    reference=Position((0, 20, 0)),
    dimensions=(20, 20, 30)
)
boxes_12y_x = box_1 + box_2y_x
print(f'{type(boxes_12y_x)==BoundingBox=}')
print(f'{type(boxes_12y_x)==BoundingVolume=}')

# %%
box_2yz_z = BoundingBox(
    reference=Position((0, 20, 30)),
    dimensions=(10, 20, 40)
)
boxes_12yz_z = box_1 + box_2yz_z
print(f'{type(boxes_12yz_z)==BoundingBox=}')
print(f'{type(boxes_12yz_z)==BoundingVolume=}')

# %%
box_plus_vol = box_1 + vol
print(f'{type(box_plus_vol)==BoundingBox=}')
print(f'{type(box_plus_vol)==BoundingVolume=}')
print(f'{(0,0,0) in box_plus_vol=}')       # True, inside the combined volume
print(f'{(-1,-2,-3) in box_plus_vol=}')    # True, inside the combined volume
print(f'{(10,20,30) in box_plus_vol=}')    # True, on the edge of the combined volume
print(f'{(11,20,30) in box_plus_vol=}')    # False, outside the combined volume

# %%
