# -*- coding: utf-8 -*-
import threading
from typing import Any

from ...control import Controller
from ...interpreter import JSONInterpreter
from .fastapi_control import FastAPIUserClient, FastAPIWorkerClient
from .socket_control import SocketClient, SocketServer

def create_fastapi_user(host:str, port:int, address:str|None = None) -> tuple[Controller, dict[str,Any]]:
    """
    Create a FastAPI client instance.
    """
    user = Controller('view', JSONInterpreter())
    if address is not None:
        user.setAddress(address)
    client = FastAPIUserClient(host, port)
    client.join_hub(user)
    return user, {
        'client': client
    }
    
def create_fastapi_worker(host:str, port:int, address:str|None = None) -> tuple[Controller, dict[str,Any]]:
    """
    Create a FastAPI client instance.
    """
    worker = Controller('model', JSONInterpreter())
    if address is not None:
        worker.setAddress(address)
    worker.start()
    client = FastAPIWorkerClient(host, port)
    terminate = threading.Event()
    client.terminate_events[worker.address] = terminate
    client.update_registry(worker, terminate=terminate)
    pause = threading.Event()
    client.pause_events[worker.address] = pause
    worker_thread = threading.Thread(target=client.create_listen_loop(worker, sender=client.url, terminate=terminate, pause=pause), daemon=True)
    worker_thread.start()
    return worker, {
        'terminate': terminate,
        'worker_thread': worker_thread,
        'client': client
    }

def create_socket_user(host:str, port:int, address:str|None = None, relay:bool = True) -> tuple[Controller, dict[str,Any]]:
    """
    Create a Socket client instance.
    """
    user = Controller('view', JSONInterpreter())
    if address is not None:
        user.setAddress(address)
    terminate = threading.Event()
    args = [host, port, user]
    kwargs = dict(terminate=terminate, relay=relay)
    user_thread = threading.Thread(target=SocketClient.start_client, args=args, kwargs=kwargs, daemon=True)
    user_thread.start()
    return user, {
        'terminate': terminate,
        'user_thread': user_thread
    }
    
def create_socket_worker(host:str, port:int, address:str|None = None, relay:bool = True) -> tuple[Controller, dict[str,Any]]:
    """
    Create a Socket client instance.
    """
    worker = Controller('model', JSONInterpreter())
    if address is not None:
        worker.setAddress(address)
    worker.start()
    terminate = threading.Event()
    args = [host, port, worker]
    kwargs = dict(terminate=terminate)
    target_func = SocketServer.start_server
    if relay:
        kwargs['relay'] = relay
        target_func = SocketClient.start_client
    worker_thread = threading.Thread(target=target_func, args=args, kwargs=kwargs, daemon=True)
    worker_thread.start()
    return worker, {
        'terminate': terminate,
        'worker_thread': worker_thread
    }

def create_socket_hub(host:str, port:int, address:str|None = None, relay:bool = True) -> tuple[Controller, dict[str,Any]]:
    """
    Create a Socket client instance.
    """
    hub = Controller('relay', JSONInterpreter())
    if address is not None:
        hub.setAddress(address)
    terminate = threading.Event()
    args = [host, port, hub]
    kwargs = dict(terminate=terminate)
    hub_thread = threading.Thread(target=SocketServer.start_server, args=args, kwargs=kwargs, daemon=True)
    hub_thread.start()
    return hub, {
        'terminate': terminate,
        'hub_thread': hub_thread
    }
