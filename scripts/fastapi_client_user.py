# %%
import requests
import json
import time
from typing import Any
from controllably.core.control import Controller, TwoTierQueue, Proxy
from controllably.core.interpreter import JSONInterpreter

HOST = 'http://localhost:8000'

users = dict()
request_ids = dict()

def join_hub(user: Controller, users:dict[str, Controller]) -> dict[str, Any]:
    """
    Join a hub.
    """
    url = f"{HOST}/registry"
    response = requests.get(url)
    registry = response.json()
    print(registry)
    users[user.address] = user
    for worker in registry:
        user.subscribe(send_command, 'request', worker)
        user.subscribe(lambda request_id: json.dumps(get_reply(request_id)), 'listen', worker)
    user.data_buffer['registration'] = {k:{'data':v} for k,v in registry.items()}
    return registry

def send_command(command:str|bytes, request_ids: dict[str, Controller], users: dict[str, Controller]) -> dict[str, Any]:
    """
    Send a command to the hub.
    """
    command_json = json.loads(command)
    url = f"{HOST}/command"
    response = requests.post(url, json=command_json)
    request_id = response.json()
    print(request_id)
    print(command_json)
    user_id = command_json.get('address', {}).get('sender', [None])[0]
    request_ids[request_id['request_id']] = users[user_id]
    return request_id

def get_reply(request_id: str):
    """
    Get a reply from the hub.
    """
    url = f"{HOST}/reply/{request_id}"
    while True:
        response = requests.get(url)
        if response.status_code == 200:
            break
        time.sleep(0.1)
    reply = response.json()
    print(reply)
    return reply

# %%
user = Controller('view', JSONInterpreter())
user.setAddress('USER')

# %%
join_hub(user)

# %%
queue = Proxy(TwoTierQueue(), 'QUEUE')
queue.bindController(user)

# %%
queue.qsize()
# %%
