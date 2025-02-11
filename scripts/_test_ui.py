# %%
import threading
import tkinter as tk

import test_init
from controllably.core.control import Controller, Proxy, start_client
from controllably.core.interpreter import JSONInterpreter

# %%
host = "127.0.0.1"  # Or "localhost"
port = 12345       # Choose a free port (above 1024 is recommended)
ui = Controller('view', JSONInterpreter())
args = [host, port, ui]

# %% Server-client version
ui_thread = threading.Thread(target=start_client, args=args, daemon=True)
ui_thread.start()
    
# %% Hub-spoke version
args.append(True)
ui_thread = threading.Thread(target=start_client, args=args, daemon=True)
ui_thread.start()

# %%
methods = ui.getMethods(private=True)

# %%
command = dict(object_id=list(methods.keys())[0], method='qsize')
ui.transmitRequest(command)

command = dict(object_id=list(methods.keys())[0], method='get_nowait')
ui.transmitRequest(command)

# %%
ui.data_buffer

# %%
from controllably.Move.Cartesian import Gantry
from controllably.GUI import MoveGUI

g = Gantry('COM0',[[100,100,100],[-100,-100,-100]], simulation=True)
p = Proxy(g, 'MOVER')
p.bindController(ui)

# %%
gui = MoveGUI(p)

# %%
root = tk.Tk()
gui.addTo(root)
gui.bindWidget(root)
root.mainloop()

# %%
