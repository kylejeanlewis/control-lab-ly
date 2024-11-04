"""
This sub-package imports the class for spin-coaters.

Classes:
    Spinner (Maker)
    SpinnerAssembly (Maker)
"""
from .spinner_utils import Spinner, Multi_Spinner

from controllably import include_this_module
include_this_module(get_local_only=False)