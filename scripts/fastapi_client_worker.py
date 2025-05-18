# %%
import requests
import json
from threading import Thread
import time
from typing import Any, Callable
from controllably.core.control import Controller, TwoTierQueue
from controllably.core.interpreter import JSONInterpreter

HOST = 'http://localhost:8000'

workers = dict()

def update_registry(worker: Controller, workers:dict[str, Controller]) -> dict[str, Any]:
    """
    Register a worker with the hub.
    """
    url = f"{HOST}/register/model?target={worker.address}"
    response = requests.post(url)
    registry = response.json()
    print(registry)
    if response.status_code == 200:
        workers[worker.address] = worker
        worker.subscribe(send_reply, 'data', 'HUB')
        worker.subscribe(lambda: json.dumps(get_command(worker.address)), 'listen', HOST)
        worker.receiveRequest(sender=HOST)
    return registry

def create_listen_loop(worker: Controller, sender:str|None = None) -> Callable:
    def loop():
        while True:
            time.sleep(0.1)
            worker.receiveRequest(sender=sender)
    return loop

def get_command(target: str) -> dict[str, Any]:
    """
    Get a reply from the hub.
    """
    url = f"{HOST}/command/{target}"
    while True:
        response = requests.get(url)
        if response.status_code == 200:
            break
        time.sleep(0.1)
    command = response.json()
    command['address']['sender'].append('HUB')
    print(command)
    return command

def send_reply(reply: str|bytes) -> str:
    """
    Send a reply to the hub.
    """
    reply_json = json.loads(reply)
    url = f"{HOST}/reply"
    response = requests.post(url, json=reply_json)
    reply_id = response.json()
    print(reply_id)
    return reply_id

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
update_registry(worker1, workers)

# %%
queue2 = TwoTierQueue()
worker2.register(queue, 'QUEUE2')
update_registry(worker2, workers)

# %%
thread1 = Thread(target=create_listen_loop(worker1, sender=HOST))
thread2 = Thread(target=create_listen_loop(worker2, sender=HOST))
thread1.start()
thread2.start()
    
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
