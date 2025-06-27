# -*- coding: utf-8 -*-
"""
This module provides a FastAPI server for managing commands and replies in a distributed system.

Attributes:
    CONNECTION_ERRORS (tuple): Tuple of exceptions that indicate connection errors.

## Classes:
    `FastAPIWorkerClient`: Client for managing worker connections to the FastAPI server.
    `FastAPIUserClient`: Client for managing user connections to the FastAPI server.
    
## Functions:
    `create_fastapi_user`: Create a FastAPI client instance for user interaction.
    `create_fastapi_worker`: Create a FastAPI client instance for worker interaction.

<i>Documentation last updated: 2025-06-11</i>
"""
# Standard library imports
from __future__ import annotations
import json
import logging
import requests
import threading
import time
from typing import Any, Callable
import urllib3

# Local application imports
from ....core.control import Controller
from ....core.interpreter import JSONInterpreter

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)
CustomLevelFilter().setModuleLevel(__name__, logging.INFO)

CONNECTION_ERRORS = (ConnectionRefusedError, ConnectionError, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError)

class FastAPIWorkerClient:
    """ 
    FastAPIWorkerClient is a singleton class that manages worker connections to a FastAPI server.
    It allows workers to register with the hub, send commands, and receive replies from the hub.
    It maintains a registry of workers and their associated terminate and pause events, allowing for
    communication between workers and the hub.
    
    ### Constructor:
        `host` (str): The host address for the FastAPI server.
        `port` (int): The port number for the FastAPI server, defaults to 8000.
        
    ### Attributes:
        `url` (str): The URL of the FastAPI server.
        `workers` (dict[str, Controller]): A dictionary mapping worker addresses to worker controllers.
        `terminate_events` (dict[str, threading.Event]): A dictionary mapping worker addresses to terminate events.
        `pause_events` (dict[str, threading.Event]): A dictionary mapping worker addresses to pause events.
        
    ### Methods:
        `update_registry`: Register a worker with the hub.
        `get_command`: Get a command from the hub for a specific worker.
        `send_reply`: Send a reply to the hub.
        `create_listen_loop`: Create a loop for the worker to listen for commands from the hub.
    """
    
    instances: dict[str, FastAPIWorkerClient] = dict()
    def __new__(cls, host:str, port:int=8000):
        url = f"{host}:{port}"
        if url in cls.instances:
            return cls.instances[url]
        instance = super().__new__(cls)
        instance.workers = dict()
        instance.terminate_events = dict()
        instance.pause_events = dict()
        cls.instances[url] = instance
        return instance
    
    def __init__(self, host:str, port:int=8000):
        """
        Initialize the FastAPIWorkerClient with the host and port.
        
        Args:
            host (str): The host address for the FastAPI server.
            port (int): The port number for the FastAPI server, defaults to 8000.
        """
        self.url = f"{host}:{port}"
        self.workers: dict[str, Controller] = self.workers
        self.terminate_events: dict[str, threading.Event] = self.terminate_events
        self.pause_events: dict[str, threading.Event] = self.pause_events
        return
    
    def update_registry(self, worker: Controller, terminate: threading.Event|None = None) -> dict[str, Any]:
        """
        Register a worker with the hub.
        
        Args:
            worker (Controller): The worker controller to register.
            terminate (threading.Event|None): An event to signal termination, defaults to None.
            
        Returns:
            dict[str, Any]: The registry of the hub.
        """
        response = requests.post(f"{self.url}/register/model?target={worker.address}")
        registry = response.json()
        logger.debug(registry)
        if response.status_code == 200:
            if worker.address in self.pause_events:
                self.pause_events[worker.address].set()
            self.workers[worker.address] = worker
            terminate = terminate if terminate is not None else threading.Event()
            worker.events[self.url] = terminate
            worker.subscribe(lambda reply: FastAPIWorkerClient.send_reply(reply, self.url), 'data', 'HUB')
            worker.subscribe(lambda: json.dumps(FastAPIWorkerClient.get_command(worker.address, self.url, terminate)), 'listen', self.url)
            if worker.address in self.pause_events:
                self.pause_events[worker.address].clear()
        return registry
    
    @staticmethod
    def get_command(target: str, url: str, terminate: threading.Event|None = None) -> dict[str, Any]:
        """
        Get a reply from the hub.
        
        Args:
            target (str): The address of the target worker.
            url (str): The URL of the FastAPI server.
            terminate (threading.Event|None): An event to signal termination, defaults to None.
            
        Returns:
            dict[str, Any]: The command from the hub.
        """
        terminate = terminate if terminate is not None else threading.Event()
        while not terminate.is_set():
            try:
                response = requests.get(f"{url}/command/{target}")
            except Exception:
                logger.error('Connection Error')
                raise ConnectionError
            if response.status_code == 200:
                break
            time.sleep(0.1)
        if terminate.is_set():
            raise InterruptedError
        command = response.json()
        command['address']['sender'].append('HUB')
        logger.debug(command)
        return command

    @staticmethod
    def send_reply(reply: str|bytes, url: str) -> dict[str, Any]:
        """
        Send a reply to the hub.
        
        Args:
            reply (str|bytes): The reply to send.
            url (str): The URL of the FastAPI server.
            
        Returns:
            dict[str, Any]: The reply ID returned by the hub.
        """
        reply_json = json.loads(reply)
        try:
            response = requests.post(f"{url}/reply", json=reply_json)
        except Exception:
            logger.error('Connection Error')
            raise ConnectionError
        reply_id = response.json()
        logger.debug(reply_id)
        return reply_id
    
    @staticmethod
    def create_listen_loop(
        worker: Controller, 
        sender: str|None = None, 
        terminate: threading.Event|None = None,
        pause: threading.Event|None = None
    ) -> Callable:
        """
        Create a loop for the worker to listen for commands from the hub.
        
        Args:
            worker (Controller): The worker controller to listen for commands.
            sender (str|None): The address of the sender, defaults to None.
            terminate (threading.Event|None): An event to signal termination, defaults to None.
            pause (threading.Event|None): An event to signal pause, defaults to None.
            
        Returns:
            Callable: A function that runs the loop for the worker.
        """
        terminate = terminate if terminate is not None else threading.Event()
        pause = pause if pause is not None else threading.Event()
        def loop():
            while not terminate.is_set():
                if pause.is_set():
                    time.sleep(0.1)
                    logger.debug('PAUSED')
                    continue
                try:
                    time.sleep(0.1)
                    worker.receiveRequest(sender=sender)
                except CONNECTION_ERRORS:
                    logger.error(f'Connection Error: {worker.address}')
                    break
                except InterruptedError:
                    logger.error(f'Interrupted: {worker.address}')
                    break
            if terminate.is_set():
                logger.debug(f'Interrupted: {worker.address}')
            return
        return loop

