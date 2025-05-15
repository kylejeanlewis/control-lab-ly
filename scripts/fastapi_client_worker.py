# %%
import requests
import json
from controllably.core.control import Controller, TwoTierQueue, Proxy
from controllably.core.interpreter import JSONInterpreter

def send_reply(reply):
    """
    Send a reply to the hub.
    """
    url = "http://localhost:8000/reply"
    response = requests.post(url, json=json.loads(reply))
    out = response.json()
    print(out)
    return out

def get_command(target):
    """
    Get a reply from the hub.
    """
    url = f"http://localhost:8000/command/{target}"
    response = requests.get(url)
    out = response.json()
    print(out)
    return out

# %%
worker = Controller('model', JSONInterpreter())
worker.subscribe(send_reply, 'request')

# %%
data = dict(object_id='999', method='qsize')
# %%
worker.transmitData(data)
# %%
