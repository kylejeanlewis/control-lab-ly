# %%
from queue import Queue
import socket
from threading import Event, Thread

import test_init
from controllably.core.connection import Client, SocketUtils

host_ip = socket.gethostbyname(socket.gethostname())
host_port = 12345

# %%
print_queue = Queue()
trigger = Event()
printer_thread = Thread(target=SocketUtils.printer, args=(print_queue, trigger))
printer_thread.start()

# %%
client = Client(host_ip, host_port, print_queue=print_queue)
client.connect()

# %%
client1 = Client(host_ip, host_port)
client1.connect()
client2 = Client(host_ip, host_port, print_queue=print_queue)
client2.connect()

# %%
client.read()
# %%
client.read()
# %%
client.query('Hello World!')
# %%
client.query('')
# %%
client.query(' ')
# %%
client.disconnect()
# %%
# time.sleep(3)
client1.disconnect()
client2.disconnect()
