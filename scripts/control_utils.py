import threading
from typing import Any

from controllably.core.control import Controller
from controllably.core.interpreter import JSONInterpreter
from controllably.core.implementations.control.fastapi_control import FastAPIUserClient, FastAPIWorkerClient
from controllably.core.implementations.control.socket_control import SocketClient

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

def create_socket_user(host:str, port:int, address:str|None = None) -> tuple[Controller, dict[str,Any]]:
    """
    Create a Socket client instance.
    """
    user = Controller('view', JSONInterpreter())
    if address is not None:
        user.setAddress(address)
    terminate = threading.Event()
    args = [host, port, user]
    kwargs = dict(terminate=terminate, relay=True)
    user_thread = threading.Thread(target=SocketClient.start_client, args=args, kwargs=kwargs, daemon=True)
    user_thread.start()
    return user, {
        'terminate': terminate,
        'user_thread': user_thread
    }
    
def create_socket_worker(host:str, port:int, address:str|None = None) -> tuple[Controller, dict[str,Any]]:
    """
    Create a Socket client instance.
    """
    worker = Controller('model', JSONInterpreter())
    if address is not None:
        worker.setAddress(address)
    worker.start()
    terminate = threading.Event()
    args = [host, port, worker]
    kwargs = dict(terminate=terminate, relay=True)
    worker_thread = threading.Thread(target=SocketClient.start_client, args=args, kwargs=kwargs, daemon=True)
    worker_thread.start()
    return worker, {
        'terminate': terminate,
        'worker_thread': worker_thread
    }
