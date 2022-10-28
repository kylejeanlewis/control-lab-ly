# %%
# -*- coding: utf-8 -*-
"""
### DEVELOPMENT PAUSED ###
Created on Fri 2022/06/18 09:00:00

@author: Chang Jie

Metrohm Autolab package documentation can be found at:
https://github.com/shuayliu/pyMetrohmAUTOLAB
"""
import os, sys
import clr # pip install pythonnet
import time
import Metrohm.AUTOLAB as EC # pip install pyMetrohmAUTOLAB
import inspect
# from eis_datatype import ImpedanceSpectrum

# Depend on computer setup and installation
AUTOLAB_INSTALLATION = r"C:\Users\leongcj\Desktop\Metrohm Autolab\Autolab SDK 2.1"
sys.path.append(AUTOLAB_INSTALLATION)
clr.AddReference('EcoChemie.Autolab.Sdk')

def retry(func):
    def do_this():
        n_tries = 0
        while n_tries < 3:
            try:
                n_tries += 1
                print(f'Trying {n_tries}')
                func()
                print('Success')
                break
            except Exception as e:
                print(e)
    return do_this

@retry
def import_sdk():
    global Instrument
    from EcoChemie.Autolab.Sdk import Instrument as Instrument
    return 

import_sdk()
# n_import = 0
# while n_import < 3:
#     success_import = False
#     try:
#         n_import += 1
#         import EcoChemie.Autolab.Sdk as Autolab
#         success_import = True
#     except SystemError:
#         print(f"Attempted ({n_import}) importing EcoChemie.Autolab.Sdk")
#     else:
#         success_import = 'Success' if success_import else 'Fail'
#         print(f"{success_import} importing EcoChemie.Autolab.Sdk")
#         break
print(f"Import: OK <{__name__}>")

SDK = AUTOLAB_INSTALLATION + "\\EcoChemie.Autolab.Sdk"
ADX = AUTOLAB_INSTALLATION + "\\Hardware Setup Files\Adk.x"
HDW = AUTOLAB_INSTALLATION + "\\Hardware Setup Files\\PGSTAT302N\\HardwareSetup.FRA32M.xml"
NOX = AUTOLAB_INSTALLATION + "\\Standard Nova Procedures\\FRA impedance potentiostatic.nox"

instrument = Instrument()

@retry
def connect():
    global instrument
    # inspect.getmembers(instrument)
    # print(instrument.__dir__)
    instrument.set_HardwareSetupFile(HDW)
    instrument.get_AutolabConnection()
    vars(instrument.get_AutolabConnection)
    # print(instrument.AutolabConnection.__dir__)
    instrument.AutolabConnection.set_EmbeddedExeFileToStart(ADX)
    # instrument.AutolabConnection.EmbeddedExeFileToStart = ADX
    instrument.Connect()
    return

# %%
connect()
# %%
instrument.__dir__()
instrument.get_AutolabConnection.__dir__()
instrument.AutolabConnection.__dir__()
# %%
myProcedure = instrument.LoadProcedure(NOX)
myCommand = myProcedure.Commands['FIAScan']

# %%
# adjust parameter
UpperVertex = Autolab.CommandParameterDouble(myCommand.Signals['Upper vertex'])
UpperVertex.Value = 2

# monitor readings (except FRA measurement)
potential = instrument.Ei.Sampler.GetSignal('WE(1).Potential')
Potential = potential.Value

# read data
potential = Autolab.CommandParameterDoubleList(myCommand.Signals['Potential'])
MeasuredPotential = potential.Value

instrument.Disconnect()

# %%
# initializing the class first
autolab = EC.AUTOLAB(sdk=SDK,adx=ADX)
autolab.CMD = True # optional: Enable CMDLOG or not, it's good if you want to trace the code

# %%
try:
    if autolab.connectToAutolab(HDW): # first we need to connect to our instrument
        print("Connecting to AUTOLAB successfully....")
        autolab.setMode('Galvanostatic')
        autolab.setCurrentRange(0.001)
        
        # load procedure and command
        myProcedure = autolab.autolab.LoadProcedure(NOX)
        myCommand = myProcedure.Commnads('FIAScan')
        
        # adjust input parameters 
        # param = Autolab.CommandParameterDouble(myCommand.Signals['parameter name'])
        # param.value = 2
        
        # # read measured data (potential)
        # data = Autolab.CommandParameterDoubleList(myCommand.Signals['Potential'])
        # point = data.value
        
        # # do measurement
        # # autolab.measure(NOX) # it will take times till measrement finish
        
        # # monitor time and potential/current
        # reading = autolab.Ei.Sampler.GetSignals("WE(1).Potential")
        # value = reading.value
        
        # autolab.saveAs("test_file")
except:
    print("Connecting to AUTOLAB FAIL....")


# %%
# it is a good habit to del the instance at the end of the script
del autolab