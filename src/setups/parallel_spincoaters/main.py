# %%
# -*- coding: utf-8 -*-
"""
Created on 

@author: Chang Jie 
"""
from routines import Controller
print(f"Import: OK <{__name__}>")


control = Controller('config/config.xlsx', position_check=False)
control.run_program()

# %%
