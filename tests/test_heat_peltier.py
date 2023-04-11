# %% 
import init
from controllably.Make.Heat import Peltier
me = Peltier('COM26')
# %%
me.toggleRecord(True)
# %%
me.holdTemperature(30, 90)
# %%
me.setTemperature(35, blocking=False)
# %%
me.toggleRecord(False)
# %%
me.getTemperatures()
# %%
me.setTemperature(25, blocking=False)
# %%
import plotly.express as px
px.line(me.buffer_df, 'Time', ['Set','Hot','Cold','Power'])
# %%
