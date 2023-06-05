"""
This sub-package imports the base class for control panels as well as basic panels
for measurers, movers, and viewers.

Classes:
    Panel (ABC)
    CompoundPanel (Panel)
    LiquidPanel (Panel)
    MeasurerPanel (Panel)
    MoverPanel (Panel)
    MultiChannelPanel (Panel)
    ViewerPanel (Panel)
"""
from .gui_utils import Panel, MultiChannelPanel
from .compound_panel import CompoundPanel
from .measurer_panel import MeasurerPanel
from .mover_panel import MoverPanel
from .transfer_liquid_panel import LiquidPanel
from .viewer_panel import ViewerPanel

from controllably import include_this_module
include_this_module(get_local_only=False)