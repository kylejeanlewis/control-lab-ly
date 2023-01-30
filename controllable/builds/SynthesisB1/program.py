# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import json

import sys
REPO = 'control-lab-le'
here = '/'.join(__file__.split('\\')[:-1])
root = here.split(REPO)[0]
sys.path.append(f'{root}{REPO}')

# Third party imports

# Local application imports
from . import create_named_tuple
from controllable.Compound.LiquidMover import LiquidMoverSetup
from controllable.Measure.Physical import MassBalance
from controllable.View.Optical import Optical
print(f"Import: OK <{__name__}>")

config_file = f"{here}/config.yaml"
layout_file = f"{here}/layout.json"

with open(layout_file) as file:
    layout_dict = json.load(file)
for slot in layout_dict['slots'].values():
    slot['filepath'] = f"{root}{slot['filepath']}"

@create_named_tuple
def create_setup():
    liquidmover = LiquidMoverSetup(config=config_file, config_option=0, layout_dict=layout_dict)
    balance = MassBalance('COM8')
    camera = Optical(1)
    setup = {
        'setup': liquidmover, 
        'mover': liquidmover.mover, 
        'liquid': liquidmover.liquid, 
        'balance': balance, 
        'camera': camera
    }
    return setup
