# %%
import init
from controllably.Measure.Electrical.Keithley import Keithley, programs

# %%
# sensor = Keithley('192.109.209.100', verbose=True)
sensor = Keithley('192.168.0.101', verbose=True)
sensor.__dict__

# %%
sensor.loadProgram(program_type=programs.Scan_Channels)
sensor.measure(
    channel_count = 4, scan_count = 100, scan_interval = 0.1, 
    fields = ('CHANnel','READing','RELative'), volt_range = 1
)

df = sensor.getData()
df.rename(columns={
    'CHANnel':'Channel', 'READing':'Volt', 'RELative':'Relative time'
}, inplace = True)
df

# %%
parameters = dict(
    channel_count = 3, scan_count = 100, scan_interval = 0.1, 
    fields = ('CHANnel','READing','RELative'), volt_range = 1
)
sensor.measure(parameters=parameters)

df = sensor.getData()
df.rename(columns={
    'CHANnel':'Channel', 'READing':'Volt', 'RELative':'Relative time'
}, inplace = True)
df
# %%
sensor.reset()