# -*- coding: utf-8 -*-
# Import logging filters
from .core.log_filters import CustomLevelFilter, AppFilter

# Import functions
from .core.factory import get_setup
from .core.file_handler import init, start_project_here
from .core.logging import start_logging

# Initialize
import os
import sys
import numpy as np

# Add the external libraries path to sys.path
external_libs = os.path.join(os.path.dirname(__file__), 'external')
sys.path.insert(0, external_libs)
del sys, os, external_libs

# Set numpy print options to 1.21
np.set_printoptions(legacy='1.21')
del np
