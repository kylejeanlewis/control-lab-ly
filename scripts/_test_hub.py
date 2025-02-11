# %%
import threading

import test_init
from controllably.core.control import Controller, start_server
from controllably.core.interpreter import JSONInterpreter

host = "127.0.0.1"  # Or "localhost"
port = 12345       # Choose a free port (above 1024 is recommended)
hub = Controller('relay', JSONInterpreter())

# Start server in a separate thread (so the client can run concurrently)
hub_thread = threading.Thread(target=start_server, args=(host, port, hub) ,daemon=True)
hub_thread.start()
    
# %%
