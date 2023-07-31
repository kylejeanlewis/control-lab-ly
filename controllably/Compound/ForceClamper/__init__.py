"""
This sub-package imports the class for clamp and gauge setups.

Classes:
    ForceClampSetup (CompoundSetup)
"""
from .forceclamper_utils import ForceClampSetup

from controllably import include_this_module
include_this_module(get_local_only=False)