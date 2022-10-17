# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/06/18 09:00:00

@author: Chang Jie

Easy BioLogic package documentation can be found at:
https://github.com/bicarlsen/easy-biologic
"""
import os, sys
import time
import easy_biologic as ebl # pip install easy-biologic
import easy_biologic.base_programs as blp

from eis_datatype import ImpedanceSpectrum
print(f"Import: OK <{__name__}>")

# %%
# create device
bl = ebl.BiologicDevice( '192.168.1.2' )

# create mpp program
params = {
	'run_time': 10* 60		
}

mpp = blp.MPP(
    bl,
    params, 	
    channels = [ 0, 1, 2, 3, 4, 5, 6 ]        
)

# run program
mpp.run( 'data' )

# %%
