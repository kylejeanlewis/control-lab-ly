# %%
import threading

import test_init
from controllably.core.control import Controller, JSONInterpreter, start_client

# %% Client-server version
if __name__ == "__main__":
    host = "127.0.0.1"  # Or "localhost"
    port = 12345       # Choose a free port (above 1024 is recommended)
    ui = Controller('view', JSONInterpreter())
    
    # Start client in a separate thread
    ui_thread = threading.Thread(target=start_client, args=(host, port, ui))
    ui_thread.daemon = True  # Allow the main thread to exit even if the server is running
    ui_thread.start()
    
# %% Hub-spoke version
if __name__ == "__main__":
    host = "127.0.0.1"  # Or "localhost"
    port = 12345       # Choose a free port (above 1024 is recommended)
    ui = Controller('view', JSONInterpreter())
    
    # Start client in a separate thread
    ui_thread = threading.Thread(target=start_client, args=(host, port, ui, True))
    ui_thread.daemon = True  # Allow the main thread to exit even if the server is running
    ui_thread.start()
    
# %%
ui.getMethods(private=True)

# %%
methods = ui.getMethods(private=False)

# %%
command = dict(
    subject_id = list(methods.keys())[0],
    method = 'qsize'
)
ui.transmitRequest(command)

# %%
ui.data_buffer

# %%
command = dict(
    subject_id = list(methods.keys())[0],
    method = 'get_nowait'
)
ui.transmitRequest(command)

# %%
ui.data_buffer
# %%
