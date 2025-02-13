# %%
import threading
import tkinter as tk

import test_init
from controllably.core.connection import get_host
from controllably.core.control import Controller, Proxy, start_client
from controllably.core.interpreter import JSONInterpreter

from controllably.Move.Cartesian import Gantry
from controllably.GUI import MoveGUI, GUI

# %%
host = get_host()
port = 12345 
ui = Controller('view', JSONInterpreter())
terminate = threading.Event()
args = [host, port, ui]
kwargs = dict(terminate=terminate)

# %% Server-client version
ui_thread = threading.Thread(target=start_client, args=args, kwargs=kwargs, daemon=True)
ui_thread.start()
    
# %% Hub-spoke version
args.append(True)
ui_thread = threading.Thread(target=start_client, args=args, kwargs=kwargs, daemon=True)
ui_thread.start()

# %%
methods = ui.getMethods(private=True)
methods

# %%
command = dict(object_id=list(methods.keys())[0], method='qsize')
size_request = ui.transmitRequest(command)

command = dict(object_id=list(methods.keys())[0], method='get_nowait')
content_request = ui.transmitRequest(command)

# %%
size = ui.retrieveData(size_request)
content = ui.retrieveData(content_request)
ui.data_buffer

# %%
gantry = Gantry('COM0',[[100,100,100],[-100,-100,-100]], simulation=True)
proxy = Proxy(gantry, 'MOVER')
gui = MoveGUI()

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
gui = GUI()
mgui = MoveGUI()
ngui = MoveGUI()

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
gui = MoveGUI()
gui.show()

# %%
