# %%
import init
from controllably.View.Thermal import Flir

# %%
me = Flir.AX8('192.168.1.111')   # FIXME: unable to connect to 192.168.1.120
# me.view()
me.__dict__
# %%
"""

cam.set_spotmeter_parameters(<parameters>)
cam.enable_spotmeter(instances=[(1,30,40), (2,50,20)])
cam.get_spotmeter_temps([1,2])
cam.disable_spotmeter([1,2])
"""
# %%
spots = {1:(50,50)}
me.enableSpotmeter(spots)

me
# %%
