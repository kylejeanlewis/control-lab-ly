# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports

# Third party imports

# Local application imports
from ...Compound.LiquidMover import LiquidMoverSetup
from ...Measure.Physical import MassBalance
from ...View.Optical import Optical
print(f"Import: OK <{__name__}>")

here = '\\'.join(__file__.split('\\')[:-1])
config_file = f"{here}\\config.yaml"
layout_file = f"{here}\\layout.json"

def run():
    spinbot = LiquidMoverSetup(config=config_file, config_option=0, layout=layout_file)
    balance = MassBalance('COM8')
    camera = Optical(1)

    setup =spinbot
    mover = setup.mover
    liquid = setup.liquid

    # setup.align(setup.deck.get_slot(name='jars').get_well('A1').middle)
    # balance.toggleRecord(True)
    # camera.toggleRecord(True, folder='C:/Users/leongcj/Desktop/machine vision', timeout=60)
    # liquid.aspirate(volume=200, speed=None)
    # time.sleep(60)
    # balance.toggleRecord(False)
    # camera.toggleRecord(False)
# %%
