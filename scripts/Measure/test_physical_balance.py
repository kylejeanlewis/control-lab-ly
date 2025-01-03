# %%
import init
import time
from controllably.Measure.Physical import MassBalance
import plotly.express as px
me = MassBalance('COM7')
# %%
me.zero()
me.toggleRecord(True)
time.sleep(10)
me.toggleRecord(False)
# %%
px.line(me.buffer_df, 'Time', 'Mass')
# %%
