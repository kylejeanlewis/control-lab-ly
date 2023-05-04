# %%
import init
from controllably.Control.GUI import *

# %%
from controllably.Move.Cartesian import Primitiv
from controllably.Move.Jointed.Dobot import M1Pro
# you = Primitiv('COM4')
you = M1Pro('192.168.2.21')
gui1 = MoverPanel(you, axes='XYZa')
# gui.runGUI()

# %%
from controllably.Transfer.Liquid.Sartorius import Sartorius
me = Sartorius('COM17')
me.getInfo('BRL1000')
me.reagent = "Ethanol"
gui2 = LiquidPanel(liquid=me)
# gui2.runGUI()

# %%
from controllably.Transfer.Liquid import SyringeAssembly
from controllably.Transfer.Liquid.Pumps import Peristaltic
pump = Peristaltic('COM8')
me = SyringeAssembly(
    pump=pump,
    capacities=[3000]*8,
    channels=(1,2,3,4,5,6,7,8),
    offsets=[(0,0,0)]*8
)
me.aspirate(250, reagent='Ethanol', channel=1)
me.aspirate(500, reagent='Water', channel=2)
me.aspirate(750, reagent='IPA', channel=3)
gui2 = LiquidPanel(liquid=me)
# gui2.runGUI()

# %%
gui = CompoundPanel(dict(
    mover=gui1, liquid=gui2
))
gui.runGUI()
# %%
