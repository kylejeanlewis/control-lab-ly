# %%
import init
from controllably.Measure.Electrical.Keithley import Keithley, programs
me = Keithley('192.168.1.104')

# %%
me.loadProgram(programs.OCV)
me.measure()

# %%
me.loadProgram(programs.IV_Scan)
me.measure(parameters=dict(currents=[0.1,0.2,0.3]))
# %%
