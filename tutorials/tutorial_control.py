# %% [markdown]

# %%
from queue import Queue, PriorityQueue
from controllably.core.control import TwoTierQueue

queue = TwoTierQueue()
print(f'{queue.qsize()=}')

# %%
# Normal tasks
queue.put("task1")
queue.put_nowait("task2")
queue.put_queue("task3")

# Priority tasks
queue.put_nowait("impt1", priority=True)
queue.put_priority("impt2", rank=1)

# Very important tasks
queue.put_first("first")
queue.put_first("second")

# %% [markdown]

# %%
while not queue.empty():
    print(f'{queue.qsize()=}')
    print(queue.get_nowait())
    queue.task_done()
print(f'{queue.qsize()=}')

# %%
limited_queue = TwoTierQueue()
limited_queue.normal_queue = Queue(maxsize=10)
limited_queue.high_priority_queue = PriorityQueue(maxsize=4)

print(f'{limited_queue.priority_counter=}')
limited_queue.put_nowait("task1")
print(f'{limited_queue.priority_counter=}')
limited_queue.put_nowait("task2")
print(f'{limited_queue.priority_counter=}')
limited_queue.put_nowait("impt1", priority=True)
print(f'{limited_queue.priority_counter=}')
limited_queue.put_nowait("impt3", priority=True)
print(f'{limited_queue.priority_counter=}')
current_priority_rank = limited_queue.priority_counter
limited_queue.put_nowait("first", priority=True, rank=0)
print(f'{limited_queue.priority_counter=}')

# %%
limited_queue.put_nowait("task3")

# %%
print(limited_queue.get_nowait())

# %%
limited_queue.put_nowait("impt2", priority=True, rank = current_priority_rank-1)

# %%
i = limited_queue.normal_queue.qsize()
while not limited_queue.full():
    i += 1
    print(f'{limited_queue.qsize()=}')
    limited_queue.put_nowait(f"task{i}")
print(f'{limited_queue.qsize()=}')

# %%
while not limited_queue.empty():
    print(f'{limited_queue.qsize()=}')
    print(limited_queue.get_nowait())
    limited_queue.task_done()
print(f'{limited_queue.qsize()=}')

# %%
from controllably.core.control import Controller, Proxy
from controllably.core.interpreter import JSONInterpreter


# %%
queue_proxy = Proxy(TwoTierQueue, 'QUEUE1')
limited_queue_proxy = Proxy(TwoTierQueue, 'QUEUE2')

# %%
# 'model' controllers receives requests, triggers execution in registered objects, 
# and transmits the resultant data
p2p_worker = Controller(role='model', interpreter=JSONInterpreter())
p2p_worker.setAddress('WORKER_P2P')

# 'view' controllers transmits requests and receives the resultant data
p2p_user = Controller(role='view', interpreter=JSONInterpreter())
p2p_user.setAddress('USER_P2P')

# %%
# request flow: USER -> WORKER
p2p_user.subscribe(callback=p2p_worker.receiveRequest, callback_type='request', address='WORKER_P2P')
# data flow: USER -> WORKER
p2p_worker.subscribe(callback=p2p_user.receiveData, callback_type='data', address='USER_P2P')

# %%
p2p_worker.register(queue, 'QUEUE1')
p2p_worker.start()
print(f'{queue.qsize()=}')

queue_proxy.bindController(p2p_user)

queue_proxy.put_nowait("task1")
print(f'{queue.qsize()=}')

# %%
while not queue_proxy.empty():
    print(f'{queue_proxy.qsize()=}')
    print(queue_proxy.get_nowait())
    queue_proxy.task_done()
print(f'{queue_proxy.qsize()=}')

# %%
# 'model' controllers receives requests, triggers execution in registered objects, 
# and transmits the resultant data
hns_worker = Controller(role='model', interpreter=JSONInterpreter())
hns_worker.setAddress('WORKER_HNS')

# 'view' controllers transmits requests and receives the resultant data
hns_user = Controller(role='view', interpreter=JSONInterpreter())
hns_user.setAddress('USER_HNS')

# %%
# 'relay' controllers bridges communication between `model` and `view` controllers
hns_hub = Controller(role='relay', interpreter=JSONInterpreter())
hns_hub.setAddress('HUB_HNS')

# request flow: USER -> HUB -> WORKER
hns_user.subscribe(callback=hns_hub.relayRequest, callback_type='request', address='HUB_HNS', relay=True)
hns_hub.subscribe(callback=hns_worker.receiveRequest, callback_type='request', address='WORKER_HNS')

# data flow: WORKER -> HUB -> USER
hns_worker.subscribe(callback=hns_hub.relayData, callback_type='data', address='HUB_HNS', relay=True)
hns_hub.subscribe(callback=hns_user.receiveData, callback_type='data', address='USER_HNS')

# %%
hns_worker.register(limited_queue, 'QUEUE2')
hns_worker.start()
print(f'{limited_queue.qsize()=}')

# %%
limited_queue_proxy.bindController(hns_user)

limited_queue_proxy.put_nowait("task1")
limited_queue_proxy.put_nowait("task2")
print(f'{limited_queue_proxy.qsize()=}')

# %%
while not limited_queue_proxy.empty():
    print(f'{limited_queue_proxy.qsize()=}')
    print(limited_queue_proxy.get_nowait())
    limited_queue_proxy.task_done()
print(f'{limited_queue_proxy.qsize()=}')

# %%
limited_queue_proxy.releaseController()
hns_worker.unregister('QUEUE2')

# %%
p2p_worker.register(limited_queue, 'QUEUE2')
limited_queue_proxy.bindController(p2p_user)

# %%
limited_queue_proxy.put_nowait("task1")
limited_queue_proxy.put_nowait("task2")
limited_queue_proxy.put_nowait("task3")
print(f'{limited_queue_proxy.qsize()=}')

# %%
while not limited_queue_proxy.empty():
    print(f'{limited_queue_proxy.qsize()=}')
    print(limited_queue_proxy.get_nowait())
    limited_queue_proxy.task_done()
print(f'{limited_queue_proxy.qsize()=}')

# %%
p2p_worker.stop()
hns_worker.stop()

# %%
hns_worker.start()
hns_worker.register(queue, 'QUEUE3')

# %%
second_proxy = Proxy(TwoTierQueue, 'QUEUE3')
second_proxy.bindController(hns_user)

# %%
second_proxy.put_nowait("extra_task")
print(f'{second_proxy.get_nowait()=}')
# %%

# %%
