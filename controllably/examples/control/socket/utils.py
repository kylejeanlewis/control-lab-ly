# -*- coding: utf-8 -*-
"""
This module provides a socket server and client for managing connections in a distributed system.

Attributes:
    BYTE_SIZE (int): size of the byte.

## Classes:
    `SocketServer`: Class for handling socket server operations.
    `SocketClient`: Class for handling socket client operations.
    
## Functions:
    `create_listen_socket_callback`: Create a callback function for listening to socket data.
    `create_socket_user`: Create a Socket client instance.
    `create_socket_worker`: Create a Socket worker instance.
    `create_socket_hub`: Create a Socket hub instance.

<i>Documentation last updated: 2025-06-11</i>
"""
# Standard library imports
from __future__ import annotations
import logging
import select
import socket
import threading
import time
from typing import Callable, Any

# Local application imports
from ....core.control import Controller
from ....core.interpreter import JSONInterpreter

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)
CustomLevelFilter().setModuleLevel(__name__, logging.INFO)

BYTESIZE = 1024

def create_listen_socket_callback(client_socket: socket.socket, relay: bool) -> Callable[[Any], str]:
    """
    Create a callback function for listening to socket data.
    
    Args:
        client_socket (socket.socket): the client socket
        relay (bool): flag to indicate if the socket is a relay
    
    Returns:
        Callable[[Any], str]: a function that listens for incoming data on the socket
    """
    def listen_socket(**kwargs) -> str:
        """
        Listen for incoming communications
        """
        try:
            data = ''
            while True:
                fragment = client_socket.recv(BYTESIZE).decode("utf-8", "replace").replace('\uFFFD', '')  # Receive data (adjust buffer size if needed)
                data += fragment
                if len(fragment)==0 or len(fragment) < BYTESIZE:
                    break
            if not data:  # Client disconnected
                time.sleep(1)
                raise EOFError
            if data == '[EXIT]':
                client_socket.sendall("[EXIT]".encode("utf-8"))
                raise InterruptedError
            logger.debug(f"Received from client: {data}")
            logger.debug(data)
        except Exception as e:
            logger.error(f"Error handling client: {e}")
            raise e
        return data.encode("utf-8") if relay else data
    return listen_socket

