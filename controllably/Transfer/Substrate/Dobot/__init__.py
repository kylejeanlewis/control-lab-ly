"""
This sub-package imports the classes for substrate gripper tools from Dobot.

Classes:
    TwoJawGrip (DobotGripper)
    VacuumGrip (DobotGripper)
"""
from .dobot_attachments import TwoJawGrip, VacuumGrip

from controllably import include_this_module
include_this_module(get_local_only=False)

__where__ = 'Move.Jointed.Dobot.attachments'
include_this_module(get_local_only=False)