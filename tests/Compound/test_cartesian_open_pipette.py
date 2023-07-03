# %%
from init import library
from controllably import Factory, Helper, guide_me
from controllably.Compound.LiquidMover import LiquidMoverSetup
from controllably.Control.GUI import CompoundPanel
from controllably.Control.GUI.Basic import MoverPanel, LiquidPanel

# %%
details = Factory.get_details(Helper.read_yaml(library['configs']['open_pipette']))
us = LiquidMoverSetup(**details['setup']['settings'])
us.liquid.getInfo('BRL200')
# %%
us.loadDeck(library['deck']['layoutL3'])
us.__dict__
me = us.mover
you = us.liquid
me.__dict__
# %%
spin = me.deck.at('spincoater')
# %%
us.attachTip(tip_length=50.8)
me.__dict__
# %%
us.returnTip()
me.__dict__
# %%
us.ejectTip()
me.__dict__
# %%
# %%
gui1 = MoverPanel(me, axes='XYZ')
gui2 = LiquidPanel(you)
gui = CompoundPanel(dict(
    Mover=gui1,
    Liquid=gui2
))
gui.runGUI()

# %%
