# %% [markdown]
# # Control Module Tutorial
#
# This tutorial demonstrates the usage of the `controllably.core.control` module, including the `TwoTierQueue`, `Controller`, and `Proxy` classes.
# It covers the creation and management of a two-tier queue system, as well as the setup of controllers for handling requests and data flow.
# 
# ## TwoTierQueue
#
# The `TwoTierQueue` class implements a queue with two levels of priority: normal and high-priority tasks.
# It allows for the addition of tasks with varying levels of importance and ensures that high-priority tasks are processed before normal tasks.
# It closely follows the interface of Python's built-in `queue.Queue` and `queue.PriorityQueue`.

# %%
from queue import Queue, PriorityQueue
from controllably.core.control import TwoTierQueue

queue = TwoTierQueue()
print(f'{queue.qsize()=}')

# %% [markdown]
# ### Adding Tasks
# Tasks can be added to the queue using various methods:
# - `put(item)`: Adds a normal task to the end of the normal queue.
# - `put_nowait(item)`: Adds a normal task to the end of the normal queue without blocking.
# - `put_queue(item)`: Adds a normal task to the end of the normal queue (alias for `put`).
# - `put_priority(item, rank=0)`: Adds a high-priority task to the high-priority queue with an optional rank (lower rank means higher priority).
# - `put_first(item)`: Adds a very important task to the front of the high-priority queue.

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
# ### Retrieving Tasks
# Tasks can be retrieved from the queue using the following methods:
# - `get()`: Retrieves and removes the highest-priority task from the queue, blocking if necessary.
# - `get_nowait()`: Retrieves and removes the highest-priority task from the queue without blocking.

# %%
while not queue.empty():
    print(f'{queue.qsize()=}')
    print(queue.get_nowait())
    queue.task_done()
print(f'{queue.qsize()=}')

# %% [markdown]
# ### Limited Size Queue
# The `TwoTierQueue` can be configured with size limits for both normal and high-priority queues.

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

# %% [markdown]
# Attempting to add more high-priority tasks than the limit will raise an exception.
# The `TwoTierQueue.full()` method can be used to check if any of the normal and high-priority queues are full.
# Meanwhile, normal tasks can still be added until their limit is reached.

# %%
print(f'{limited_queue.full()=}')
limited_queue.put_nowait("task3")

# %% [markdown]
# Retrieving tasks from the two-tier queue will prioritize high-priority tasks first.

# %%
print(limited_queue.get_nowait())

# %% [markdown]
# After retrieving a high-priority task, a new high-priority task can be added.

# %%
limited_queue.put_nowait("impt2", priority=True, rank = current_priority_rank-1)

# %% [markdown]
# The normal queue can be filled up to its limit.

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

# %% [markdown]
# ## Controller and Proxy
# The `Controller` class manages communication between different components using a publish-subscribe model.
# The `Proxy` class acts as an intermediary for registered objects, allowing them to be controlled remotely via a `Controller`.

# %%
from controllably.core.control import Controller, Proxy
from controllably.core.interpreter import JSONInterpreter

# %% [markdown]
# Create controllers for peer-to-peer (P2P) and hub-and-spoke (HNS) communication patterns.
# 
# ### Peer-to-Peer (P2P)
# In the P2P pattern, the 'model' controller directly communicates with the 'view' controller.
# First, we create the worker and user controllers.

# %%
# 'model' controllers receives requests, triggers execution in registered objects, 
# and transmits the resultant data
p2p_worker = Controller(role='model', interpreter=JSONInterpreter())
p2p_worker.setAddress('WORKER_P2P')

# 'view' controllers transmits requests and receives the resultant data
p2p_user = Controller(role='view', interpreter=JSONInterpreter())
p2p_user.setAddress('USER_P2P')

# %% [markdown]
# Next, we set up the communication flow between the user and worker controllers.

# %%
# request flow: USER -> WORKER
p2p_user.subscribe(callback=p2p_worker.receiveRequest, callback_type='request', address='WORKER_P2P')
# data flow: USER -> WORKER
p2p_worker.subscribe(callback=p2p_user.receiveData, callback_type='data', address='USER_P2P')

# %% [markdown]
# Now we can register the `queue` with the worker controller and bind the `queue_proxy` to the user controller.
# Registration requires the object to be registered and a unique name for the object within the controller.
# The worker execution loop is then started in order to receive commands, execute them, and return the output.

# %%
p2p_worker.register(queue, 'QUEUE1')
p2p_worker.start()
print(f'{queue.qsize()=}')

# %% [markdown]
# Create a proxy for the two-tier queue created above.
# The proxy will allow remote control of the queue via controllers.
# The proxy is also a subclass of the target class (i.e. `TwoTierQueue`), so that they can be used interchangeably.
# 
# To create a proxy, the target class is required as a blueprint to construct the proxy.
# The matching unique name is also provided so that it knows which object it is paired with.

# %%
queue_proxy = Proxy(TwoTierQueue, 'QUEUE1')
print(f'{issubclass(type(queue_proxy), TwoTierQueue)=}')

queue_proxy.bindController(p2p_user)

# %% [markdown]
# The proxy can then be used just as if it is the original object, using the object's methods and accessing the object's attributes.

# %%
queue_proxy.put_nowait("task1")
print(f'{queue.qsize()=}')

# %%
while not queue_proxy.empty():
    print(f'{queue_proxy.qsize()=}')
    print(queue_proxy.get_nowait())
    queue_proxy.task_done()
print(f'{queue_proxy.qsize()=}')

# %% [markdown]
# ### Hub-and-spoke (HNS)
# In the HNS pattern, both 'model' and 'view' controller are connected to a central 'hub' controller, and any communication is relayed through the hub.
# Here, on top of the worker and user controllers, a hub controller is also created.

