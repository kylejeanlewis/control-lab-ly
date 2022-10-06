# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/06/18 09:00:00

@author: Chang Jie

Impedance package documentation can be found at:
https://impedancepy.readthedocs.io/en/latest/index.html
"""
import os, sys
import clr
import time
import Metrohm.AUTOLAB as EC

hdw=r'C:\Users\leongcj\Desktop\Metrohm Autolab\Autolab SDK 2.1\Hardware Setup Files\PGSTAT302N\HardwareSetup.FRA32M.xml',
sdk=r"C:\Users\leongcj\Desktop\Metrohm Autolab\Autolab SDK 2.1\EcoChemie.Autolab.Sdk"
adx=r"C:\Users\leongcj\Desktop\Metrohm Autolab\Autolab SDK 2.1\Hardware Setup Files\Adk.x"

AUTOLAB_INSTALLATION = r"C:\Users\leongcj\Desktop\Metrohm Autolab\Autolab SDK 2.1"
sys.path.append(AUTOLAB_INSTALLATION)
clr.AddReference('EcoChemie.Autolab.Sdk')

from EcoChemie.Autolab.Sdk import Instrument

# try:
#     clr.AddReference(sdk)
#     from EcoChemie.Autolab.Sdk import Instrument
# except SystemError:
#     pass

from eis_datatype import ImpedanceSpectrum

print(f"Import: OK <{__name__}>")

# %%
# initializing the class first
autolab = EC.AUTOLAB(sdk=sdk,adx=adx)
# autolab.sdk = sdk
# autolab.autolab = Instrument()

autolab.CMD = True # optional: Enable CMDLOG or not, it's good if you want to trace the code

# %%
try:
    if autolab.connectToAutolab(hdw): # first we need to connect to our instrument
        print("Connecting to AUTOLAB successfully....")
        # do measurement
        autolab.measure(R"*.nox file path") # it will take times till measrement finish
        autolab.saveAs(R"save file name")
except:
    print("Connecting to AUTOLAB FAIL....")


# %%
# it is a good habit to del the instance at the end of the script
del autolab
# %%
