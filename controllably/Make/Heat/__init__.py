"""
This sub-package imports the class for Peltier devices.

Classes:
    Peltier (Maker)
"""
from .peltier_utils import Peltier

from controllably import include_this_module
include_this_module(get_local_only=False)