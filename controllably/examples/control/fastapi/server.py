# -*- coding: utf-8 -*-
# Key imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import uvicorn

# Standard library imports
import json
from typing import Any

# Local application imports
from ....core.control import Controller
from ....core.interpreter import JSONInterpreter

PORT = 8000
HOST = 'http://localhost'

app = FastAPI()
outbound_replies = dict()
outbound_commands = dict()
worker_registry = dict()
hub = Controller('both', JSONInterpreter(), relay_delay=0)
hub.setAddress('HUB')


class Command(BaseModel):
    """
    Request model for the FastAPI server.
    """
    request_id: str
    address: dict[str, list[str]]
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
    address: dict[str, list[str]]
    priority: bool = False
    rank: int|None = None
    status: str
    data: Any

def place_command(command: Command) -> str:
    """
    Place a command in the outbound queue.
    """
    targets = command.address.get('target',[])
    targets = targets or list(worker_registry.keys())
    for target in targets:
        if target not in outbound_commands:
            outbound_commands[target] = dict()
        outbound_commands[target][command.request_id] = command
    return command.request_id

def place_reply(reply: Reply) -> str:
    """
    Place a reply in the outbound queue.
    """
    targets = reply.address.get('target',[])
    if reply.request_id == 'registration':
        targets.append('HUB')
    outbound_replies[reply.request_id] = reply
    if 'HUB' in targets and reply.request_id == 'registration':
        for worker in reply.address.get('sender',[]):
            if worker not in worker_registry:
                worker_registry[worker] = dict()
            worker_registry[worker] = reply.data
    return reply.reply_id


# Main
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
    if target not in outbound_commands:
        outbound_commands[target] = dict()
    if target not in hub.callbacks['request']:
        hub.subscribe(lambda content: place_command(Command(**json.loads(content))), 'request', target)
    get_methods_command = dict(method='exposeMethods')
    hub.transmitRequest(get_methods_command, [target])
    return {'workers': [k for k in worker_registry]}


# Commands
@app.get("/commands")
def commands():
    """
    Get the commands in the outbound queue.
    """
    return outbound_commands

@app.post("/command")
def send_command(command: Command):
    """
    Send a command to the hub.
    """
    request_id = place_command(command)
    return {"request_id": request_id}
    
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

@app.get("/command/clear")
def clear_commands():
    """
    Clear the commands in the outbound queue.
    """
    outbound_commands.clear()
    return {"status": "cleared"}

@app.get("/command/clear/{target}")
def clear_commands_target(target: str):
    """
    Clear the commands in the outbound queue for a specific target.
    """
    if target in outbound_commands:
        outbound_commands[target].clear()
        return {"status": "cleared"}
    else:
        raise HTTPException(status_code=404, detail=f"No pending requests for target: {target}")


# Replies
@app.get("/replies")
def replies():
    """
    Get the replies in the outbound queue.
    """
    return outbound_replies

@app.post("/reply")
def send_reply(reply: Reply):
    """
    Send a command to the hub.
    """
    reply_id = place_reply(reply)
    return {"reply_id": reply_id}
    
@app.get("/reply/{request_id}")
def get_reply(request_id: str):
    """
    Get a command from the hub.
    """
    if request_id not in outbound_replies:
        raise HTTPException(status_code=404, detail=f"No pending replies to request: {request_id}")
    return outbound_replies[request_id]
 
@app.get("/reply/clear")
def clear_replies():
    """
    Clear the replies in the outbound queue.
    """
    outbound_replies.clear()
    return {"status": "cleared"}

@app.get("/reply/clear/{request_id}")
def clear_replies_target(request_id: str):
    """
    Clear the replies in the outbound queue for a specific request_id.
    """
    if request_id in outbound_replies:
        outbound_replies.pop(request_id)
        return {"status": "cleared"}
    else:
        raise HTTPException(status_code=404, detail=f"No pending replies to request: {request_id}")


def start_server(host: str = HOST, port: int = PORT):
    try:
        response = requests.get(f'{host}:{port}/')
        if response.status_code == 200:
            print("Server is running")
        else:
            print("Server is not running or returned an error status code")
    except requests.ConnectionError:
        print("Server was not running, starting server now...")
        uvicorn.run(app, host='0.0.0.0', port=port)
    
# Start the server if not yet running
if __name__ == "__main__":
    start_server()
