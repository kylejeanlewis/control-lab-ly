# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import pandas as pd
# Third party imports

# Local application imports
# from controllable.Move import Cartesian, Jointed
# from controllable.builds import mySetup
# from controllable.Measure.Electrical.Biologic import biologic_utils
# from controllable.Analyse.Data.Types.eis_datatype import ImpedanceSpectrum
# from controllable.Measure.Electrical import Biologic, Keithley
from controllable.builds.Paraspin import Setup, Program
print(f"Import: OK <{__name__}>")

REAGENTS_FILE = r'C:\Users\leongcj\Desktop\Astar_git\control-lab-le\controllable\builds\Paraspin\reagents.csv'
RECIPE_FILE = r'C:\Users\leongcj\Desktop\Astar_git\control-lab-le\controllable\builds\Paraspin\recipe.csv'
STATE_FILE = 'Paraspin/program/state.yaml'

if __name__ == "__main__":
    # spinbot = Setup('', ignore_connections=True)
    spin_program = Program(ignore_connections=False, recover_state_from_file=STATE_FILE)
    spin_program.loadRecipe(REAGENTS_FILE, RECIPE_FILE)
    spin_program.setup.labelPosition('fill', (-120,0,0))
    # spin_program.saveState()
    # spin_program.prepareSetup()
    # spin_program.saveState()
    pass
# %%