# %%
# 'model' controllers receives requests, triggers execution in registered objects, 
# and transmits the resultant data
hns_worker = Controller(role='model', interpreter=JSONInterpreter())
hns_worker.setAddress('WORKER_HNS')

# 'view' controllers transmits requests and receives the resultant data
hns_user = Controller(role='view', interpreter=JSONInterpreter())
hns_user.setAddress('USER_HNS')

# 'relay' controllers bridges communication between `model` and `view` controllers
hns_hub = Controller(role='relay', interpreter=JSONInterpreter())
hns_hub.setAddress('HUB_HNS')

# %% [markdown]
# Next, we set up the communication flow between the user and worker controllers, with the hub controller.

# %%
# request flow: USER -> HUB -> WORKER
hns_user.subscribe(callback=hns_hub.relayRequest, callback_type='request', address='HUB_HNS', relay=True)
hns_hub.subscribe(callback=hns_worker.receiveRequest, callback_type='request', address='WORKER_HNS')

# data flow: WORKER -> HUB -> USER
hns_worker.subscribe(callback=hns_hub.relayData, callback_type='data', address='HUB_HNS', relay=True)
hns_hub.subscribe(callback=hns_user.receiveData, callback_type='data', address='USER_HNS')

# %% [markdown]
# 
# Similarly, we register the `limited_queue` with the worker controller and bind the `limited_queue_proxy` to the user controller.
# Registration requires the object to be registered and a unique name for the object within the controller.
# The worker execution loop is then started in order to receive commands, execute them, and return the output.

# %%
hns_worker.register(limited_queue, 'QUEUE2')
hns_worker.start()
print(f'{limited_queue.qsize()=}')

# %% [markdown]
# Again, a proxy is created using the target class `TwoTierQueue` and the corresponding unique object name

# %%
limited_queue_proxy = Proxy(TwoTierQueue, 'QUEUE2')
limited_queue_proxy.bindController(hns_user)

# %% [markdown]
# The proxy can then be used just as if it is the original object, using the object's methods and accessing the object's attributes.

# %%
limited_queue_proxy.put_nowait("task1")
limited_queue_proxy.put_nowait("task2")
print(f'{limited_queue_proxy.qsize()=}')

# %%
while not limited_queue_proxy.empty():
    print(f'{limited_queue_proxy.qsize()=}')
    print(limited_queue_proxy.get_nowait())
    limited_queue_proxy.task_done()
print(f'{limited_queue_proxy.qsize()=}')

# %% [markdown]
# ### Changing the connection
# The proxies can change the pathway by which commands and data is transmitted.
# 
# Use `Proxy.releaseController()` to drop the associated user controller.
# Use `Controller.unregister()` to remove the principal object from the worker's list of objects that user controllers can connect to.

# %%
limited_queue_proxy.releaseController()
hns_worker.unregister('QUEUE2')

# %% [markdown]
# Likewise, a different worker can register the object, and the proxy can bind to the corresponding controller.

# %%
p2p_worker.register(limited_queue, 'QUEUE2')
limited_queue_proxy.bindController(p2p_user)

# %% [markdown]
# Here, we just demonstrate that the command and data transmission pathway has changed, 
# while the principal object and proxy still communicate like before.

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

# %% [markdown]
# The execution loop on the workers can be stopped using the `Controller.stop()` method.

# %%
p2p_worker.stop()
hns_worker.stop()

# %% [markdown]
# In order to make the worker active again, the `start` method has to be called.
# A single object can be registered to multiple workers, as long as the object identifier has not already been registered on the new worker.

# %%
hns_worker.start()
hns_worker.register(queue, 'QUEUE3')

# %% [markdown]
# A new proxy can be created to interact with the same principal object.

# %%
second_proxy = Proxy(TwoTierQueue, 'QUEUE3')
second_proxy.bindController(hns_user)

# %%
second_proxy.put_nowait("extra_task")
print(f'{second_proxy.get_nowait()=}')

# %% [markdown]
# # Examples
# Further examples of how to setup different kinds of communication pathways like sockets and fastapi
# can be found in `control-lab-ly/scripts/control`.
# 
# ## Sockets
# Sockets can be used for inter-process communication (IPC) on the same machine or over a network.
# 
# On the worker side, refer to the following for the respective modes of operation:
# - Peer-to-Peer: `control-lab-ly/scripts/control/socket/socket_server_worker.py`
# - Hub-and-Spoke: 
#   - `control-lab-ly/scripts/control/socket/start_socket_hub_worker.py`
#   - `control-lab-ly/scripts/control/socket/socket_client_worker.py`
# 
# On the User side, refer to `control-lab-ly/scripts/control/socket/start_socket_user.py`.
# 
# ## FastAPI
# The only mode of operation is Hub-and-Spoke.
# Refer to the following for the respective sides:
# - Hub: `control-lab-ly/scripts/control/fastapi/start_fastapi_server.py`
# - Worker: `control-lab-ly/scripts/control/fastapi/fastapi_client_worker.py`
# - User: `control-lab-ly/scripts/control/fastapi/fastapi_client_user.py`
# 
# ## SiLA2
# SiLA2 is a standard for laboratory device communication.
# Refer to the documentation at `control-lab-ly/controllably/examples/sila/readme.md` for more details.
# 
# 1. Generate the SiLA2 package for your setup using `control-lab-ly/scripts/control/sila/sila_demo/generate_sila_package.py`.
# 2. Start the SiLA2 server using `control-lab-ly/scripts/control/sila/sila_demo/server.py`.
# 3. Use the SiLA2 client to interact with the server using `control-lab-ly/scripts/control/sila/sila_demo/client.py`.


# %%
