# %%
import init
from controllably.View.Thermal import Flir
# %%
me = Flir.AX8('192.168.1.111')   # FIXME: unable to connect to 192.168.1.120
me.view()
me.__dict__

# %%
spots = {1:(40,35)}
me.enableSpotmeter(spots)
me.getSpotPositions([1])

# %%
me.getSpotTemperatures([1])

# %%
