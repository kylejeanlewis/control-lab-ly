# %%
from init import library
from controllably import Helper, Factory, guide_me
from controllably.Control.GUI.Basic import *
guis = {}

# %%
from controllably.Move.Jointed.Dobot import M1Pro
details = Factory.get_details(Helper.read_yaml(library['configs']['m1pro_B1']))
me = M1Pro(**details['mover']['settings'])
gui = MoverPanel(me, axes='XYZa')
gui.runGUI()
guis['mover'] = gui

# %%
from controllably.Transfer.Liquid.Sartorius import Sartorius
me = Sartorius('COM17')
me.getInfo('BRL1000')
me.reagent = "Ethanol"
gui = LiquidPanel(me)
gui.runGUI()
guis['liquid'] = gui

# %%
from controllably.Transfer.Liquid import SyringeAssembly
from controllably.Transfer.Liquid.Pumps import Peristaltic
details = Factory.get_details(Helper.read_yaml(library['configs']['syringe_assembly']))
me = SyringeAssembly(pump=Peristaltic('COM28'), **details['liquid']['settings'])
me.aspirate(250, reagent='Ethanol', channel=1)
me.aspirate(500, reagent='Water', channel=2)
me.aspirate(750, reagent='IPA', channel=3)
gui = LiquidPanel(liquid=me)
gui.runGUI()

# %%
from controllably.Control.GUI import CompoundPanel
gui = CompoundPanel(guis)
gui.runGUI()

# %%
from controllably.Measure.Electrical.Keithley import Keithley
me = Keithley()
gui = MeasurerPanel(me)
gui.runGUI()

# %%
from controllably.Make.Light import LEDArray
me = LEDArray('COM4', channels=[0,1,2,3])
gui = MakerPanel(me)
gui.runGUI()

# %%
from controllably.Make.ThinFilm import SpinnerAssembly
details = Factory.get_details(Helper.read_yaml(library['configs']['spin_assembly']))
me = SpinnerAssembly(**details['spinner']['settings'])
gui = MakerPanel(me)
gui.runGUI()

# %%
from controllably.Make.Mixture.QInstruments import BioShake
me = BioShake('COM27', verbose=False)
gui = MakerPanel(me)
gui.runGUI()

# %%
