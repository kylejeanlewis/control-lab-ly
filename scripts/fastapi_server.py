from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

from controllably.core.control import Controller
from controllably.core.interpreter import JSONInterpreter
import json

app = FastAPI()
outbound_replies = dict()
outbound_commands = dict()
worker_registry = dict()
hub = Controller('both', JSONInterpreter())
hub.setAddress('HUB')

class Address(BaseModel):
    """
    Address model for the FastAPI server.
    """
    sender: list[str]
    target: list[str]

class Command(BaseModel):
    """
    Request model for the FastAPI server.
    """
    request_id: str
    address: Address
    priority: bool = False
    rank: int|None = None
    object_id: str = ''
    method: str
    args: list[Any] = list()
    kwargs: dict[str, Any] = dict()

class Reply(BaseModel):
    """
    Reply model for the FastAPI server.
    """
    reply_id: str
    request_id: str
    address: Address
    priority: bool = False
    rank: int|None = None
    status: str
    data: Any


def place_command(command: Command) -> str:
    """
    Place a command in the outbound queue.
    """
    for target in command.address.target:
        if target not in outbound_commands:
            outbound_commands[target] = dict()
        outbound_commands[target][command.request_id] = command
    return 

def place_command_json(command_json_str: str) -> str:
    """
    Place a command (JSON) in the outbound queue.
    """
    command_dict = json.loads(command_json_str)
    command_dict['address'] = Address(**command_dict.pop('address', {'sender':[],'target':[]}))
    command = Command(**command_dict)
    return place_command(command)

def place_reply(reply: Reply) -> str:
    """
    Place a reply in the outbound queue.
    """
    outbound_replies[reply.request_id] = reply
    if reply.address.sender == 'HUB':
        for target in reply.address.target:
            if target not in worker_registry:
                worker_registry[target] = dict()
            worker_registry[target]['methods'] = reply.data
    return 

def place_reply_json(reply_json_str: str) -> str:
    """
    Place a reply (JSON) in the outbound queue.
    """
    reply_dict = json.loads(reply_json_str)
    reply_dict['address'] = Address(**reply_dict.pop('address', {'sender':[],'target':[]}))
    reply = Reply(**reply_dict)
    return place_reply(reply)

# APP
@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/registry")
def registry():
    """
    See the registry of workers.
    """
    return worker_registry

@app.post("/register/model")
def register_model(target: str):
    """
    Register the model with the hub.
    """
    if target not in worker_registry:
        worker_registry[target] = dict()
    outbound_commands[target] = dict()
    if target not in hub.callbacks['request']:
        hub.subscribe(place_command_json, 'request', target)
    hub.getMethods([target])
    return {"target": target}

@app.post("/command")
def send_command(command: Command):
    """
    Send a command to the hub.
    """
    place_command(command)
    return command.request_id
    
@app.get("/command/{target}")
def get_command(target: str):
    """
    Get a command from the hub.
    """
    request_ids = list(outbound_commands[target].keys()) if target in outbound_commands else []
    request_id = request_ids[0] if len(request_ids) > 0 else None
    if request_id is None:
        raise HTTPException(status_code=404, detail=f"No pending requests for target: {target}")
    return outbound_commands[target].pop(request_id)

@app.post("/reply")
def send_reply(reply: Reply):
    """
    Send a command to the hub.
    """
    place_reply(reply)
    return reply.reply_id
    
@app.get("/reply/{request_id}")
def get_reply(request_id: str):
    """
    Get a command from the hub.
    """
    if request_id not in outbound_replies:
        raise HTTPException(status_code=404, detail=f"No pending replies to request: {request_id}")
    return outbound_replies[request_id]
 