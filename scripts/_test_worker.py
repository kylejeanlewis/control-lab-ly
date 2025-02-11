# %%
import threading

import test_init
from controllably.core.control import Controller, start_server, start_client
from controllably.core.interpreter import JSONInterpreter

host = "127.0.0.1"
port = 12345
worker = Controller('model', JSONInterpreter())
terminate = threading.Event()
args = [host, port, worker]
kwargs = dict(terminate=terminate)
worker.start()

# %% Client-server version
worker_thread = threading.Thread(target=start_server, args=args, kwargs=kwargs, daemon=True)
worker_thread.start()

# %% Hub-spoke version
args.append(True)
worker_thread = threading.Thread(target=start_client, args=args, kwargs=kwargs, daemon=True)
worker_thread.start()

# %%
from controllably.core.control import TwoTierQueue
q = TwoTierQueue()
worker.register(q)
q.put_nowait('12345')

# %%
from controllably.Move.Cartesian import Gantry
mover = Gantry('COM0',[[100,100,100],[-100,-100,-100]], simulation=True)
worker.register(mover, 'MOVER')
worker.object_methods

# %%
