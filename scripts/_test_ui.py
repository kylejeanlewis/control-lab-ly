# %%
import tkinter as tk

import test_init
from controllably.GUI import gui
from controllably.GUI import move_gui
from controllably.GUI import transfer_gui

# %%
import importlib
importlib.reload(gui)
importlib.reload(move_gui)
importlib.reload(transfer_gui)

# %%
panel = gui.Panel()
panel.show()

# %%
move_app = move_gui.MovePanel()
move_app.show()

# %%
liquid_app = transfer_gui.LiquidPanel()
liquid_app.show()

# %%
panel.clearPanels()
panel.addGrid(move_app, row=0, column=0)
panel.addGrid(move_app, row=0, column=1)
panel.show()

# %%
from controllably.Move.Cartesian import Gantry
gantry = Gantry('COM0', limits=[[100,100,100],[-100,-100,-100]], simulation=True)

# %%
move_app.bindObject(gantry)
move_app.show()

# %%
from controllably.Transfer.Liquid.Pumps.TriContinent.tricontinent import TriContinent
pump = TriContinent('COM0',5000, simulation=True)

# %%
liquid_app.bindObject(pump)
liquid_app.show()

# %%
from controllably.Transfer.Liquid.Sartorius.sartorius import Sartorius
pipette = Sartorius('COM0', simulation=True)

# %%
from controllably.Make.Mixture.QInstruments.orbital_shaker_utils import _BioShake
shake = _BioShake('COM0', simulation=True)

# %%
