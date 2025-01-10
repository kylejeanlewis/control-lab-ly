# %%
import socket

import test_init
from controllably.core.connection import Server

host_ip = socket.gethostbyname(socket.gethostname())
host_port = 12345

# %%
server = Server(host_ip, host_port)
server.start(blocking=True)

# %%
