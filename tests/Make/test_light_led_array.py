# %% 
from .. import init
from controllably.Make.Light import LEDArray
me = LEDArray('COM4', channels=[0,1,2,3])
me.__dict__
# %%
me.setPower(255,3, channel=0)
# %%
me.setPower(128,4, channel=1)
# %%
me.setPower(64,5, channel=2)
# %%
me.setPower(32,6, channel=3)
# %%
me.getTimedChannels()
# %%
me.setPower(200,3)
# %%
me.turnOff()
# %%
