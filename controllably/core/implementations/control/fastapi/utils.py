# -*- coding: utf-8 -*-
"""
This module provides classes for a simple remote procedure call (RPC) framework.

Attributes:
    BYTE_SIZE (int): size of the byte.
    
## Functions:
    `handle_client`: handle a client connection.
    `start_server`: start a server.
    `start_client`: start a client.

<i>Documentation last updated: 2025-02-22</i>
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
from ....control import Controller
from ....interpreter import JSONInterpreter

CONNECTION_ERRORS = (ConnectionRefusedError, ConnectionError, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError)

logger = logging.getLogger(__name__)

class FastAPIWorkerClient:
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
        self.url = f"{host}:{port}"
        self.workers: dict[str, Controller] = self.workers
        self.terminate_events: dict[str, threading.Event] = self.terminate_events
        self.pause_events: dict[str, threading.Event] = self.pause_events
        return
    
    def update_registry(self, worker: Controller, terminate: threading.Event|None = None) -> dict[str, Any]:
        """
        Register a worker with the hub.
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
        """
        terminate = terminate if terminate is not None else threading.Event()
        while not terminate.is_set():
            try:
                response = requests.get(f"{url}/command/{target}")
            except Exception as e:
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
        """
        reply_json = json.loads(reply)
        try:
            response = requests.post(f"{url}/reply", json=reply_json)
        except Exception as e:
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
                except CONNECTION_ERRORS as e:
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
        self.url = f"{host}:{port}"
        self.users: dict[str, Controller] = self.users
        self.request_ids: dict[str, Controller] = self.request_ids
        return
    
    def join_hub(self, user: Controller) -> dict[str, Any]:
        """
        Join a hub.
        """
        try:
            response = requests.get(f"{self.url}/registry")
        except Exception as e:
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
        """
        command_json = json.loads(command)
        try:
            response = requests.post(f"{url}/command", json=command_json)
        except Exception as e:
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
        """
        terminate = terminate if terminate is not None else threading.Event()
        while not terminate.is_set():
            try:
                response = requests.get(f"{url}/reply/{request_id}")
            except Exception as e:
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
