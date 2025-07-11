# %%
import init
from controllably.Measure.Electrical.Keithley import Keithley, programs

me = Keithley('192.109.209.100')
me.__dict__
# %%
me.loadProgram(programs.OCV)
me.measure()

# %%
me.loadProgram(programs.IV_Scan)
# %%
import numpy as np
import time

currents = np.linspace(0, 10E-9, 11, True)
# %%
me.measure(parameters=dict(currents=currents)) # FIXME: unable to run IV properly

# %%
voltages = np.linspace(0, 10E-9, 11, True)
count = 1
# %%
device = me.device
device.reset()
device.sendCommands(['ROUTe:TERMinals FRONT'])
device.configureSource('voltage', measure_limit=1)
device.configureSense('current', limit=1, four_point=True, count=count)
device.makeBuffer()
device.beep()

for voltage in voltages:
    device.setSource(value=voltage)
    device.toggleOutput(on=True)
    device.run()
    time.sleep(0.1*count)
time.sleep(1)
data_df = device.readAll()
device.beep()
device.getErrors()

# %%
device = me.device
device.reset()
device.sendCommands(['ROUTe:TERMinals FRONT'])
device.configureSource('current', measure_limit=2)
device.configureSense('voltage', limit=2, four_point=True, count=1)
device.makeBuffer()
device.beep()

# %%
device.setSource(0)
device.toggleOutput(True)
volts = []
for _ in range(100):
    volt = device._query("MEASure:VOLTage?")
    volt = float(volt)
    print(f"Voltage: {volt}")
    volts.append(volt)
# %%
import plotly.express as px
px.scatter(x=[i for i in range(len(volts))], y=volts)
# %%
