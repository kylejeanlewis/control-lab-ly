# %%
import tkinter as tk

import test_init
from controllably.GUI import gui
from controllably.GUI import move_gui
from controllably.GUI import transfer_gui
from controllably.GUI import view_gui

# %%
import importlib
importlib.reload(gui)
importlib.reload(move_gui)
importlib.reload(transfer_gui)
importlib.reload(view_gui)

# %%
panel = gui.Panel()
# panel.show()

# %%
move_app = move_gui.MovePanel()
# move_app.show()

# %%
liquid_app = transfer_gui.LiquidPanel()
# liquid_app.show()

# %%
panel.clearPanels()
panel.addGrid(move_app, row=0, column=0)
panel.addGrid(liquid_app, row=0, column=1)
panel.show()

# %%
from controllably.Move.Cartesian import Gantry
gantry = Gantry('COM0', limits=[[100,100,100],[-100,-100,-100]], simulation=True)

# %%
move_app.bindObject(gantry)
move_app.show()

# %%
from controllably.Transfer.Liquid.Pumps.TriContinent.tricontinent import TriContinent
from controllably.Transfer.Liquid.Pumps.TriContinent.tricontinent_api.tricontinent_api import TriContinentDevice
pump_device = TriContinentDevice('COM0', simulation=True, verbose=True)
pump_device.connect()
pump_device.getInfo()
pump = TriContinent('COM0', 5000, simulation=True, device=pump_device, verbose=True)

# %%
liquid_app.bindObject(pump)
liquid_app.show()

# %%
from controllably.Transfer.Liquid.Sartorius.sartorius import Sartorius
from controllably.Transfer.Liquid.Sartorius.sartorius_api.sartorius_api import SartoriusDevice
pipette_device = SartoriusDevice('COM0', simulation=True, verbose=True)
pipette_device.connect()
pipette_device.getInfo(model='BRL1000')
pipette = Sartorius('COM0', simulation=True, device=pipette_device, verbose=True)

# %%
liquid_app.bindObject(pipette)
liquid_app.show()

# %%
from controllably.Make.Mixture.QInstruments.orbital_shaker_utils import _BioShake
shake = _BioShake('COM0', simulation=True)

# %%
from controllably.View.camera import Camera
cam = Camera(simulation=True)
cam.connect()

# %%
view_app = view_gui.ViewPanel(cam)
view_app.show()

# %%
panel.addGrid(view_app, row=0, column=0, sticky="nsew")
panel.addGrid(move_app, row=0, column=1, sticky="nsew")
panel.addGrid(liquid_app, row=0, column=2, sticky='nsew')
panel.show()

# %%
