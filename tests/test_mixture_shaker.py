# %% 
import init
import time
from controllably.Make.Mixture.QInstruments import BioShake
me = BioShake('COM27')
me.info()

# %%
me.shakeGoHome()
me.getShakeState()
# %%
me.setElmLockPos()
me.getElmState()
# %%
me.setShakeTargetSpeed(1500)
# %%
me.setShakeAcceleration(5)
# %%
me.shakeOn()
time.sleep(7)
print(me.getShakeState())
print(me.getShakeActualSpeed())
time.sleep(60)
me.shakeOff()
time.sleep(7)
me.getShakeState()
# %%