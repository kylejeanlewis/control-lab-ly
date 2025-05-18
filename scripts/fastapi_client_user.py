# %%
from controllably.core.control import Controller, TwoTierQueue, Proxy
from controllably.core.interpreter import JSONInterpreter
from controllably.core.implementations.control.fastapi_control import FastAPIUserClient

client = FastAPIUserClient('http://localhost', 8000)

# %%
user = Controller('view', JSONInterpreter())
user.setAddress('USER')

# %%
client.join_hub(user)

# %%
queue = Proxy(TwoTierQueue(), 'QUEUE')
queue.bindController(user)

# %%
queue.qsize()
# %%
queue.get_nowait()

# %%
