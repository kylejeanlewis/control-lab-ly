# %%
from threading import Thread

from controllably.core.control import Controller, TwoTierQueue
from controllably.core.interpreter import JSONInterpreter
from controllably.core.implementations.control.fastapi_control import FastAPIWorkerClient

client = FastAPIWorkerClient('http://localhost', 8000)

# %%
worker1 = Controller('model', JSONInterpreter())
worker1.setAddress('WORKER1')
worker1.start()

# %%
worker2 = Controller('model', JSONInterpreter())
worker2.setAddress('WORKER2')
worker2.start()

# %%
queue = TwoTierQueue()
queue1 = TwoTierQueue()
worker1.register(queue, 'QUEUE')
worker1.register(queue1, 'QUEUE1')
client.update_registry(worker1)

# %%
queue2 = TwoTierQueue()
worker2.register(queue, 'QUEUE2')
client.update_registry(worker2)

# %%
thread1 = Thread(target=client.create_listen_loop(worker1, sender=client.url))
thread2 = Thread(target=client.create_listen_loop(worker2, sender=client.url))
thread1.start()
thread2.start()

# %%
queue.put(12345)

# %%
