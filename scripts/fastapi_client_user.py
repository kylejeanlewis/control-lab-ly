# %%
from controllably.core.control import TwoTierQueue, Proxy
from control_utils import create_fastapi_user

# %%
user, user_pack = create_fastapi_user('http://localhost', 8000, 'USER')

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