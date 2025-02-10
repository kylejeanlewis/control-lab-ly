# %%
import threading

import test_init
from controllably.core.control import Controller, TwoTierQueue, start_server, start_client
from controllably.core.interpreter import JSONInterpreter

# %% Client-server version
if __name__ == "__main__":
    host = "127.0.0.1"  # Or "localhost"
    port = 12345       # Choose a free port (above 1024 is recommended)
    worker = Controller('model', JSONInterpreter())
    worker.start()
    
    # Start server in a separate thread (so the client can run concurrently)
    server_thread = threading.Thread(target=start_server, args=(host, port, worker))
    server_thread.daemon = True  # Allow the main thread to exit even if the server is running
    server_thread.start()

# %% Hub-spoke version
if __name__ == "__main__":
    host = "127.0.0.1"  # Or "localhost"
    port = 12345       # Choose a free port (above 1024 is recommended)
    worker = Controller('model', JSONInterpreter())
    worker.start()
    
    # Start client in a separate thread
    worker_thread = threading.Thread(target=start_client, args=(host, port, worker, True))
    worker_thread.daemon = True  # Allow the main thread to exit even if the server is running
    worker_thread.start()

# %%
q = TwoTierQueue()
worker.register(q)

# %%
q.put_nowait('12345')


# %%
from controllably.Move.Cartesian import Gantry
mover = Gantry('COM0',[[100,100,100],[-100,-100,-100]], simulation=True)

# %%
worker.register(mover, 'MOVER')
worker.object_methods

# %%
