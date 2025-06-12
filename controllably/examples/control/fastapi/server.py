# -*- coding: utf-8 -*-
""" 
This module provides a FastAPI server for managing commands and replies in a distributed system.

Attributes:
    PORT (int): The port number for the FastAPI server.
    HOST (str): The host address for the FastAPI server.
    
## Functions:
    `place_command`: Place a command in the outbound queue.
    `place_reply`: Place a reply in the outbound queue.
    `start_server`: Start the FastAPI server if it is not already running.

<i>Documentation last updated: 2025-06-11</i>
"""
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
    
    Args:
        command (Command): The command to place in the outbound queue.
        
    Returns:
        str: The request ID of the command.
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
    
    Args:
        reply (Reply): The reply to place in the outbound queue.
        
    Returns:
        str: The reply ID of the reply.
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

def start_server(host: str = HOST, port: int = PORT):
    """
    Start the FastAPI server if it is not already running.
    
    Args:
        host (str): The host address for the server.
        port (int): The port number for the server.
    """
    try:
        response = requests.get(f'{host}:{port}/')
        if response.status_code == 200:
            print("Server is running")
        else:
            print("Server is not running or returned an error status code")
    except requests.ConnectionError:
        print("Server was not running, starting server now...")
        uvicorn.run(app, host='0.0.0.0', port=port)

# Main
@app.get("/")
def read_root() -> dict:
    """
    Root endpoint for the FastAPI server.
    
    Returns:
        dict: A simple greeting message.
    """
    return {"Hello": "World"}

@app.get("/registry")
def registry() -> dict:
    """
    See the registry of workers.
    
    Returns:
        dict: A dictionary containing the worker registry.
    """
    return worker_registry

@app.post("/register/model")
def register_model(target: str) -> dict:
    """
    Register the model with the hub.
    
    Args:
        target (str): The target worker to register.
        
    Returns:
        dict: A dictionary containing the list of registered workers.
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
def commands() -> dict:
    """
    Get the commands in the outbound queue.
    
    Returns:
        dict: A dictionary containing the outbound commands.
    """
    return outbound_commands

@app.post("/command")
def send_command(command: Command) -> dict:
    """
    Send a command to the hub.
    
    Args:
        command (Command): The command to send.
        
    Returns:
        dict: A dictionary containing the request ID of the command.
    """
    request_id = place_command(command)
    return {"request_id": request_id}
    
@app.get("/command/{target}")
def get_command(target: str) -> Command:
    """
    Get a command from the hub.
    
    Args:
        target (str): The target worker to get the command for.
        
    Returns:
        Command: The command for the specified target worker.
    """
    request_ids = list(outbound_commands[target].keys()) if target in outbound_commands else []
    request_id = request_ids[0] if len(request_ids) > 0 else None
    if request_id is None:
        raise HTTPException(status_code=404, detail=f"No pending requests for target: {target}")
    return outbound_commands[target].pop(request_id)

@app.get("/command/clear")
def clear_commands() -> dict:
    """
    Clear the commands in the outbound queue.
    
    Returns:
        dict: A dictionary indicating the status of the clear operation.
    """
    outbound_commands.clear()
    return {"status": "cleared"}

@app.get("/command/clear/{target}")
def clear_commands_target(target: str) -> dict:
    """
    Clear the commands in the outbound queue for a specific target.
    
    Args:
        target (str): The target worker to clear the commands for.
        
    Returns:
        dict: A dictionary indicating the status of the clear operation.
    """
    if target in outbound_commands:
        outbound_commands[target].clear()
        return {"status": "cleared"}
    else:
        raise HTTPException(status_code=404, detail=f"No pending requests for target: {target}")


# Replies
@app.get("/replies")
def replies() -> dict:
    """
    Get the replies in the outbound queue.
    
    Returns:
        dict: A dictionary containing the outbound replies.
    """
    return outbound_replies

@app.post("/reply")
def send_reply(reply: Reply) -> dict:
    """
    Send a command to the hub.
    
    Args:
        reply (Reply): The reply to send.
        
    Returns:
        dict: A dictionary containing the reply ID of the reply.
    """
    reply_id = place_reply(reply)
    return {"reply_id": reply_id}
    
@app.get("/reply/{request_id}")
def get_reply(request_id: str) -> Reply:
    """
    Get a command from the hub.
    
    Args:
        request_id (str): The request ID to get the reply for.
        
    Returns:
        Reply: The reply for the specified request ID.
    """
    if request_id not in outbound_replies:
        raise HTTPException(status_code=404, detail=f"No pending replies to request: {request_id}")
    return outbound_replies[request_id]
 
@app.get("/reply/clear")
def clear_replies() -> dict:
    """
    Clear the replies in the outbound queue.
    
    Returns:
        dict: A dictionary indicating the status of the clear operation.
    """
    outbound_replies.clear()
    return {"status": "cleared"}

@app.get("/reply/clear/{request_id}")
def clear_replies_target(request_id: str) -> dict:
    """
    Clear the replies in the outbound queue for a specific request_id.
    
    Args:
        request_id (str): The request ID to clear the reply for.
        
    Returns:
        dict: A dictionary indicating the status of the clear operation.
    """
    if request_id in outbound_replies:
        outbound_replies.pop(request_id)
        return {"status": "cleared"}
    else:
        raise HTTPException(status_code=404, detail=f"No pending replies to request: {request_id}")



    
# Start the server if not yet running
if __name__ == "__main__":
    start_server()
