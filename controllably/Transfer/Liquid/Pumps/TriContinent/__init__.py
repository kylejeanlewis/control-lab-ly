"""
This sub-package imports the class for syringe pumps from TriContinent.

Classes:
    TriContinent (Pump)
"""
from .tricontinent_utils import TriContinent

from controllably import include_this_module
include_this_module(get_local_only=False)