"""
This sub-package imports the class for orbital shakers from QInstruments.

Classes:
    BioShake (Maker)
"""
from .orbital_shaker_utils import BioShake

from controllably import include_this_module
include_this_module(get_local_only=False)