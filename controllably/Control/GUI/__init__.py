"""
This sub-package imports the base class for control panels as well as basic panels
for measurers, movers, and viewers.

Classes:
    Panel (ABC)
    CompoundPanel (Panel)
    Guide(Panel)
    MultiChannelPanel (Panel)

Functions:
    guide_me
"""
from .gui_utils import Panel
from .compound_panel import CompoundPanel
from .guide_panel import Guide
from .multichannel_panel import MultiChannelPanel

from controllably import include_this_module
include_this_module(get_local_only=False)

from .guide_panel import guide_me