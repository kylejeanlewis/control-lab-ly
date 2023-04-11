# %%
import init
from controllably.Move.Cartesian import Primitiv
from controllably.Move.Jointed.Dobot import M1Pro
from controllably.Control.GUI import MoverPanel

# me = Primitiv('COM4')
you = M1Pro()

gui = MoverPanel(you, axes='XYZ')
gui.runGUI()
# %%
