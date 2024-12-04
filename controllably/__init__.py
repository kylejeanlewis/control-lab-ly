"""
.. include:: ../docs/README.md
.. include:: ../docs/CHANGELOG.md
"""
from .core import init, start_logging
from .misc import *
from .Control.GUI import guide_me

import numpy as np
np.set_printoptions(legacy='1.21')