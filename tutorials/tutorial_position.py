
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

# %%
