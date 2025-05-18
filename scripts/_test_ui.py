# %%
import tkinter as tk

import test_init
from controllably.core.implementations.gui import gui
from controllably.core.implementations.gui import move_gui
from controllably.core.implementations.gui import transfer_gui
from controllably.core.implementations.gui import view_gui

# %%
# import importlib
# importlib.reload(gui)
# importlib.reload(move_gui)
# importlib.reload(transfer_gui)
# importlib.reload(view_gui)

# %%
from controllably.Move.Cartesian import Gantry
gantry = Gantry('COM0', limits=[[100,100,100],[-100,-100,-100]], simulation=True)

# %%
move_app = move_gui.MovePanel()
move_app.bindObject(gantry)
move_app.show()

# %%
from controllably.Transfer.Liquid.Pump.TriContinent import TriContinent
pump = TriContinent('COM0', 5000, simulation=True, output_right=True, verbose=True)

# %%
liquid_app = transfer_gui.LiquidPanel()
liquid_app.bindObject(pump)
liquid_app.show()

# %%
from controllably.Transfer.Liquid.Pipette.Sartorius.sartorius import Sartorius
from controllably.Transfer.Liquid.Pipette.Sartorius.sartorius_api.sartorius_api import SartoriusDevice
pipette_device = SartoriusDevice('COM0', simulation=True, verbose=True)
pipette_device.connect()
pipette_device.getInfo(model='BRL1000')
pipette = Sartorius('COM0', simulation=True, device=pipette_device, verbose=True)

# %%
liquid_app.bindObject(pipette)
liquid_app.show()

# %%
from controllably.View.camera import Camera
cam = Camera(simulation=True)
cam.connect()

# %%
view_app = view_gui.ViewPanel(cam)
view_app.show()

# %%
panel = gui.Panel()
panel.addGrid(view_app, row=0, column=0, sticky="nsew")
panel.addGrid(move_app, row=0, column=1, sticky="nsew")
panel.addGrid(liquid_app, row=0, column=2, sticky='nsew')
panel.show()

# %%
