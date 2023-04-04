# %%
import init
import time
from controllably.Measure.Physical import MassBalance
me = MassBalance('COM22')
# %%
me.zero()
me.toggleRecord(True)
time.sleep(10)
me.toggleRecord(False)