class SocketServer:
    @staticmethod
    def handle_client(
        client_socket: socket.socket, 
        client_addr:str, 
        controller: Controller, 
        client_role:str|None = None, 
        *,
        terminate: threading.Event|None = None
    ):
        """
        Handles communication with a single client
        
        Args:
            client_socket (socket.socket): the client socket
            client_addr (str): the client address
            controller (Controller): the controller
            client_role (str|None, optional): the client role. Defaults to None.
            terminate (threading.Event|None, optional): the termination event. Defaults to None.
        """
        relay = (controller.role == 'relay')
        receive_method = controller.receiveRequest
        callback_type = 'data'
        if relay:
            if client_role not in ('model', 'view'):
                raise ValueError(f"Invalid role: {client_role}")
            callback_type = 'request' if client_role == 'model' else 'data'
            receive_method = controller.relayData if client_role == 'model' else controller.relayRequest
        listen_socket = create_listen_socket_callback(client_socket=client_socket, relay=relay)
        listen_key = client_addr #if relay else 'main'
        controller.callbacks['listen'][listen_key] = listen_socket
        
        terminate = threading.Event() if terminate is None else terminate
        while not terminate.is_set():
            try:
                data = listen_socket()
                receive_method(data, sender=listen_key)
            except EOFError:
                continue
            except (InterruptedError, Exception):
                break
        
        client_socket.close()
        logger.warning(f"Disconnected from client [{client_addr}]")
        
        # Clean up
        controller.unsubscribe(callback_type, client_addr)
        controller.unsubscribe('listen', listen_key)
        controller.data_buffer.get('registration', {}).pop(client_addr, None)
        return

    @staticmethod
    def start_server(host:str, port:int, controller: Controller, *, n_connections:int = 5, terminate: threading.Event|None = None):
        """
        Starts the server
        
        Args:
            host (str): the host
            port (int): the port
            controller (Controller): the controller
            n_connections (int, optional): the number of connections. Defaults to 5.
            terminate (threading.Event|None, optional): the termination event. Defaults to None
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(n_connections)  # Listen for up to 5 connections (default)

        logger.info(f"Server listening on {host}:{port}")
        controller.setAddress(f"{host}:{port}")

        threads = []
        terminate = threading.Event() if terminate is None else terminate
        while not terminate.is_set():
            read_list, _, _ = select.select([server_socket], [], [], 1)
            if server_socket not in read_list:
                time.sleep(0.01)
                continue
            try:
                client_socket, addr = server_socket.accept()
            except TimeoutError:
                time.sleep(0.01)
                continue
            
            # client_socket, addr = server_socket.accept()  # Accept a connection
            logger.info(f"Client connected from {addr}")
            client_addr = f"{addr[0]}:{addr[1]}"
            client_socket.sendall(f"[CONNECTED] {client_addr}".encode("utf-8"))
            handshake = client_socket.recv(BYTESIZE).decode("utf-8", "replace").replace('\uFFFD', '')  # Receive response" ")[1]
            logger.info(handshake)
            if not handshake.startswith("[CONNECTED] "):
                raise ConnectionError(f"Invalid handshake: {handshake}")
            client_role = handshake.replace('[CONNECTED] ','')
            if client_role not in ('model', 'view'):
                raise ValueError(f"Invalid role: {client_role}")
            callback_type = 'request' if client_role == 'model' else 'data'
            controller.subscribe(client_socket.sendall, callback_type, client_addr)
            if client_role == 'view':
                controller.broadcastRegistry(target=[client_addr])

            # Handle each client in a separate thread
            client_thread = threading.Thread(
                target = SocketServer.handle_client, daemon = True,
                args = (client_socket,client_addr,controller,client_role), 
                kwargs = dict(terminate=terminate),
            )
            client_thread.start()
            threads.append(client_thread)
        
        for thread in threads:
            thread.join()
        logger.warning(f"Server [{host}:{port}] stopped.")
        return

class SocketClient:
    @staticmethod
    def start_client(host:str, port:int, controller: Controller, relay:bool = False, *, terminate: threading.Event|None = None):
        """
        Starts the client
        
        Args:
            host (str): the host
            port (int): the port
            controller (Controller): the controller
            relay (bool, optional): flag to indicate relay. Defaults to False.
            terminate (threading.Event|None, optional): the termination event. Defaults to None.
        """
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        match controller.role:
            case 'model':
                callback_type = 'data'
                receive_method = controller.receiveRequest
            case 'view':
                callback_type = 'request'
                receive_method = controller.receiveData
            case _:
                raise ValueError(f"Invalid role: {controller.role}")

        try:
            client_socket.connect((host, port))  # Connect to the server
            host_addr = f"{host}:{port}"
            logger.info(f"Connected to server at {host_addr}")
            time.sleep(1)
            handshake = client_socket.recv(BYTESIZE).decode("utf-8","replace").replace('\uFFFD', '')  # Receive data (adjust buffer size if needed)
            logger.info(handshake)
            if not handshake.startswith("[CONNECTED] "):
                raise ConnectionError(f"Invalid handshake: {handshake}")
            controller.setAddress(handshake.replace('[CONNECTED] ',''))
            client_socket.sendall(f"[CONNECTED] {controller.role}".encode("utf-8"))
            controller.subscribe(client_socket.sendall, callback_type, host_addr, relay=relay)
            listen_socket = create_listen_socket_callback(client_socket=client_socket, relay=relay)
            listen_key = host_addr # if relay else 'main'
            controller.callbacks['listen'][listen_key] = listen_socket
            
            terminate = threading.Event() if terminate is None else terminate
            while not terminate.is_set():
                try:
                    data = listen_socket()
                    receive_method(data, sender=listen_key)
                except EOFError:
                    continue
                except (InterruptedError, Exception):
                    break
            
        except Exception as e:
            logger.error(f"Error connecting to server: {e}")
        else:
            logger.warning(f"Disconnected from server [{host}:{port}]")
        
        # Clean up
        controller.unsubscribe(callback_type, host_addr)
        controller.unsubscribe('listen', listen_key)
        return


def create_socket_user(host:str, port:int, address:str|None = None, relay:bool = True) -> tuple[Controller, dict[str,Any]]:
    """
    Create a Socket client instance.
    
    Args:
        host (str): the host address
        port (int): the port number
        address (str|None, optional): the address to set for the controller. Defaults to None.
        relay (bool, optional): whether to relay messages. Defaults to True.
        
    Returns:
        tuple[Controller, dict[str,Any]]: a tuple containing the controller and a dictionary with termination event and thread information.
    """
    user = Controller('view', JSONInterpreter())
    if address is not None:
        user.setAddress(address)
    terminate = threading.Event()
    args = [host, port, user]
    kwargs = dict(terminate=terminate, relay=relay)
    user_thread = threading.Thread(target=SocketClient.start_client, args=args, kwargs=kwargs, daemon=True)
    user_thread.start()
    time.sleep(3)
    return user, {
        'terminate': terminate,
        'user_thread': user_thread
    }
    
def create_socket_worker(host:str, port:int, address:str|None = None, relay:bool = True) -> tuple[Controller, dict[str,Any]]:
    """
    Create a Socket client instance.
    
    Args:
        host (str): the host address
        port (int): the port number
        address (str|None, optional): the address to set for the controller. Defaults to None.
        relay (bool, optional): whether to relay messages. Defaults to True.
        
    Returns:
        tuple[Controller, dict[str,Any]]: a tuple containing the controller and a dictionary with termination event and thread information.
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
    
    Args:
        host (str): the host address
        port (int): the port number
        address (str|None, optional): the address to set for the controller. Defaults to None.
        relay (bool, optional): whether to relay messages. Defaults to True.
        
    Returns:
        tuple[Controller, dict[str,Any]]: a tuple containing the controller and a dictionary with termination event and thread information.
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
