# -*- coding: utf-8 -*-
# Set numpy print options to 1.21
import numpy as np
np.set_printoptions(legacy='1.21')
del np

# Add the external libraries path to sys.path
import sys
import os
external_libs = os.path.join(os.path.dirname(__file__), 'external')
sys.path.insert(0, external_libs)
del sys, os, external_libs

# Import logging filters
from ._log_filters import CustomLevelFilter, AppFilter

# Import functions
from .core.factory import get_setup
from .core.file_handler import init, start_project_here
from .core.logging import start_logging
