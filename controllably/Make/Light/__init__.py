"""
This sub-package imports the class for LED arrays.

Classes:
    LEDArray (Maker)
"""
from .led_utils import LEDArray

from controllably import include_this_module
include_this_module(get_local_only=False)