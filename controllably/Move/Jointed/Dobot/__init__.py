"""
This sub-package imports the classes for movement tools from Dobot.

Classes:
    Dobot (RobotArm)
    M1Pro (Dobot)
    MG400 (Dobot)
"""
from .dobot_utils import Dobot
from .m1pro_utils import M1Pro
from .mg400_utils import MG400

from controllably import include_this_module
include_this_module(get_local_only=False)