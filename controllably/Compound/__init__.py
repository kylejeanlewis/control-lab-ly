"""
This sub-package imports the base class for compound setups.

Classes:
    CompoundSetup (ABC)
"""
from .compound_utils import CompoundSetup

from controllably import include_this_module
include_this_module(get_local_only=False)