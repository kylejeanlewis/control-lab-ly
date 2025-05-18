# %%
from controllably.core.control import TwoTierQueue, Proxy
from control_utils import create_socket_user
from controllably.core.connection import get_host

import time

# %%
user, user_pack = create_socket_user(get_host(), 12345, 'USER', relay=True)
time.sleep(1)

# %%
queue = Proxy(TwoTierQueue(), 'QUEUE')
queue.bindController(user)

# %%
queue.qsize()

# %%
queue.get_nowait()

# %%
queue.put(2000)

# %%
queue.get_nowait()

# %%