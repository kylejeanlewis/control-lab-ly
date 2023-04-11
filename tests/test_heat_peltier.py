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
me.clearCache()
me.toggleRecord(True)
for temperature in [25,30,35,40,45,50]:
    me.holdTemperature(temperature, 90)
me.toggleRecord(False)
me.setTemperature(25)
fig = px.line(me.buffer_df, 'Time', ['Set','Hot','Cold','Power'])
fig.show()
# %%
