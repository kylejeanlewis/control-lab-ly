# %%
import threading

import test_init
from controllably.core.control import Controller, start_server
from controllably.core.interpreter import JSONInterpreter

host = "127.0.0.1"
port = 12345
hub = Controller('relay', JSONInterpreter())
terminate = threading.Event()
args = [host, port, hub]
kwargs = dict(terminate=terminate)

hub_thread = threading.Thread(target=start_server, args=args, kwargs=kwargs, daemon=True)
hub_thread.start()
    
# %%
