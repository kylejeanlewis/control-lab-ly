# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
import inspect
import logging
import queue
import socket
import threading
import time
from typing import Callable, Mapping, Any, Iterable
import uuid

# Local application imports
from .interpreter import Interpreter, Message

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

@dataclass
class ClassMethods:
    name: str
    methods: dict[str, dict[str, str]]

class TwoTierQueue:
    def __init__(self):
        self.normal_queue = queue.Queue()
        self.high_priority_queue = queue.PriorityQueue()
        self.last_used_queue_normal = True
        self.priority_counter = 0
        return

    def qsize(self):
        return self.normal_queue.qsize() + self.high_priority_queue.qsize()
    
    def empty(self):
        return self.normal_queue.empty() and self.high_priority_queue.empty()
    
    def full(self):
        return self.normal_queue.full() or self.high_priority_queue.full()
    
    def put(self, item: Any, block: bool = True, timeout: float|None = None, *, priority: bool = False, rank: int|None = None):
        if priority or rank is not None:
            self.priority_counter += 1
            rank = self.priority_counter if rank is None else rank
            self.put_priority(item, rank, block=block, timeout=timeout)
        else:
            self.put_queue(item, block=block, timeout=timeout)
        return
    
    def put_nowait(self, item: Any, *, priority: bool = False, rank: int = None):
        return self.put(item, block=False, priority=priority, rank=rank)
    
    def get(self, block: bool = True, timeout: float|None = None) -> Any:
        item = None
        start_time = time.perf_counter()
        while True:
            if not self.high_priority_queue.empty():
                _, item = self.high_priority_queue.get(block=False)
                self.last_used_queue_normal = False
                break
            elif not self.normal_queue.empty():
                item = self.normal_queue.get(block=False)
                self.last_used_queue_normal = True
                break
            if not block:
                break
            if timeout is not None and (time.perf_counter()-start_time) >= timeout:
                break
        return item
    
    def get_nowait(self) -> Any:
        return self.get(block=False)
    
    def task_done(self):
        return self.normal_queue.task_done() if self.last_used_queue_normal else self.high_priority_queue.task_done()
    
    def join(self):
        self.normal_queue.join()
        self.high_priority_queue.join()
        return
    
    def put_first(self, item: Any):
        self.put_priority(item, rank=0)
        return
    
    def put_priority(self, item: Any, rank: int, block: bool = True, timeout: float|None = None):
        self.high_priority_queue.put((rank, item), block=block, timeout=timeout)
        return
    
    def put_queue(self, item: Any, block: bool = True, timeout: float|None = None):
        self.normal_queue.put(item, block=block, timeout=timeout)
        return

    def reset(self):
        self.normal_queue = queue.Queue()
        self.high_priority_queue = queue.PriorityQueue()
        self.last_used_queue_normal = True
        self.priority_counter = 0
        return


class Proxy:
    def __new__(cls, prime:Callable, object_id:str|None = None):
        new_class = cls.factory(prime, object_id)
        return super(Proxy,cls).__new__(new_class)
    
    def __init__(self, prime:Callable, object_id:str|None = None):
        self.prime = prime
        self.object_id = object_id or id(prime)
        self.controller: Controller|None = None
        self.remote = False
        return
    
    @classmethod
    def factory(cls, prime:Callable, object_id:str|None = None):
        name = prime.__name__ if inspect.isclass(prime) else prime.__class__.__name__
        object_id = object_id or id(prime)
        attrs = {attr:cls.makeEmitter(getattr(prime,attr)) for attr in dir(prime) if callable(getattr(prime,attr)) and (attr not in dir(cls))}
        attrs.update({"_channel_class":prime})
        new_class = type(f"{name}_Proxy-{object_id}", (cls,), attrs)
        return new_class
    
    @staticmethod
    def makeEmitter(method):
        def emitter(self, *args, **kwargs):
            if not self.remote and not inspect.isclass(self.prime):
                prime_method = getattr(self.prime, method.__name__)
                return prime_method(*args, **kwargs)
            
            assert isinstance(self.controller, Controller), 'No controller is bound to this Proxy.'
            command = dict(
                object_id = self.object_id,
                method = method.__name__,
                args = args,
                kwargs = kwargs
            )
            return self.controller.transmitRequest(command)
        emitter.__name__ = method.__name__
        emitter.__doc__ = method.__doc__
        emitter.__signature__ = inspect.signature(method)
        return emitter
    
    def bindController(self, controller: Controller):
        self.controller = controller
        return
    
    def releaseController(self) -> Controller:
        controller = self.controller
        self.controller = None
        return controller


