# %%
import init
import time
import serial
from controllably.Measure.Electrical.Keithley import KeithleyDevice
from controllably.Measure.Mechanical import LoadCell
from controllably.Measure.Physical.balance_utils import Balance
import plotly.express as px

# %%
device = KeithleyDevice('192.109.209.101')
device.__dict__

# %%
device1 = serial.Serial('COM43', 115200, timeout=1)
device1.__dict__

# %%
# me = LoadCell(device=device, verbose=True)
me = Balance(device=device1, verbose=True)

# %%
me.clearCache()
me.toggleRecord(True)
time.sleep(20)
me.toggleRecord(False)
# %%
px.scatter(me.buffer_df, 'Time', 'Value')
# %%
calib = 1/166322569.226326
you = Balance(device=device, calibration_factor=calib, verbose=True)
# %%
you.clearCache()
you.toggleRecord(True)
time.sleep(10)
you.toggleRecord(False)
px.scatter(you.buffer_df, 'Time', 'Mass')
# %%
you.clearCache()
you.toggleRecord(True)
time.sleep(10)
you.toggleRecord(False)