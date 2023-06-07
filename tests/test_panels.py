# %%
import init
from controllably.Control.GUI import MoverPanel
from controllably.Move.Cartesian import Primitiv
from controllably.Move.Jointed.Dobot import M1Pro
from controllably.Transfer.Substrate import Dobot
# you = Primitiv('COM4')
you = M1Pro('192.168.2.21')
gui1 = MoverPanel(you, axes='XYZa')
# gui.runGUI()
gui1.runGUI()

# %%
import init
from controllably.Control.GUI import LiquidPanel
from controllably.Transfer.Liquid.Sartorius import Sartorius
me = Sartorius('COM17')
me.getInfo('BRL1000')
me.reagent = "Ethanol"
gui2 = LiquidPanel(liquid=me)
# gui2.runGUI()

# %%
import init
from controllably.Control.GUI import LiquidPanel
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
import init
from controllably.Control.GUI import CompoundPanel
gui = CompoundPanel(dict(
    mover=gui1, liquid=gui2
))
gui.runGUI()
# %%
import init
from controllably.Control.GUI import MeasurerPanel
from controllably.Measure.Electrical.Keithley import Keithley

me = Keithley()
gui = MeasurerPanel(me)
gui.runGUI()

# %%
import init
from controllably.Control.GUI import MakerPanel
from controllably.Make.Light import LEDArray
me = LEDArray('COM4', channels=[0,1,2,3])
me.__dict__
gui = MakerPanel(me)
gui.runGUI()

# %%
import init
from controllably.Control.GUI import MakerPanel
from controllably.Make.ThinFilm import SpinnerAssembly

me = SpinnerAssembly(
    ports=['COM13','COM14','COM15','COM16'], 
    channels=[1,2,3,4], 
    positions=[(50,0,0),(100,0,0),(150,0,0),(200,0,0)]
)
gui = MakerPanel(me)
gui.runGUI()

# %%
import init
from controllably.Control.GUI import MakerPanel
from controllably.Make.Mixture.QInstruments import BioShake
me = BioShake('COM27', verbose=False)
gui = MakerPanel(me)
gui.runGUI()

# %%
import init
from controllably.Move.Cartesian import Primitiv
# from controllably.Move.Jointed.Dobot import M1Pro
# from controllably.Transfer.Substrate import Dobot
# from controllably.Make.ThinFilm import SpinnerAssembly
# from controllably.Make.Mixture.QInstruments import BioShake
# from controllably.Measure.Electrical.Keithley import Keithley
# from controllably.Transfer.Liquid import SyringeAssembly
# from controllably.Transfer.Liquid.Pumps import Peristaltic

from controllably import guide_me
guide_me()

# %%
