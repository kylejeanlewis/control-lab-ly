# -*- coding: utf-8 -*-
from .core.factory import get_setup
from .core.file_handler import init, start_logging, start_project_here

# Initialization code
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
