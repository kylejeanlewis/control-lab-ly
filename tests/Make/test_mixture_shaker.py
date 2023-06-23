# %% 
from .. import init
import time
from controllably.Make.Mixture.QInstruments import BioShake
you = BioShake('COM27', verbose=True)
you.__info__()

# %%
you.shake(speed=1000, duration=60, acceleration=10)
you.isAtSpeed()
# %%
you.getShakeTimeLeft()
# %%
you.isAtSpeed()
# %%
you.toggleGrip(on=False)
you.shake()
time.sleep(30)
you.toggleShake(on=False, home=False)
# %%
you.home()
# %%
you.shake(speed=199,acceleration=10,duration=30)
# %%
you.shake(speed=3000,acceleration=10,duration=30)
# ===========
# %%
me = you.device
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
# ELM must be locked before shakeOn
me.shakeOn()
time.sleep(7)
print(me.getShakeState())
print(me.getShakeActualSpeed())
time.sleep(60)
me.shakeOff()
time.sleep(7)
me.getShakeState()
# %%
me.getTempLimiterMax()
# %%
me.getTempLimiterMin()
# %%
me.getTempMax()
# %%
me.getTempMin()
# %%
