from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

from controllably.core.control import Controller
from controllably.core.interpreter import JSONInterpreter

hub = Controller('relay', JSONInterpreter())
hub.setAddress('HUB')

app = FastAPI()

inbound_replies = dict()
outbound_replies = dict()
inbound_commands = dict()
outbound_commands = dict()

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
    object_id: str
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
    



@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/view")
def register_view():
    """
    Register the view with the hub.
    """
    return hub.getMethods()

@app.post("/model")
def register_model(target: str):
    """
    Register the model with the hub.
    """
    hub.subscribe(lambda command: outbound_commands[])
    return {"model": model}





@app.post("/command")
def send_command(command: Command):
    """
    Send a command to the hub.
    """
    for target in command.address.target:
        if target not in inbound_commands:
            inbound_commands[target] = dict()
        inbound_commands[target][command.request_id] = command
    
@app.get("/command/{target}")
def get_command(target: str):
    """
    Get a command from the hub.
    """
    request_ids = list(inbound_commands[target].keys()) if target in inbound_commands else []
    request_id = request_ids[0] if len(request_ids) > 0 else None
    if request_id is None:
        raise HTTPException(status_code=404, detail="No pending requests")
    return inbound_commands[target].pop(request_id)

@app.post("/reply")
def send_reply(reply: Reply):
    """
    Send a command to the hub.
    """
    inbound_replies[reply.request_id] = reply
    
@app.get("/reply/{request_id}")
def get_reply(request_id: str):
    """
    Get a command from the hub.
    """
    if request_id not in inbound_replies:
        raise HTTPException(status_code=404, detail="No pending replies")
    return inbound_replies[request_id]
 