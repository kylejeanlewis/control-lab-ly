"""
This sub-package imports the class for thermal cameras from FLIR.

Classes:
    AX8 (Camera)
"""
from .ax8_utils import AX8

from controllably import include_this_module
include_this_module(get_local_only=False)