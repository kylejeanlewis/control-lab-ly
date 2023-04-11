"""
This sub-package imports the classes for substrate gripper tools from Dobot.

Classes:
    DobotGripper (Gripper)
    TwoJawGrip (DobotGripper)
    VacuumGrip (DobotGripper)
"""
from .dobot_attachments import DobotGripper, TwoJawGrip, VacuumGrip

from controllably import include_this_module
include_this_module(get_local_only=False)