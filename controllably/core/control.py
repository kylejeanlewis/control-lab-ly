# -*- coding: utf-8 -*-
"""
This module provides classes for a simple remote procedure call (RPC) framework.

Attributes:
    BYTE_SIZE (int): size of the byte.
    
## Classes:
    `ClassMethods`: class to store methods of a class.
    `TwoTierQueue`: a queue that can handle two types of items: normal and high-priority.
    `Proxy`: a proxy class to handle remote method calls.
    `Controller`: a class to control the flow of data and commands between models and views.
    
## Functions:
    `handle_client`: handle a client connection.
    `start_server`: start a server.
    `start_client`: start a client.

<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import asyncio
from dataclasses import dataclass
import inspect
import logging
import queue
import socket
import threading
import time
from typing import Callable, Mapping, Any, Iterable, Type
import uuid

# Local application imports
from .interpreter import Interpreter, Message

BYTESIZE = 1024

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

@dataclass
class ClassMethods:
    """ 
    Class to store methods of a class.
    
    ### Attributes:
        `name` (str): name of the class.
        `methods` (dict[str, dict[str, str]]): dictionary of methods and their parameters.
    """
    name: str
    methods: dict[str, dict[str, str]]


class TwoTierQueue:
    """
    A queue that can handle two types of items: normal and high-priority.
    
    ### Attributes:
        `normal_queue` (queue.Queue): queue for normal items.
        `high_priority_queue` (queue.PriorityQueue): queue for high-priority items.
        `last_used_queue_normal` (bool): flag to indicate the last used queue.
        `priority_counter` (int): counter for high-priority items.
        
    ### Methods:
        `qsize`: return the size of the queue
        `empty`: check if the queue is empty
        `full`: check if the queue is full
        `put`: put an item in the queue
        `put_nowait`: put an item in the queue without waiting
        `get`: get an item from the queue
        `get_nowait`: get an item from the queue without waiting
        `task_done`: mark a task as done
        `join`: wait for all tasks to be done
        `put_first`: put an item at the front of the priority queue
        `put_priority`: put a high-priority item in the queue
        `put_queue`: put an item in the queue
        `reset`: reset the queue
    """
    
    def __init__(self):
        self.normal_queue = queue.Queue()
        self.high_priority_queue = queue.PriorityQueue()
        self.last_used_queue_normal = True
        self.priority_counter = 0
        return

    def qsize(self):
        """Return the size of the queue."""
        return self.normal_queue.qsize() + self.high_priority_queue.qsize()
    
    def empty(self):
        """Check if the queue is empty."""
        return self.normal_queue.empty() and self.high_priority_queue.empty()
    
    def full(self):
        """Check if the queue is full."""
        return self.normal_queue.full() or self.high_priority_queue.full()
    
    def put(self, item: Any, block: bool = True, timeout: float|None = None, *, priority: bool = False, rank: int|None = None):
        """
        Put an item in the queue.
        
        Args:
            item (Any): item to put in the queue.
            block (bool): flag to block the queue.
            timeout (float): time to wait for the queue.
            priority (bool): flag to indicate high-priority item.
            rank (int): rank of the high-priority item.
        """
        if priority or rank is not None:
            self.priority_counter += 1
            rank = self.priority_counter if rank is None else rank
            self.put_priority(item, rank, block=block, timeout=timeout)
        else:
            self.put_queue(item, block=block, timeout=timeout)
        return
    
    def put_nowait(self, item: Any, *, priority: bool = False, rank: int = None):
        """ 
        Put an item in the queue without waiting.
        
        Args:
            item (Any): item to put in the queue.
            priority (bool): flag to indicate high-priority item.
            rank (int): rank of the high-priority item.
        """
        return self.put(item, block=False, priority=priority, rank=rank)
    
    def get(self, block: bool = True, timeout: float|None = None) -> Any:
        """
        Get an item from the queue.
        
        Args:
            block (bool): flag to block the queue.
            timeout (float): time to wait for the queue.
            
        Returns:
            Any: item from the queue.
        """
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
        """ 
        Get an item from the queue without waiting.
        
        Returns:
            Any: item from the queue.
        """
        return self.get(block=False)
    
    def task_done(self):
        """Mark a task as done."""
        return self.normal_queue.task_done() if self.last_used_queue_normal else self.high_priority_queue.task_done()
    
    def join(self):
        """Wait for all tasks to be done."""
        self.normal_queue.join()
        self.high_priority_queue.join()
        return
    
    def put_first(self, item: Any):
        """ 
        Put an item at the front of the priority queue.
        
        Args:
            item (Any): item to put in the queue.
        """
        self.put_priority(item, rank=0)
        return
    
    def put_priority(self, item: Any, rank: int, block: bool = True, timeout: float|None = None):
        """
        Put a high-priority item in the queue.
        
        Args:
            item (Any): item to put in the queue.
            rank (int): rank of the high-priority item.
            block (bool): flag to block the queue.
            timeout (float): time to wait for the queue.
        """
        self.high_priority_queue.put((rank, item), block=block, timeout=timeout)
        return
    
    def put_queue(self, item: Any, block: bool = True, timeout: float|None = None):
        """ 
        Put an item in the queue.
        
        Args:
            item (Any): item to put in the queue.
            block (bool): flag to block the queue.
            timeout (float): time to wait for the queue.
        """
        self.normal_queue.put(item, block=block, timeout=timeout)
        return

    def reset(self):
        """Reset the queue."""
        self.normal_queue = queue.Queue()
        self.high_priority_queue = queue.PriorityQueue()
        self.last_used_queue_normal = True
        self.priority_counter = 0
        return


class Proxy:
    """
    A proxy class to handle remote method calls.
    
    ### Constructor:
        `prime` (Callable): the object to create a proxy for
        `object_id` (str|None, optional): the ID of the object. Defaults to None.
        
    ### Attributes:
        `prime` (Callable): the object to create a proxy for
        `object_id` (str): the ID of the object
        `controller` (Controller): the controller bound to the proxy
        `remote` (bool): flag to indicate remote method calls
        
    ### Methods:
        `factory`: factory method to create a new class with methods and properties of the prime object
        `createMethodEmitter`: create a method emitter for the proxy class
        `createPropertyEmitter`: create a property emitter for the proxy class
        `bindController`: bind a controller to the proxy
        `releaseController`: release the controller from the proxy
    """
    
    def __new__(cls, prime:Callable, object_id:str|None = None):
        new_class = cls.factory(prime, object_id)
        return super(Proxy,cls).__new__(new_class)
    
    def __init__(self, prime:Callable, object_id:str|None = None):
        """
        Initialize the Proxy class.
        
        Args:
            prime (Callable): the object to create a proxy for
            object_id (str|None, optional): the ID of the object. Defaults to None.
        """
        self.prime = prime
        self.object_id = object_id or id(prime)
        self.controller: Controller|None = None
        self.remote = True
        return
    
    @classmethod
    def factory(cls, prime:Callable, object_id:str|None = None) -> Type[Proxy]:
        """
        Factory method to create a new class with methods and properties of the prime object.
        
        Args:
            prime (Callable): the object to create a proxy for
            object_id (str|None, optional): the ID of the object
            
        Returns:
            Type[Proxy]: the new class with methods and properties of the prime object
        """
        name = prime.__name__ if inspect.isclass(prime) else prime.__class__.__name__
        object_id = object_id or id(prime)
        attrs = dict()
        methods = {attr:cls.createMethodEmitter(getattr(prime,attr)) for attr in dir(prime) if callable(getattr(prime,attr)) and (attr not in dir(cls))}
        properties = {attr:cls.createPropertyEmitter(attr) for attr in dir(prime) if not callable(getattr(prime,attr)) and (attr not in dir(cls))}
        attrs.update(methods)
        attrs.update(properties)
        new_class = type(f"{name}_Proxy-{object_id}", (cls,), attrs)
        return new_class
    
    @staticmethod
    def createMethodEmitter(method: Callable) -> Callable:
        """
        Create a method emitter for the proxy class.
        
        Args:
            method (Callable): the method to create an emitter for
            
        Returns:
            Callable: the method emitter
        """
        def methodEmitter(self, *args, **kwargs):
            if not self.remote:
                if inspect.isclass(self.prime):
                    raise TypeError('This Proxy was created with a class, not instance.')
                prime_method = getattr(self.prime, method.__name__)
                result = prime_method(*args, **kwargs)
                return result
            
            assert isinstance(self.controller, Controller), 'No controller is bound to this Proxy.'
            controller = self.controller
            target = self.controller.registry.get(self.object_id, [])
            command = dict(
                object_id = self.object_id,
                method = method.__name__,
                args = args,
                kwargs = kwargs
            )
            request_id = controller.transmitRequest(command, target=target)
            response: dict = controller.retrieveData(request_id, data_only=False)
            data = response.get('data')
            if response.get('status', '') != 'completed':
                exception = data if isinstance(data,Exception) else Exception(data)
                raise exception
            return data
        methodEmitter.__name__ = method.__name__
        methodEmitter.__doc__ = method.__doc__
        methodEmitter.__signature__ = inspect.signature(method)
        return methodEmitter
    
    @staticmethod
    def createPropertyEmitter(attr_name:str) -> property:
        """
        Create a property emitter for the proxy class.
        
        Args:
            attr_name (str): the name of the property to create an emitter for
            
        Returns:
            property: the property emitter
        """
        def getterEmitter(self) -> Any:
            if not self.remote:
                if inspect.isclass(self.prime):
                    raise TypeError('This Proxy was created with a class, not instance.')
                result = getattr(self.prime, attr_name)
                return result
            
            assert isinstance(self.controller, Controller), 'No controller is bound to this Proxy.'
            controller = self.controller
            target = self.controller.registry.get(self.object_id, [])
            command = dict(method='getattr', args=[self.object_id, attr_name])
            request_id = controller.transmitRequest(command, target=target)
            return controller.retrieveData(request_id)
        getterEmitter.__name__ = attr_name
        getterEmitter.__doc__ = f"Property {attr_name}"
        
        def setterEmitter(self, value: Any):
            if not self.remote:
                if inspect.isclass(self.prime):
                    raise TypeError('This Proxy was created with a class, not instance.')
                result = setattr(self.prime, attr_name, value)
                return result
            
            assert isinstance(self.controller, Controller), 'No controller is bound to this Proxy.'
            controller = self.controller
            target = self.controller.registry.get(self.object_id, [])
            command = dict(method='getattr', args=[self.object_id, attr_name, value])
            request_id = controller.transmitRequest(command, target=target)
            return controller.retrieveData(request_id)
        return property(getterEmitter, setterEmitter)
    
    def bindController(self, controller: Controller):
        """
        Bind a controller to the proxy.
        
        Args:
            controller (Controller): the controller to bind to the proxy
        """
        assert isinstance(controller, Controller), 'Controller must be an instance of Controller'
        self.controller = controller
        self.remote = True
        return
    
    def releaseController(self) -> Controller:
        """
        Release the controller from the proxy.
        
        Returns:
            Controller: the controller that was bound to the proxy
        """
        assert isinstance(self.controller, Controller), 'No controller is bound to this Proxy.'
        controller = self.controller
        self.controller = None
        self.remote = False
        return controller


class Controller:
    def __init__(self, role: str, interpreter: Interpreter):
        """
        Initialize the Controller class.
        
        Args:
            role (str): the role of the controller
            interpreter (Interpreter): the interpreter to use
        """
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
        self._registry: dict[str, list[str]] = dict()
        
        self.execution_event = threading.Event()
        self.threads = {}
        
        if self.role in ('model', 'both'):
            # self.register(self)
            pass
        return
    
    @property
    def registry(self) -> dict[str,str]:
        """Object registry"""
        if self.role in ('model', 'both'):
            return self._registry
        
        registry = dict()
        registration = self.data_buffer.get('registration', {})
        if not len(registration):
            return {}
        for _, reply in registration.items():
            objects = reply.get('data', {})
            for key, address in objects.items():
                if key not in registry:
                    registry[key] = list(set(address))
                elif set(registry[key]) != set(address):
                    logger.warning(f'Conflict in object_id {key} at multiple addresses: {[registry[key], address]}')
                    logger.warning('Please resolve ID object_id conflict.')
                    registry[key] = list(set(registry[key] + address))
        return registry
    @registry.setter
    def registry(self, value: dict[str,str]):
        if self.role in ('model', 'both'):
            self._registry = value
        return
    
    # Model side
    def receiveRequest(self, request: Message):
        """ 
        Receive a request
        
        Args:
            request (Message): the request to receive
        """
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
        """
        Transmit data
        
        Args:
            data (Any): the data to transmit
            metadata (Mapping[str, Any]|None, optional): the metadata to include. Defaults to None.
            status (Mapping[str, Any]|None, optional): the status to include. Defaults to None.
        """
        assert self.role in ('model', 'both', 'relay'), "Only the model can transmit data"
        response = dict()
        status = status or dict(status='completed')
        response.update(dict(data=data))
        response.update(status)
        response.update(metadata)
        package = self.interpreter.encodeData(response)
        logger.debug('Transmitted data')
        self.relayData(package)
        return
    
    def broadcastRegistry(self, target: Iterable[str]|None = None):
        """ 
        Broadcast the registry
        
        Args:
            target (Iterable[str]|None, optional): the target addresses. Defaults to None.
        """
        address = self.address or str(id(self))
        target = target if target is not None else []
        self.registry = {key: [address] for key in self.objects}
        metadata = self.extractMetadata(dict(method='registration'))
        metadata.update(dict(
            request_id = 'registration',
            reply_id = address,
            address = metadata.get('address', dict(sender=[address],target=target))
        ))
        self.transmitData(
            data = self.registry,
            metadata = metadata,
            status = dict(status='completed')
        )
        return
    
    def register(self, new_object: Callable, object_id: str|None = None):
        """
        Register an object
        
        Args:
            new_object (Callable): the object to register
            object_id (str|None, optional): the ID of the object. Defaults to None.
        """
        assert self.role in ('model', 'both'), "Only the model can register object"
        key =  str(id(new_object)) if object_id is None else object_id
        if key in self.object_methods:
            logger.warning(f"{new_object.__class__}_{key} already registered.")
            return False
        self.object_methods[key] = self.extractMethods(new_object)
        self.objects[key] = new_object
        self.broadcastRegistry()
        return
    
    def unregister(self, object_id:str|None = None, old_object: Callable|None = None) -> bool:
        """
        Unregister an object
        
        Args:
            object_id (str|None, optional): the ID of the object. Defaults to None.
            old_object (Callable|None, optional): the object to unregister. Defaults to None.
            
        Returns:
            bool: flag indicating success
        """
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
        self.broadcastRegistry()
        return success
    
    def extractMetadata(self, command: Mapping[str, Any]) -> dict[str, Any]:
        """
        Extract metadata from a command
        
        Args:
            command (Mapping[str, Any]): the command to extract metadata from
            
        Returns:
            dict[str, Any]: the extracted metadata
        """
        target = command.get('address', {}).get('sender', [])
        target.extend(self.relays)
        sender = [self.address or str(id(self))]
        return dict(
            address = dict(sender=sender, target=target),
            request_id = command.get('request_id', uuid.uuid4().hex),
            reply_id = uuid.uuid4().hex,
            priority = command.get('priority', False),
            rank = command.get('rank', None)
        )
    
    @staticmethod
    def extractMethods(new_object: Callable) -> ClassMethods:
        """
        Extract methods from an object
        
        Args:
            new_object (Callable): the object to extract methods from
            
        Returns:
            ClassMethods: the extracted methods
        """
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
    
    def exposeMethods(self):
        """Expose methods of registered objects"""
        assert self.role in ('model', 'both'), "Only the model can expose methods"
        return {k:v.__dict__ for k,v in self.object_methods.items()}
    
    def start(self):
        """Start the execution loop"""
        assert self.role in ('model', 'both'), "Only the model can start execution loop"
        self.execution_event.set()
        self.threads['execution'] = threading.Thread(target=self._loop_execution, daemon=True)
        logger.info("Starting execution loop")
        for thread in self.threads.values():
            thread.start()
        return
    
    def stop(self):
        """Stop the execution loop"""
        assert self.role in ('model', 'both'), "Only the model can stop execution loop"
        self.execution_event.clear()
        logger.info("Stopping execution loop")
        for thread in self.threads.values():
            thread.join()
        return
   
    def executeCommand(self, command: Mapping[str, Any]) -> tuple[Any, dict[str, Any]]:
        """
        Execute a command
        
        Args:
            command (Mapping[str, Any]): the command to execute
            
        Returns:
            tuple[Any, dict[str, Any]]: the result of the command and the status
        """
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
                    return 'Object not found', dict(status='error')
                
                if not isinstance(name, str):
                    assert isinstance(name, Iterable), "Invalid input for attribute(s)"
                    data = {attr: getattr(this_object, attr) for attr in name if hasattr(this_object, attr)}
                    return data, dict(status='completed')
                
                if not hasattr(this_object, name):
                    logger.error(f"Attribute not found: {name}")
                    return 'Attribute not found', dict(status='error')
                if method_name == 'getattr':
                    return getattr(this_object, name), dict(status='completed')
                elif method_name == 'setattr':
                    value = args[2] if len(args) > 2 else kwargs.get('value', None)
                    if value is None:
                        logger.error(f"Value not provided for attribute: {name}")
                        return 'Value not provided', dict(status='error')
                    setattr(this_object, name, args[2]), dict(status='completed')
                    return None, dict(status='completed')
                elif method_name == 'delattr':
                    delattr(this_object, name)
                    return None, dict(status='completed')
            else:
                logger.error(f"Object not found: {object_id}")
                return 'Object not found', dict(status='error')
        
        this_object = self.objects[object_id]
        try:
            method: Callable = getattr(this_object, method_name)
        except AttributeError:
            logger.error(f"Method not found: {method_name}")
            return 'Method not found', dict(status='error')
        
        logger.info(f"Executing command: {command}")
        args = command.get('args', [])
        kwargs = command.get('kwargs', {})
        try:
            out = method(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return str(e), dict(status='error')
        logger.info(f"Completed command: {command}")
        return out, dict(status='completed')
    
    def _loop_execution(self):
        """Execution loop"""
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
        """
        Transmit a request
        
        Args:
            command (Mapping[str, Any]): the command to transmit
            target (Iterable[int]|None, optional): the target addresses. Defaults to None.
            private (bool, optional): flag to indicate private transmission. Defaults to True.
            priority (bool, optional): flag to indicate high-priority transmission. Defaults to False.
            rank (int, optional): rank of the high-priority transmission. Defaults to None.
            
        Returns:
            str: the request ID
        """
        assert self.role in ('view', 'both'), "Only the view can transmit requests"
        sender = [self.address or str(id(self))] if private else []
        target = target if target is not None else []
        target.extend(self.relays)
        request_id = uuid.uuid4().hex
        self.data_buffer[request_id] = dict()
        command['address'] = dict(sender=sender, target=target)
        command['request_id'] = request_id
        command['priority'] = priority
        command['rank'] = rank
        request = self.interpreter.encodeRequest(command)
        logger.debug('Transmitted request')
        self.relayRequest(request)
        return request_id
    
    def receiveData(self, package: Message):
        """
        Receive data
        
        Args:
            package (Message): the package to receive
        """
        assert self.role in ('view', 'both'), "Only the view can receive data"
        data = self.interpreter.decodeData(package)
        sender = data.get('address', {}).get('sender', [])
        request_id = data.get('request_id', uuid.uuid4().hex)
        reply_id = data.get('reply_id', uuid.uuid4().hex)
        if len(sender):
            logger.info(f"[{self.address or str(id(self))}] Received data from {sender}")
        
        reply_data = {reply_id: data}
        if request_id not in self.data_buffer:
            self.data_buffer[request_id] = reply_data
        else:
            self.data_buffer[request_id].update(reply_data)
        logger.debug('Received data')
        return
    
    def retrieveData(self, 
        request_id: str, 
        timeout: int|float = 5, 
        *, 
        min_count: int|None = 1, 
        max_count: int|None = 1,
        default: Any|None = None,
        data_only: bool = True,
        close_request: bool = True
    ) -> Any | dict[tuple[str,str], Any]:
        """
        Retrieve data
        
        Args:
            request_id (str): the request ID
            timeout (int|float, optional): the timeout. Defaults to 5.
            min_count (int|None, optional): the minimum count. Defaults to 1.
            max_count (int|None, optional): the maximum count. Defaults to 1.
            default (Any|None, optional): the default value. Defaults to None.
            data_only (bool, optional): flag to indicate data only. Defaults to True.
            close_request (bool, optional): flag to indicate close request. Defaults to True.
            
        Returns:
            Any | dict[tuple[str,str], Any]: the retrieved data
        """
        assert self.role in ('view', 'both'), "Only the view can listen for data"
        all_data = dict()
        count = 0
        start_time = time.perf_counter()
        while request_id in self.data_buffer:
            time.sleep(0.1)
            if min_count and (count >= min_count):
                break
            if (time.perf_counter()-start_time) >= timeout:
                logger.warning(f"Timeout retrieving data for request_id: {request_id}")
                logger.warning("Please try again later.")
                return all_data if len(all_data) else None
            if len(self.data_buffer[request_id]):
                reply_ids = list(self.data_buffer[request_id].keys())
                for reply_id in reply_ids:
                    response = self.data_buffer[request_id].pop(reply_id)
                    status = response.get('status', None)
                    data = response.get('data', default)
                    sender = response.get('address', {}).get('sender', [])[0]
                    if status != 'completed':
                        error_message = data if status == 'error' else "Unable to read response"
                        logger.warning(error_message)
                        data = Exception(error_message)
                    all_data.update({(sender,reply_id[-6:]): (data if data_only else response)})
                    count += 1
                    if count >= max_count:
                        break
                    start_time = time.perf_counter()
                continue
        if close_request:
            self.data_buffer.pop(request_id)
        if max_count == 1:
            return (data if data_only else response)
        return all_data
    
    def getMethods(self, target: Iterable[int]|None = None, *, private: bool = True) -> dict:
        """
        Get methods
        
        Args:
            target (Iterable[int]|None, optional): the target addresses. Defaults to None.
            private (bool, optional): flag to indicate private transmission. Defaults to True.
            
        Returns:
            dict: the methods
        """
        assert self.role in ('view', 'both'), "Only the view can get methods"
        command = dict(method='exposeMethods')
        request_id = self.transmitRequest(command, target, private=private)
        return self.retrieveData(request_id, default={})
    
    # Controller side
    def relay(self, message: Message, callback_type:str, addresses: Iterable[int]|None = None):
        """
        Relay a message
        
        Args:
            message (Message): the message to relay
            callback_type (str): the callback type
            addresses (Iterable[int]|None, optional): the target addresses. Defaults to None.
        """
        assert callback_type in self.callbacks, f"Invalid callback type: {callback_type}"
        self_address = self.address or str(id(self))
        if self_address in addresses and self.role == 'relay':
            addresses.remove(self_address)
        addresses = addresses or self.callbacks[callback_type].keys()
        for address in set(addresses):
            if address not in self.callbacks[callback_type]:
                if len(self.relays) == 0:
                    logger.warning(f"Callback not found for address: {address}")
                continue
            callback = self.callbacks[callback_type][address]
            callback(message)
        time.sleep(1)
        return
    
    def relayRequest(self, request: Message):
        """
        Relay a request
        
        Args:
            request (Message): the request to relay
        """
        content = self.interpreter.decodeRequest(request)
        addresses = content.get('address', {}).get('target', [])
        self.relay(request, 'request', addresses=addresses)
        if self.role == 'relay':
            logger.debug('Relayed request')
        return
    
    def relayData(self, package: Message):
        """
        Relay data
        
        Args:
            package (Message): the package to relay
        """
        content = self.interpreter.decodeData(package)
        if self.role == 'relay':
            if content.get('request_id', '') == 'registration':
                if content.get('reply_id', '') != self.address:
                    if 'registration' not in self.data_buffer:
                        self.data_buffer['registration'] = dict()
                    sender = content.get('address', {}).get('sender', ['UNKNOWN'])[0]
                    self.data_buffer['registration'].update({sender: content})
                    return self.broadcastRegistry()
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
        """
        Subscribe to a callback
        
        Args:
            callback (Callable): the callback to subscribe
            callback_type (str): the callback type
            address (int|str|None, optional): the address. Defaults to None.
            relay (bool, optional): flag to indicate relay. Defaults to False.
        """
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
    
    def unsubscribe(self, callback_type: str, address: int|str):
        """
        Unsubscribe from a callback
        
        Args:
            callback_type (str): the callback type
            address (int|str): the address
        """
        assert callback_type in self.callbacks, f"Invalid callback type: {callback_type}"
        key = address
        key = str(key)
        _callback = self.callbacks[callback_type].pop(key, None)
        if _callback is None:
            logger.warning(f"{key} was not subscribed to {callback_type}")
            return
        if key in self.relays:
            self.relays.remove(key)
        return
    
    def setAddress(self, address: int|str):
        """
        Set the address
        
        Args:
            address (int|str): the address
        """
        assert isinstance(address, (int,str)), f"Invalid address: {address}"
        self.address = address
        return


# --- Socket Communication Implementation ---
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
    if relay:
        if client_role not in ('model', 'view'):
            raise ValueError(f"Invalid role: {client_role}")
        callback_type = 'request' if client_role == 'model' else 'data'
        receive_method = controller.relayData if client_role == 'model' else controller.relayRequest
        # match client_role:
        #     case 'model':  # (i.e. client is a model)
        #         receive_method = controller.relayData
        #         callback_type = 'request'
        #     case 'view':
        #         receive_method = controller.relayRequest
        #         callback_type = 'data'
        #     case _:
        #         raise ValueError(f"Invalid role: {client_role}")
    
    terminate = threading.Event() if terminate is None else terminate
    while not terminate.is_set():
        try:
            data = ''
            while True:
                fragment = client_socket.recv(BYTESIZE).decode("utf-8", "replace").replace('\uFFFD', '')  # Receive data (adjust buffer size if needed)
                data += fragment
                if len(fragment)==0 or len(fragment) < BYTESIZE:
                    break
            if not data:  # Client disconnected
                time.sleep(1)
                continue
            if data == '[EXIT]':
                break
            logger.debug(f"Received from client: {data}")
            logger.debug(data)
            data = data.encode("utf-8") if relay else data
            receive_method(data)
        except Exception as e:
            logger.error(f"Error handling client: {e}")
            break
    client_socket.close()
    logger.warning(f"Disconnected from client [{client_addr}]")
    
    # Clean up
    controller.unsubscribe(callback_type, client_addr)
    controller.data_buffer.get('registration', {}).pop(client_addr, None)
    return


def start_server(host:str, port:int, controller: Controller, *, terminate: threading.Event|None = None):
    """
    Starts the server
    
    Args:
        host (str): the host
        port (int): the port
        controller (Controller): the controller
        terminate (threading.Event|None, optional): the termination event. Defaults to None
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)  # Listen for up to 5 connections

    print(f"Server listening on {host}:{port}")
    controller.setAddress(f"{host}:{port}")

    threads = []
    terminate = threading.Event() if terminate is None else terminate
    while not terminate.is_set():
        client_socket, addr = server_socket.accept()  # Accept a connection
        logger.info(f"Client connected from {addr}")
        client_addr = f"{addr[0]}:{addr[1]}"
        client_socket.sendall(f"[CONNECTED] {client_addr}".encode("utf-8"))
        handshake = client_socket.recv(BYTESIZE).decode("utf-8", "replace").replace('\uFFFD', '')  # Receive response" ")[1]
        print(handshake)
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
            target = handle_client, daemon = True,
            args = (client_socket,client_addr,controller,client_role), 
            kwargs = dict(terminate=terminate),
        )
        client_thread.start()
        threads.append(client_thread)
    
    for thread in threads:
        thread.join()
    logger.warning(f"Server [{host}:{port}] stopped.")
    return


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
        logger.info(f"Connected to server at {host}:{port}")
        time.sleep(1)
        handshake = client_socket.recv(BYTESIZE).decode("utf-8","replace").replace('\uFFFD', '')  # Receive response" ")[1]
        print(handshake)
        if not handshake.startswith("[CONNECTED] "):
            raise ConnectionError(f"Invalid handshake: {handshake}")
        controller.setAddress(handshake.replace('[CONNECTED] ',''))
        client_socket.sendall(f"[CONNECTED] {controller.role}".encode("utf-8"))
        controller.subscribe(client_socket.sendall, callback_type, f"{host}:{port}", relay=relay)
        
        terminate = threading.Event() if terminate is None else terminate
        while not terminate.is_set():
            try:
                data = ''
                while True:
                    fragment = client_socket.recv(BYTESIZE).decode("utf-8","replace").replace('\uFFFD', '')  # Receive data (adjust buffer size if needed)
                    data += fragment
                    if len(fragment)==0 or len(fragment) < BYTESIZE:
                        break
                if not data:  # Client disconnected
                    time.sleep(1)
                    continue
                if data == '[EXIT]':
                    break
                logger.debug(f"Received from server: {data}")
                logger.debug(data)
                receive_method(data)
            except Exception as e:
                logger.error(f"Error listening server: {e}")
                break
    except Exception as e:
        logger.error(f"Error connecting to server: {e}")
    else:
        logger.warning(f"Disconnected from server [{host}:{port}]")
    return
