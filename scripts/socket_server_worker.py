# %%
from controllably.core.control import TwoTierQueue
from controllably.examples.control.socket import create_socket_worker
from controllably.core.connection import get_host

# %%
worker, worker_pack = create_socket_worker(get_host(), 12345, 'WORKER', relay=False)

# %%
queue = TwoTierQueue()
worker.register(queue, 'QUEUE')

# %%
queue.put(12345)

# %%
queue.qsize()

# %%