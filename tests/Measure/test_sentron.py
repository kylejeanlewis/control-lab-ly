# %%
import init
import time
from controllably.Measure.Chemical.Sentron import SentronProbe
import plotly.express as px
me = SentronProbe('COM9')
# %%
me.getReadings()
me.buffer_df

# %%
me.toggleRecord(True)
time.sleep(25)
me.toggleRecord(False)
# %%
px.line(me.buffer_df, 'Time', 'Mass')
# %%
