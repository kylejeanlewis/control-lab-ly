# %%
import init
from controllably.Measure.Mechanical.PiezoRobotics import PiezoRobotics, programs
me = PiezoRobotics('COM19')
me.loadProgram()
me.measure()