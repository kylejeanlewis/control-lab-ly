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
import requests
import threading
import time
from typing import Any, Callable
import urllib3

# Local application imports
from ...control import Controller

CONNECTION_ERRORS = (Exception,)#(ConnectionRefusedError, ConnectionError, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError)

class FastAPIWorkerClient:
    def __init__(self, host:str, port:int=8000):
        self.url = f"{host}:{port}"
        self.workers = dict()
    
    def update_registry(self, worker: Controller) -> dict[str, Any]:
        """
        Register a worker with the hub.
        """
        response = requests.post(f"{self.url}/register/model?target={worker.address}")
        registry = response.json()
        print(registry)
        if response.status_code == 200:
            self.workers[worker.address] = worker
            worker.subscribe(lambda reply: FastAPIWorkerClient.send_reply(reply, self.url), 'data', 'HUB')
            worker.subscribe(lambda: json.dumps(FastAPIWorkerClient.get_command(worker.address, self.url)), 'listen', self.url)
            worker.receiveRequest(sender=self.url)
        return registry
    
    @staticmethod
    def get_command(target: str, url: str) -> dict[str, Any]:
        """
        Get a reply from the hub.
        """
        while True:
            try:
                response = requests.get(f"{url}/command/{target}")
            except CONNECTION_ERRORS as e:
                print('Connection Error')
                raise ConnectionError
            if response.status_code == 200:
                break
            time.sleep(0.1)
        command = response.json()
        command['address']['sender'].append('HUB')
        print(command)
        return command

    @staticmethod
    def send_reply(reply: str|bytes, url: str) -> dict[str, Any]:
        """
        Send a reply to the hub.
        """
        reply_json = json.loads(reply)
        try:
            response = requests.post(f"{url}/reply", json=reply_json)
        except CONNECTION_ERRORS as e:
            print('Connection Error')
            raise ConnectionError
        reply_id = response.json()
        print(reply_id)
        return reply_id
    
    @staticmethod
    def create_listen_loop(worker: Controller, sender:str|None = None, terminate:threading.Event|None = None) -> Callable:
        terminate = terminate if terminate is not None else threading.Event()
        def loop():
            while not terminate.is_set():
                try:
                    time.sleep(0.1)
                    worker.receiveRequest(sender=sender)
                except CONNECTION_ERRORS as e:
                    print(f'Connection Error: {worker.address}')
                    break
        return loop


class FastAPIUserClient:
    def __init__(self, host:str, port:int=8000):
        self.url = f"{host}:{port}"
        self.users: dict[str, Controller] = dict()
        self.request_ids: dict[str, Controller] = dict()
    
    def join_hub(self, user: Controller) -> dict[str, Any]:
        """
        Join a hub.
        """
        try:
            response = requests.get(f"{self.url}/registry")
        except CONNECTION_ERRORS as e:
            print('Connection Error')
            raise ConnectionError
        registry = response.json()
        print(registry)
        self.users[user.address] = user
        for worker in registry:
            user.subscribe(lambda command: FastAPIUserClient.send_command(command, self.url, self.request_ids, self.users), 'request', worker)
            user.subscribe(lambda request_id: json.dumps(FastAPIUserClient.get_reply(request_id, self.url)), 'listen', worker)
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
        except CONNECTION_ERRORS as e:
            print('Connection Error')
            raise ConnectionError
        request_id = response.json()
        print(request_id)
        print(command_json)
        user_id = command_json.get('address', {}).get('sender', [None])[0]
        request_ids[request_id['request_id']] = users[user_id]
        return request_id

    @staticmethod
    def get_reply(request_id: str, url: str) -> dict[str, Any]:
        """
        Get a reply from the hub.
        """
        while True:
            try:
                response = requests.get(f"{url}/reply/{request_id}")
            except CONNECTION_ERRORS as e:
                print('Connection Error')
                raise ConnectionError
            if response.status_code == 200:
                break
            time.sleep(0.1)
        reply = response.json()
        print(reply)
        return reply
