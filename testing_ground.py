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
from controllable.Analyse.Data.Types.eis_datatype import ImpedanceSpectrum
print(f"Import: OK <{__name__}>")


if __name__ == "__main__":
    df = pd.read_csv('src/utils/characterisation/electrical/examples/biologic_test3.csv', header=1)    
    name_map = {
            "Impendance phase": "Impedance phase [rad]",
            "Impendance_ce phase": "Impedance_ce phase [rad]"
        }
    df.rename(columns=name_map, inplace=True)
    
    spectrum = ImpedanceSpectrum(df, instrument='biologic_')
    spectrum.plotNyquist()
    spectrum.fit()
    spectrum.getCircuitDiagram()
    spectrum.plotNyquist()
    pass
# %%