class FastAPIUserClient:
    """ 
    FastAPIUserClient is a singleton class that manages user connections to a FastAPI server.
    It allows users to join a hub, send commands, and receive replies from the hub.
    It maintains a registry of users and their associated request IDs, allowing for communication
    between users and the hub.
    
    ### Constructor:
        `host` (str): The host address for the FastAPI server.
        `port` (int): The port number for the FastAPI server, defaults to 8000.
    
    ### Attributes:
        `url` (str): The URL of the FastAPI server.
        `users` (dict[str, Controller]): A dictionary mapping user addresses to user controllers.
        `request_ids` (dict[str, Controller]): A dictionary mapping request IDs to user controllers.
    
    ### Methods:
        `join_hub`: Join a hub with the user controller.
        `send_command`: Send a command to the hub.
        `get_reply`: Get a reply from the hub based on a request ID.
    """
    
    instances: dict[str, FastAPIUserClient] = dict()
    def __new__(cls, host:str, port:int=8000):
        url = f"{host}:{port}"
        if url in cls.instances:
            return cls.instances[url]
        instance = super().__new__(cls)
        instance.users = dict()
        instance.request_ids = dict()
        cls.instances[url] = instance
        return instance
    
    def __init__(self, host:str, port:int=8000):
        """
        Initialize the FastAPIUserClient with the host and port.
        
        Args:
            host (str): The host address for the FastAPI server.
            port (int): The port number for the FastAPI server, defaults to 8000.
        """
        self.url = f"{host}:{port}"
        self.users: dict[str, Controller] = self.users
        self.request_ids: dict[str, Controller] = self.request_ids
        return
    
    def join_hub(self, user: Controller) -> dict[str, Any]:
        """
        Join a hub.
        
        Args:
            user (Controller): The user controller to join the hub.
            
        Returns:
            dict[str, Any]: The registry of the hub.
        """
        try:
            response = requests.get(f"{self.url}/registry")
        except Exception:
            logger.error('Connection Error')
            raise ConnectionError
        registry = response.json()
        logger.debug(registry)
        self.users[user.address] = user
        for worker_address in registry:
            terminate = threading.Event()
            user.events[worker_address] = terminate
            user.subscribe(lambda command: FastAPIUserClient.send_command(command, self.url, self.request_ids, self.users), 'request', worker_address)
            user.subscribe(lambda request_id: json.dumps(FastAPIUserClient.get_reply(request_id, self.url, terminate)), 'listen', worker_address)
        user.data_buffer['registration'] = {k:{'data':v} for k,v in registry.items()}
        return registry

    @staticmethod
    def send_command(command:str|bytes, url: str, request_ids: dict[str, Controller], users: dict[str, Controller]) -> dict[str, Any]:
        """
        Send a command to the hub.
        
        Args:
            command (str|bytes): The command to send.
            url (str): The URL of the FastAPI server.
            request_ids (dict[str, Controller]): A dictionary mapping request IDs to users.
            users (dict[str, Controller]): A dictionary mapping user addresses to user controllers.
            
        Returns:
            dict[str, Any]: The request ID returned by the hub.
        """
        command_json = json.loads(command)
        try:
            response = requests.post(f"{url}/command", json=command_json)
        except Exception:
            logger.error('Connection Error')
            raise ConnectionError
        request_id = response.json()
        user_id = command_json.get('address', {}).get('sender', [None])[0]
        request_ids[request_id['request_id']] = users[user_id]
        return request_id

    @staticmethod
    def get_reply(request_id: str, url: str, terminate: threading.Event|None = None) -> dict[str, Any]:
        """
        Get a reply from the hub.
        
        Args:
            request_id (str): The ID of the request to get the reply for.
            url (str): The URL of the FastAPI server.
            terminate (threading.Event|None): An event to signal termination, defaults to None.
            
        Returns:
            dict[str, Any]: The reply from the hub.
        """
        terminate = terminate if terminate is not None else threading.Event()
        while not terminate.is_set():
            try:
                response = requests.get(f"{url}/reply/{request_id}")
            except Exception:
                logger.error('Connection Error')
                raise ConnectionError
            if response.status_code == 200:
                break
            time.sleep(0.1)
        if terminate.is_set():
            raise InterruptedError
        reply = response.json()
        logger.debug(reply)
        return reply


def create_fastapi_user(host:str, port:int, address:str|None = None) -> tuple[Controller, dict[str,Any]]:
    """
    Create a FastAPI client instance.
    
    Args:
        host (str): The host address for the FastAPI server.
        port (int): The port number for the FastAPI server.
        address (str|None): The address of the user, defaults to None.
        
    Returns:
        tuple[Controller, dict[str, Any]]: A tuple containing the Controller instance and a dictionary with the client.
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
    
    Args:
        host (str): The host address for the FastAPI server.
        port (int): The port number for the FastAPI server.
        address (str|None): The address of the worker, defaults to None.
        
    Returns:
        tuple[Controller, dict[str, Any]]: A tuple containing the Controller instance and a dictionary with the client.
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
