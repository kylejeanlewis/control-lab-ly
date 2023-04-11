# %%
import init
from controllably.Measure.Mechanical.PiezoRobotics import PiezoRobotics, programs

me = PiezoRobotics('COM19')
me.__dict__
# %%
me.device.toggleClamp(True)
# %%
me.loadProgram()
# %%
me.measure(repeat=2)
# %%
