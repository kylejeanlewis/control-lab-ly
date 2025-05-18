# %%
import threading
import tkinter as tk

import test_init
from controllably.core.connection import get_host
from controllably.core.control import Controller, Proxy, TwoTierQueue
from controllably.core.interpreter import JSONInterpreter
from controllably.core.implementations.control.socket_control import SocketClient
from controllably.GUI import MovePanel, Panel, LiquidPanel

from controllably.Move.Cartesian import Gantry
from controllably.Transfer.Liquid.Pipette.Sartorius.sartorius import Sartorius
from controllably.Transfer.Liquid.Pump.TriContinent.tricontinent import TriContinent

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# %%
host = '192.109.209.100' #get_host()
host = get_host()
port = 12345 
ui = Controller('view', JSONInterpreter())
terminate = threading.Event()
args = [host, port, ui]
kwargs = dict(terminate=terminate)

# %% Server-client version
ui_thread = threading.Thread(target=SocketClient.start_client, args=args, kwargs=kwargs, daemon=True)
ui_thread.start()
    
# %% Hub-spoke version
args.append(True)
ui_thread = threading.Thread(target=SocketClient.start_client, args=args, kwargs=kwargs, daemon=True)
ui_thread.start()

# %%
methods = ui.getMethods(private=True)
methods

# %%
p = Proxy(TwoTierQueue(),list(methods.keys())[0])
p.bindController(ui)
p.get_nowait()

# %%
# gantry = Gantry('COM0',[[100,100,100],[-100,-100,-100]], simulation=True)
proxy = Proxy(Gantry, 'MOVER')
gui = MovePanel()

# %%
proxy.bindController(ui)
gui.bindObject(proxy)
gui.show()

# %%
proxy.remote = True
position = proxy.move('x',-10)
position

# %%
proxy.remote = False
position = proxy.move('x',10)
position

# %%
gui = Panel()
mgui = MovePanel()
ngui = MovePanel()

# %%
gui.addPack(mgui, side=tk.LEFT)
gui.addPack(ngui)
gui.show()

# %%
mgui.show()

# %%
gui.addGrid(mgui, row=0, column=0)
gui.addGrid(ngui, row=1, column=1)
gui.show()

# %%
move_gui = MovePanel()
move_gui.show()

# %%
liquid_gui = LiquidPanel()
liquid_gui.show()

# %%
pipette = Proxy(Sartorius, 'PIPETTE')
pipette.bindController(ui)

# %%
pump = Proxy(TriContinent, 'PUMP')
pump.bindController(ui)

# %%
liquid_gui.bindObject(pipette)
liquid_gui.show()

# %%
liquid_gui.bindObject(pump)
liquid_gui.show()

# %%
