"""
This sub-package imports the class for liquid mover setups.

Classes:
    LiquidMoverSetup (CompoundSetup)
"""
from .liquidmover_utils import LiquidMoverSetup, LiquidMover

from controllably import include_this_module
include_this_module(get_local_only=False)