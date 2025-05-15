# %%
import requests
import json
from controllably.core.control import Controller, TwoTierQueue, Proxy
from controllably.core.interpreter import JSONInterpreter

def send_command(command):
    """
    Send a command to the hub.
    """
    url = "http://localhost:8000/command"
    response = requests.post(url, json=json.loads(command))
    out = response.json()
    print(out)
    return out

def get_reply(request_id):
    """
    Get a reply from the hub.
    """
    url = f"http://localhost:8000/reply/{request_id}"
    response = requests.get(url)
    out = response.json()
    print(out)
    return out

# %%
user = Controller('view', JSONInterpreter())
user.subscribe(send_command, 'request', 'WORKER')

# %%
command = dict(object_id='999', method='qsize')
# %%
user.transmitRequest(command, ['WORKER'])
# %%
