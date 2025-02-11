# %%
import threading
import tkinter as tk

import test_init
from controllably.core.control import Controller, Proxy, start_client
from controllably.core.interpreter import JSONInterpreter

host = "127.0.0.1"
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
from controllably.Move.Cartesian import Gantry
from controllably.GUI import MoveGUI

gantry = Gantry('COM0',[[100,100,100],[-100,-100,-100]], simulation=True)
proxy = Proxy(gantry, 'MOVER')
gui = MoveGUI()

# %%
root = tk.Tk()
gui.addTo(root)

proxy.bindController(ui)
gui.bindObject(proxy)
gui.bindWidget(root)
root.mainloop()

# %%