class Controller:
    def __init__(self, role: str, interpreter: Interpreter):
        assert role in ('model', 'view', 'both', 'relay'), f"Invalid role: {role}"
        assert isinstance(interpreter, Interpreter), f"Invalid interpreter: {interpreter}"
        self.role = role
        self.interpreter = interpreter
        self.address = None
        
        self.relays = []
        self.callbacks: dict[str, dict[str,Callable]] = dict(request={}, data={})
        self.command_queue = TwoTierQueue()
        self.data_buffer = dict()
        self.objects = {}
        self.object_methods: dict[str, ClassMethods] = dict()
        
        self.execution_event = threading.Event()
        self.threads = {}
        
        if self.role in ('model', 'both'):
            # self.register(self)
            pass
        return
    
    # Model side
    def receiveRequest(self, request: Message):
        assert self.role in ('model', 'both'), "Only the model can receive requests"
        command = self.interpreter.decodeRequest(request)
        sender = command.get('address', {}).get('sender', [])
        if len(sender):
            logger.info(f"[{self.address or str(id(self))}] Received request from {sender}")
        priority = command.get("priority", False)
        rank = command.get("rank", None)
        self.command_queue.put(command, priority=priority, rank=rank)
        logger.debug('Received request')
        return
    
    def transmitData(self, 
        data: Any, 
        *, 
        metadata: Mapping[str, Any]|None = None, 
        status: Mapping[str, Any]|None = None
    ):
        assert self.role in ('model', 'both'), "Only the model can transmit data"
        response = dict()
        status = status or dict(status='completed')
        response.update(dict(data=data))
        response.update(status)
        response.update(metadata)
        package = self.interpreter.encodeData(response)
        logger.debug('Transmitted data')
        self.relayData(package)
        return
    
    def register(self, new_object: Callable, object_id: str|None = None):
        assert self.role in ('model', 'both'), "Only the model can register object"
        key =  str(id(new_object)) if object_id is None else object_id
        if key in self.object_methods:
            logger.warning(f"{new_object.__class__}_{key} already registered.")
            return False
        self.object_methods[key] = self.extractMethods(new_object)
        self.objects[key] = new_object
        return
    
    def unregister(self, object_id:str|None = None, old_object: Callable|None = None) -> bool:
        assert self.role in ('model', 'both'), "Only the model can unregister object"
        assert (object_id is None) != (old_object is None), "Either object_id or object must be provided"
        key = str(id(old_object)) if object_id is None else object_id
        success = False
        try:
            self.object_methods.pop(key) 
            self.objects.pop(key)
            success = True
        except KeyError:
            if old_object is not None:
                logger.warning(f"Object not found: {old_object.__class__} [{key}]")
            else:
                logger.warning(f"Object not found: {key}")
        return success
    
    @staticmethod
    def extractMethods(new_object: Callable) -> ClassMethods:
        methods = {}
        for method in dir(new_object):
            if method.startswith('_'):
                continue
            is_method = False
            if inspect.ismethod(getattr(new_object, method)):
                is_method = True
            elif isinstance(inspect.getattr_static(new_object, method), staticmethod):
                is_method = True
            elif isinstance(inspect.getattr_static(new_object, method), classmethod):
                is_method = True
            if not is_method:
                continue
            
            methods[method] = dict()
            signature = inspect.signature(getattr(new_object, method))
            parameters = dict()
            for name, param in signature.parameters.items():
                if name == 'self':
                    continue
                annotation = str(param.annotation) if param.annotation!=inspect.Parameter.empty else ''
                default = param.default if param.default!=inspect.Parameter.empty else None
                if param.kind in [inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.VAR_KEYWORD]:
                    if 'kwargs' not in parameters:
                        parameters['kwargs'] = []
                    parameters['kwargs'].append((name, default, annotation))
                else:
                    if 'args' not in parameters:
                        parameters['args'] = []
                    parameters['args'].append((name, default, annotation))
            if len(parameters):
                methods[method]['parameters'] = parameters
            returns = str(signature.return_annotation) if signature.return_annotation!=inspect.Signature.empty else {}
            if len(returns):
                methods[method]['returns'] = returns
        
        return ClassMethods(
            name = new_object.__class__.__name__,
            methods = methods
        )
    
    def extractMetadata(self, command: Mapping[str, Any]) -> Mapping[str, Any]:
        target = command.get('address', {}).get('sender', [])
        target.extend(self.relays)
        sender = [self.address or str(id(self))]
        return dict(
            address = dict(sender=sender, target=target),
            request_id = command.get('request_id', uuid.uuid4().hex),
            priority = command.get('priority', False),
            rank = command.get('rank', None)
        )
    
    def exposeMethods(self):
        assert self.role in ('model', 'both'), "Only the model can expose methods"
        return {k:v.__dict__ for k,v in self.object_methods.items()}
    
    def start(self):
        assert self.role in ('model', 'both'), "Only the model can start execution loop"
        self.execution_event.set()
        self.threads['execution'] = threading.Thread(target=self._loop_execution, daemon=True)
        logger.info("Starting execution loop")
        for thread in self.threads.values():
            thread.start()
        return
    
    def stop(self):
        assert self.role in ('model', 'both'), "Only the model can stop execution loop"
        self.execution_event.clear()
        logger.info("Stopping execution loop")
        for thread in self.threads.values():
            thread.join()
        return
   
    def executeCommand(self, command: Mapping[str, Any]) -> tuple[Any, dict[str, Any]]:
        assert self.role in ('model', 'both'), "Only the model can execute commands"
        object_id = command.get('object_id', '')
        method_name = command.get('method', '')
        
        # Implement the command execution logic here
        if object_id not in self.objects:
            if method_name in ('exposeMethods',):
                return self.exposeMethods(), dict(status='completed')
            elif method_name in ('getattr', 'setattr', 'delattr'):
                args = command.get('args', [])
                kwargs = command.get('kwargs', {})
                object_id = args[0] if len(args) else kwargs.get('object_id', '')
                name = args[1] if len(args) > 1 else kwargs.get('name', '')
                this_object = self.objects.get(object_id)
                
                if this_object is None:
                    logger.error(f"Object not found: {object_id}")
                    return None, dict(status='error', message='Object not found')
                try:
                    attr = getattr(this_object, name)
                except AttributeError:
                    logger.error(f"Attribute not found: {name}")
                    return None, dict(status='error', message='Attribute not found')
                
                if method_name == 'getattr':
                    return attr, dict(status='completed')
                elif method_name == 'setattr':
                    setattr(this_object, name, args[2]), dict(status='completed')
                    return None, dict(status='completed')
                elif method_name == 'delattr':
                    delattr(this_object, name)
                    return None, dict(status='completed')
            else:
                logger.error(f"Object not found: {object_id}")
                return None, dict(status='error', message='Object not found')
        
        this_object = self.objects[object_id]
        try:
            method: Callable = getattr(this_object, method_name)
        except AttributeError:
            logger.error(f"Method not found: {method_name}")
            return None, dict(status='error', message='Method not found')
        
        logger.info(f"Executing command: {command}")
        args = command.get('args', [])
        kwargs = command.get('kwargs', {})
        try:
            out = method(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return None, dict(status='error', message=str(e))
        logger.info(f"Completed command: {command}")
        return out, dict(status='completed')
    
    def _loop_execution(self):
        assert self.role in ('model', 'both'), "Only the model can execute commands"
        while self.execution_event.is_set():
            try:
                command = self.command_queue.get(timeout=5)
                if command is not None:
                    metadata = self.extractMetadata(command)
                    data,status = self.executeCommand(command)
                    logger.debug(status)
                    self.transmitData(data, metadata=metadata, status=status)
                    self.command_queue.task_done()
            except queue.Empty:
                time.sleep(0.1)
                pass
            except KeyboardInterrupt:
                self.execution_event.clear()
                break
        time.sleep(1)
        
        while self.command_queue.qsize() > 0:
            try:
                command = self.command_queue.get(timeout=1)
                if command is not None:
                    metadata = self.extractMetadata(command)
                    data,status = self.executeCommand(command)
                    self.transmitData(data, metadata=metadata, status=status)
                    self.command_queue.task_done()
            except queue.Empty:
                break
            except KeyboardInterrupt:
                break
        self.command_queue.join()
        return
    
    # View side
    def transmitRequest(self, 
        command: Mapping[str, Any], 
        target: Iterable[int]|None = None, 
        *, 
        private:bool = True, 
        priority: bool = False, 
        rank: int = None
    ) -> str:
        assert self.role in ('view', 'both'), "Only the view can transmit requests"
        sender = [self.address or str(id(self))] if private else []
        target = target if target is not None else []
        target.extend(self.relays)
        request_id = uuid.uuid4().hex
        command['address'] = dict(sender=sender, target=target)
        command['request_id'] = request_id
        command['priority'] = priority
        command['rank'] = rank
        request = self.interpreter.encodeRequest(command)
        logger.debug('Transmitted request')
        self.relayRequest(request)
        return request_id
    
    def receiveData(self, package: Message):
        assert self.role in ('view', 'both'), "Only the view can receive data"
        data = self.interpreter.decodeData(package)
        sender = data.get('address', {}).get('sender', [])
        request_id = data.get('request_id', uuid.uuid4().hex)
        if len(sender):
            logger.info(f"[{self.address or str(id(self))}] Received data from {sender}")
        self.data_buffer[request_id] = data
        logger.debug('Received data')
        return
    
    def getMethods(self, target: Iterable[int]|None = None, *, private: bool = True):
        assert self.role in ('view', 'both'), "Only the view can get methods"
        command = dict(method='exposeMethods')
        request_id = self.transmitRequest(command, target, private=private)
        while request_id not in self.data_buffer:
            time.sleep(0.1)
            pass
        response = self.data_buffer.pop(request_id)
        methods = response.get('data', {})
        return methods
    
    # Controller side
    def relay(self, message: Message, callback_type:str, addresses: Iterable[int]|None = None):
        assert callback_type in self.callbacks, f"Invalid callback type: {callback_type}"
        self_address = self.address or str(id(self))
        if self_address in addresses and self.role == 'relay':
            addresses.remove(self_address)
        addresses = addresses or self.callbacks[callback_type].keys()
        for address in addresses:
            if address not in self.callbacks[callback_type]:
                if len(self.relays) == 0:
                    logger.warning(f"Callback not found for address: {address}")
                continue
            callback = self.callbacks[callback_type][address]
            callback(message)
        time.sleep(1)
        return
    
    def relayRequest(self, request: Message):
        content = self.interpreter.decodeRequest(request)
        addresses = content.get('address', {}).get('target', [])
        self.relay(request, 'request', addresses=addresses)
        if self.role == 'relay':
            logger.debug('Relayed request')
        return
    
    def relayData(self, package: Message):
        content = self.interpreter.decodeData(package)
        addresses = content.get('address', {}).get('target', [])
        self.relay(package, 'data', addresses=addresses)
        if self.role == 'relay':
            logger.debug('Relayed data')
        return
    
    def subscribe(self, 
        callback: Callable, 
        callback_type: str, 
        address: int|str|None = None, 
        *, 
        relay: bool = False
    ):
        assert callback_type in self.callbacks, f"Invalid callback type: {callback_type}"
        assert isinstance(callback, Callable), f"Invalid callback: {callback}"
        key = address
        if key is None:
            key = id(callback)
            if '__self__' in dir(callback):
                key = id(callback.__self__)
        key = str(key)
        if relay:
            self.relays.append(key)
        if key in self.callbacks[callback_type]:
            logger.warning(f"{callback} already subscribed to {callback_type}")
            return
        self.callbacks[callback_type][key] = callback
        return
    
    def unsubscribe(self, callback: Callable, callback_type: str):
        assert callback_type in self.callbacks, f"Invalid callback type: {callback_type}"
        assert isinstance(callback, Callable), f"Invalid callback: {callback}"
        key = id(callback.__self__) if '__self__' in dir(callback) else id(callback)
        key = str(key)
        _callback = self.callbacks[callback_type].pop(key, None)
        if _callback is None:
            logger.warning(f"{callback} was not subscribed to {callback_type}")
            return
        if key in self.relays:
            self.relays.remove(key)
        return
    
    def setAddress(self, address: int|str):
        assert isinstance(address, (int,str)), f"Invalid address: {address}"
        self.address = address
        return


# --- Socket Communication Implementation ---
def handle_client(client_socket: socket.socket, client_addr:str, controller: Controller, client_role:str|None = None):
    """Handles communication with a single client."""
    relay = (controller.role == 'relay')
    receive_method = controller.receiveRequest
    if relay:
        match client_role:
            case 'model':  # (i.e. client is a model)
                receive_method = controller.relayData
            case 'view':
                receive_method = controller.relayRequest
            case _:
                raise ValueError(f"Invalid role: {client_role}")
    while True:
        try:
            data = client_socket.recv(4096).decode("utf-8")  # Receive data (adjust buffer size if needed)
            if not data:  # Client disconnected
                time.sleep(1)
                continue
            if data == '[EXIT]':
                break
            logger.debug(f"Received from client: {data}")
            print(data)
            data = data.encode("utf-8") if relay else data
            receive_method(data)
                
        except Exception as e:
            print(f"Error handling client: {e}")
            break

    print(f"Client [{client_addr}] disconnected.")
    client_socket.close()
    return


def start_server(host:str, port:int, controller: Controller):
    """Starts the server."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)  # Listen for up to 5 connections

    print(f"Server listening on {host}:{port}")
    controller.setAddress(f"{host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()  # Accept a connection
        print(f"Client connected from {addr}")
        client_addr = f"{addr[0]}:{addr[1]}"
        client_socket.sendall(f"[CONNECTED] {client_addr}".encode("utf-8"))
        handshake = client_socket.recv(1024).decode("utf-8")  # Receive response" ")[1]
        print(handshake)
        if not handshake.startswith("[CONNECTED] "):
            raise ConnectionError(f"Invalid handshake: {handshake}")
        client_role = handshake.replace('[CONNECTED] ','')
        match client_role:
            case 'model':
                callback_type = 'request'
            case 'view':
                callback_type = 'data'
            case _:
                raise ValueError(f"Invalid role: {client_role}")
        controller.subscribe(client_socket.sendall, callback_type, client_addr)

        # Handle each client in a separate thread
        client_thread = threading.Thread(target=handle_client, args=(client_socket,client_addr,controller,client_role))
        client_thread.start()
    return


def start_client(host:str, port:int, controller: Controller, relay:bool = False):
    """Starts the client."""
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
        print(f"Connected to server at {host}:{port}")
        time.sleep(1)
        handshake = client_socket.recv(1024).decode("utf-8")  # Receive response" ")[1]
        print(handshake)
        if not handshake.startswith("[CONNECTED] "):
            raise ConnectionError(f"Invalid handshake: {handshake}")
        controller.setAddress(handshake.replace('[CONNECTED] ',''))
        client_socket.sendall(f"[CONNECTED] {controller.role}".encode("utf-8"))
        controller.subscribe(client_socket.sendall, callback_type, f"{host}:{port}", relay=relay)
        
        while True:
            try:
                data = client_socket.recv(4096).decode("utf-8")  # Receive data (adjust buffer size if needed)
                if not data:  # Client disconnected
                    time.sleep(1)
                    continue
                if data == '[EXIT]':
                    break
                logger.debug(f"Received from server: {data}")
                print(data)
                receive_method(data)

            except Exception as e:
                print(f"Error listening server: {e}")
                break

    except Exception as e:
        print(f"Error connecting to server: {e}")
    return
