"""
This sub-package imports the base class for control panels as well as basic panels
for measurers, movers, and viewers.

Modules:
    Popups
    Templates

Classes:
    LoaderPanel (Panel)
"""
from .loader_panel import LoaderPanel
from . import pop_ups as Popups
from . import templates as Templates

from controllably import include_this_module
include_this_module(get_local_only=False)