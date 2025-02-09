# %%
import threading

import test_init
from controllably.core.control import Controller, JSONInterpreter, start_server

if __name__ == "__main__":
    host = "127.0.0.1"  # Or "localhost"
    port = 12345       # Choose a free port (above 1024 is recommended)
    hub = Controller('relay', JSONInterpreter())
    
    # Start server in a separate thread (so the client can run concurrently)
    server_thread = threading.Thread(target=start_server, args=(host, port, hub))
    server_thread.daemon = True  # Allow the main thread to exit even if the server is running
    server_thread.start()
    
# %%
