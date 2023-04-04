# %% 
import init
from controllably.Make.Heat import Peltier
me = Peltier('COM26')
# %%
me.toggleRecord(True)
me.holdTemperature(30, 30)
me.setTemperature(35, blocking=False)
me.toggleRecord(False)