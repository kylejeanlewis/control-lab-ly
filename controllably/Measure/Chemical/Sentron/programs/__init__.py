"""
This sub-package imports the program class for tools from Sentron.

Classes:
    phMonitor (Program)
"""
from .base_programs import pHMonitor

from controllably import include_this_module
include_this_module(get_local_only=False)