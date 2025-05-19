# %%
from controllably.core.control import TwoTierQueue
from controllably.core.implementations.control.control_utils import create_fastapi_worker

# %%
worker1, worker1_pack = create_fastapi_worker('http://localhost', 8000, 'WORKER1')
worker2, worker2_pack = create_fastapi_worker('http://localhost', 8000, 'WORKER2')
worker1_pack['client'] == worker2_pack['client']

# %%
queue = TwoTierQueue()
queue1 = TwoTierQueue()
worker1.register(queue, 'QUEUE')
worker1.register(queue1, 'QUEUE1')
worker1_pack['client'].update_registry(worker1)

# %%
queue2 = TwoTierQueue()
worker2.register(queue, 'QUEUE2')
worker2_pack['client'].update_registry(worker2)

# %%
queue.put(12345)

# %%
queue.qsize()

# %%