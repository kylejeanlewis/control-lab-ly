# %%
import init
from controllably import Helper, guide_me
from controllably.Measure.Mechanical.PiezoRobotics import PiezoRobotics, programs

# %%
me = PiezoRobotics('COM19')
me.__dict__
me.device.verbose = True
# %%
me.device.toggleClamp(False)
# %%
me.loadProgram()
# %%
me.measure(repeat=2)
# %%
