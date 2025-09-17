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

<i>Documentation last updated: 2025-06-11</i>
"""
# Standard library imports
from __future__ import annotations
import builtins
from dataclasses import dataclass
import inspect
import logging
import queue
import threading
import time
from typing import Callable, Mapping, Any, Iterable, Type
import uuid

# Local application imports
from .interpreter import Interpreter

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)
CustomLevelFilter().setModuleLevel(__name__, logging.INFO)

BYTESIZE = 1024

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
        self.priority_counter = 1
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
            block (bool, optional): flag to block the queue. Defaults to True.
            timeout (float, optional): time to wait for the queue. Defaults to None.
            priority (bool, optional): flag to indicate high-priority item. Defaults to False.
            rank (int, optional): rank of the high-priority item. Defaults to None.
        """
        if priority or rank is not None:
            rank = self.priority_counter if rank is None else rank
            self.put_priority(item, rank, block=block, timeout=timeout)
            self.priority_counter += 1
        else:
            self.put_queue(item, block=block, timeout=timeout)
        return
    
    def put_nowait(self, item: Any, *, priority: bool = False, rank: int|None = None):
        """ 
        Put an item in the queue without waiting.
        
        Args:
            item (Any): item to put in the queue.
            priority (bool, optional): flag to indicate high-priority item. Defaults to False.
            rank (int|None, optional): rank of the high-priority item. Defaults to None.
        """
        return self.put(item, block=False, priority=priority, rank=rank)
    
    def get(self, block: bool = True, timeout: float|None = None) -> Any:
        """
        Get an item from the queue.
        
        Args:
            block (bool): flag to block the queue. Defaults to True.
            timeout (float): time to wait for the queue. Defaults to None.
            
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
            rank (int): rank of the high-priority item
            block (bool, optional): flag to block the queue. Defaults to True.
            timeout (float, optional): time to wait for the queue. Defaults to None.
        """
        self.high_priority_queue.put((rank, item), block=block, timeout=timeout)
        
        return
    
    def put_queue(self, item: Any, block: bool = True, timeout: float|None = None):
        """ 
        Put an item in the queue.
        
        Args:
            item (Any): item to put in the queue.
            block (bool, optional): flag to block the queue. Defaults to True.
            timeout (float, optional): time to wait for the queue. Defaults to None.
        """
        self.normal_queue.put(item, block=block, timeout=timeout)
        return

    def reset(self):
        """Reset the queue."""
        self.normal_queue = queue.Queue()
        self.high_priority_queue = queue.PriorityQueue()
        self.last_used_queue_normal = True
        self.priority_counter = 1
        return


class Proxy:
    """
    A proxy class to handle remote method calls.
    
    ### Constructor:
        `prime` (object): the object to create a proxy for
        `object_id` (str|None, optional): the ID of the object. Defaults to None.
        
    ### Attributes:
        `prime` (object): the object to create a proxy for
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
    
    def __new__(cls, prime:object, object_id:str|None = None):
        new_class = cls.factory(prime, object_id)
        return super(Proxy,cls).__new__(new_class)
    
    def __init__(self, prime:object, object_id:str|None = None):
        """
        Initialize the Proxy class.
        
        Args:
            prime (object): the object to create a proxy for
            object_id (str|None, optional): the ID of the object. Defaults to None.
        """
        self.prime = prime
        self.object_id = object_id or id(prime)
        self.controller: Controller|None = None
        self.remote = False
        return
    
    @classmethod
    def factory(cls, prime:object, object_id:str|None = None) -> Type[Proxy]:
        """
        Factory method to create a new class with methods and properties of the prime object.
        
        Args:
            prime (object): the object to create a proxy for
            object_id (str|None, optional): the ID of the object. Defaults to None.
            
        Returns:
            Type[Proxy]: the new class with methods and properties of the prime object
        """
        class_ = prime if inspect.isclass(prime) else prime.__class__
        name = class_.__name__
        object_id = object_id or id(prime)
        attrs = dict()
        methods = {attr:cls.createMethodEmitter(getattr(prime,attr)) for attr in dir(prime) if callable(getattr(prime,attr)) and (attr not in dir(cls))}
        properties = {attr:cls.createPropertyEmitter(attr) for attr in dir(prime) if not callable(getattr(prime,attr)) and (attr not in dir(cls))}
        attrs.update(methods)
        attrs.update(properties)
        new_class = type(f"{name}_Proxy-{object_id}", (cls,class_), attrs)
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
        def methodEmitter(self: Proxy, *args, **kwargs):
            if not self.remote:
                if inspect.isclass(self.prime):
                    raise TypeError('This Proxy was created with a class, not instance.')
                prime_method = getattr(self.prime, method.__name__)
                result = prime_method(*args, **kwargs)
                return result
            
            assert isinstance(self.controller, Controller), 'No controller is bound to this Proxy.'
            controller = self.controller
            target = self.controller.registry.get(self.object_id, [])
            sender = target[0] if len(target) else None
            command = dict(
                object_id = self.object_id,
                method = method.__name__,
                args = args,
                kwargs = kwargs
            )
            request_id = controller.transmitRequest(command, target=target)
            response: dict = controller.retrieveData(request_id, sender=sender, data_only=False)
            data = response.get('data')
            if response.get('status', '') != 'completed':
                error_type_name, message = data.split('!!', maxsplit=1)
                error_type = getattr(builtins, error_type_name, Exception)
                exception = error_type(message)
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
        def getterEmitter(self: Proxy) -> Any:
            if not self.remote:
                if inspect.isclass(self.prime):
                    raise TypeError('This Proxy was created with a class, not instance.')
                result = getattr(self.prime, attr_name)
                return result
            
            assert isinstance(self.controller, Controller), 'No controller is bound to this Proxy.'
            controller = self.controller
            target = self.controller.registry.get(self.object_id, [])
            sender = target[0] if len(target) else None
            command = dict(method='getattr', args=[self.object_id, attr_name])
            request_id = controller.transmitRequest(command, target=target)
            return controller.retrieveData(request_id, sender=sender)
        getterEmitter.__name__ = attr_name
        getterEmitter.__doc__ = f"Property {attr_name}"
        
        def setterEmitter(self: Proxy, value: Any):
            if not self.remote:
                if inspect.isclass(self.prime):
                    raise TypeError('This Proxy was created with a class, not instance.')
                result = setattr(self.prime, attr_name, value)
                return result
            
            assert isinstance(self.controller, Controller), 'No controller is bound to this Proxy.'
            controller = self.controller
            target = self.controller.registry.get(self.object_id, [])
            sender = target[0] if len(target) else None
            command = dict(method='setattr', args=[self.object_id, attr_name, value])
            request_id = controller.transmitRequest(command, target=target)
            return controller.retrieveData(request_id, sender=sender)
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
        all_attributes = controller.getAttributes()
        assert self.object_id in all_attributes, f"Object ID {self.object_id} not found in controller registry: {list(all_attributes.keys())}"
        matching_attributes = all_attributes.get(self.object_id, ['',[]])
        class_name = self.prime.__name__ if inspect.isclass(self.prime) else self.prime.__class__.__name__
        assert class_name == matching_attributes[0], f"Class name {class_name} does not match remote class name {matching_attributes[0]}"
        if not inspect.isclass(self.prime):
            return
        for attr in matching_attributes[1]:
            if not hasattr(self.prime, attr):
                setattr(self.__class__, attr, self.createPropertyEmitter(attr))
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
    """
    A class to control the flow of data and commands between models and views.
    
    ### Constructor:
        `role` (str): the role of the controller
        `interpreter` (Interpreter): the interpreter to use
        `relay_delay` (int, optional): delay for relaying data. Defaults to 1.
        
    ### Attributes and properties:
        `role` (str): the role of the controller
        `interpreter` (Interpreter): the interpreter to use
        `address` (str|None): the address of the controller
        `relay_delay` (int): delay for relaying data
        `relays` (list): list of relays
        `callbacks` (dict[str, dict[str, Callable]]): dictionary of callbacks
        `events` (dict[str, threading.Event]): dictionary of events
        `command_queue` (TwoTierQueue): command queue
        `data_buffer` (dict): data buffer
        `objects` (dict): dictionary of objects
        `object_methods` (dict[str, ClassMethods]): dictionary of object methods
        `object_attributes` (dict[str, tuple[str]]): dictionary of object attributes
        `execution_event` (threading.Event): event for execution loop
        `registry` (dict[str, list[str]]): object registry
        
    ### Methods:
        `receiveRequest`: receive a request
        `transmitData`: transmit data
        `broadcastRegistry`: broadcast the registry
        `register`: register an object
        `unregister`: unregister an object
        `extractMetadata`: extract metadata from a command
        `extractMethods`: extract methods from an object
        `exposeAttributes`: expose attributes of registered objects
        `exposeMethods`: expose methods of registered objects
        `start`: start the execution loop
        `stop`: stop the execution loop
        `executeCommand`: execute a command
        `transmitRequest`: transmit a request
        `receiveData`: receive data
        `retrieveData`: retrieve data
        `getAttributes`: get attributes of the controller
        `getMethods`: get methods of the controller
        `relay`: relay a request or data
        `relayRequest`: relay a request
        `relayData`: relay data
        `subscribe`: subscribe to a relay
        `unsubscribe`: unsubscribe from a relay
        `setAddress`: set the address of the controller
    """
    
    def __init__(self, role: str, interpreter: Interpreter, *, relay_delay: int = 1):
        """
        Initialize the Controller class.
        
        Args:
            role (str): the role of the controller
            interpreter (Interpreter): the interpreter to use
            relay_delay (int, optional): delay for relaying data. Defaults to 1.
        """
        assert role in ('model', 'view', 'both', 'relay'), f"Invalid role: {role}"
        assert isinstance(interpreter, Interpreter), f"Invalid interpreter: {interpreter}"
        self.role = role
        self.interpreter = interpreter
        self.address = None
        
        self.relay_delay = relay_delay
        self.relays = []
        self.callbacks: dict[str, dict[str,Callable]] = dict(request={}, data={}, listen={})
        self.events: dict[str, threading.Event] = dict()
        self.command_queue = TwoTierQueue()
        self.data_buffer = dict()
        self.objects = {}
        self.object_methods: dict[str, ClassMethods] = dict()
        self.object_attributes: dict[str, tuple[str]] = dict()
        self._registry: dict[str, list[str]] = dict()
        
        self.execution_event = threading.Event()
        self._threads = {}
        
        # if self.role in ('model', 'both'):
        #     # self.register(self)
        #     pass
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
        
        duplicates = []
        for _, reply in registration.items():
            objects = reply.get('data', {})
            for key, address in objects.items():
                if key not in registry:
                    registry[key] = list(set(address))
                elif set(registry[key]) != set(address):
                    logger.warning(f'Conflict in object_id {key} at multiple addresses: {[registry[key], address]}')
                    
                    registry[key] = list(set(registry[key] + address))
                    duplicates.append(key)
        duplicates = list(set(duplicates))
        if duplicates:
            logger.warning('Please resolve object_id conflict(s) above.')
            raise LookupError(f"{len(duplicates)} object(s) with same ID: {duplicates}")
        return registry
    @registry.setter
    def registry(self, value: dict[str,str]):
        if self.role in ('model', 'both'):
            self._registry = value
        return
    
    # Model side
    def receiveRequest(self, packet: str|bytes|None = None, *, sender: str|None = None, **kwargs):
        """ 
        Receive a request
        
        Args:
            packet (str|bytes, optional): the request to receive. Defaults to None.
            sender (str|None, optional): the sender of the request. Defaults to None.
        """
        assert self.role in ('model', 'both'), "Only the model can receive requests"
        if packet is None:
            sender = sender or 'main'
            if sender not in self.callbacks['listen']:
                return
            packet = self.callbacks['listen'][sender](**kwargs)
        command = self.interpreter.decodeRequest(packet)
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
        packet = self.interpreter.encodeData(response)
        logger.debug('Transmitted data')
        self.relayData(packet)
        return
    
    def broadcastRegistry(self, target: Iterable[str]|None = None):
        """ 
        Broadcast the registry
        
        Args:
            target (Iterable[str]|None, optional): the target addresses. Defaults to None.
        """
        address = self.address or str(id(self))
        target = list(target) if target is not None else []
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
            logger.warning(f"{new_object.__class__.__name__}_{key} already registered.")
            return False
        self.object_methods[key] = self.extractMethods(new_object)
        self.object_attributes[key] = tuple(set([attr for attr in dir(new_object) if not callable(getattr(new_object, attr)) and (not attr.startswith('_') and not attr.endswith('__'))]))
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
            self.object_attributes.pop(key)
            self.objects.pop(key)
            success = True
        except KeyError:
            if old_object is not None:
                logger.warning(f"Object not found: {old_object.__class__.__name__} [{key}]")
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
    
    def exposeAttributes(self):
        """Expose attributes of registered objects"""
        assert self.role in ('model', 'both'), "Only the model can expose attributes"
        return {k: (self.objects[k].__class__.__name__, v) for k,v in self.object_attributes.items()}
    
    def exposeMethods(self):
        """Expose methods of registered objects"""
        assert self.role in ('model', 'both'), "Only the model can expose methods"
        return {k:v.__dict__ for k,v in self.object_methods.items()}
    
    def start(self):
        """Start the execution loop"""
        assert self.role in ('model', 'both'), "Only the model can start execution loop"
        self.execution_event.set()
        self._threads['execution'] = threading.Thread(target=self._loop_execution, daemon=True)
        logger.info("Starting execution loop")
        for thread in self._threads.values():
            thread.start()
        return
    
    def stop(self):
        """Stop the execution loop"""
        assert self.role in ('model', 'both'), "Only the model can stop execution loop"
        self.execution_event.clear()
        logger.info("Stopping execution loop")
        for thread in self._threads.values():
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
            if method_name in ('exposeMethods','exposeAttributes'):
                return getattr(self,method_name)(), dict(status='completed')
            elif method_name in ('getattr', 'setattr', 'delattr'):
                args = command.get('args', [])
                kwargs = command.get('kwargs', {})
                object_id = args[0] if len(args) else kwargs.get('object_id', '')
                name = args[1] if len(args) > 1 else kwargs.get('name', '')
                this_object = self.objects.get(object_id)
                if this_object is None:
                    logger.error(f"Object not found: {object_id}")
                    return f'KeyError!!Object not found: {object_id}', dict(status='error')
                
                if not isinstance(name, str):
                    assert isinstance(name, Iterable), "Invalid input for attribute(s)"
                    data = {attr: getattr(this_object, attr) for attr in name if hasattr(this_object, attr)}
                    return data, dict(status='completed')
                
                if not hasattr(this_object, name):
                    logger.error(f"Attribute not found: {name}")
                    return f'AttributeError!!Attribute not found: {name}', dict(status='error')
                if method_name == 'getattr':
                    return getattr(this_object, name), dict(status='completed')
                elif method_name == 'setattr':
                    value = args[2] if len(args) > 2 else kwargs.get('value', None)
                    if value is None:
                        logger.error(f"Value not provided for attribute: {name}")
                        return f'ValueError!!Value not provided for attribute: {name}', dict(status='error')
                    setattr(this_object, name, value), dict(status='completed')
                    return None, dict(status='completed')
                elif method_name == 'delattr':
                    delattr(this_object, name)
                    return None, dict(status='completed')
            else:
                logger.error(f"Object not found: {object_id}")
                return 'KeyError!!Object not found', dict(status='error')
        
        this_object = self.objects[object_id]
        try:
            method: Callable = getattr(this_object, method_name)
        except AttributeError:
            logger.error(f"Method not found: {method_name}")
            return f'AttributeError!!Method not found: {method_name}', dict(status='error')
        
        logger.info(f"Executing command: {command}")
        args = command.get('args', [])
        kwargs = command.get('kwargs', {})
        try:
            out = method(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing command: {command} ({args}, {kwargs})")
            logger.error(f"{e.__class__.__name__}: {e}")
            return f"{e.__class__.__name__}!!{e}", dict(status='error')
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
            except ConnectionError:
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
            except ConnectionError:
                break
        self.command_queue.join()
        return
    
    # View side
    def transmitRequest(self, 
        command: Mapping[str, Any], 
        target: Iterable[int|str]|None = None, 
        *, 
        private:bool = True, 
        priority: bool = False, 
        rank: int|None = None
    ) -> str:
        """
        Transmit a request
        
        Args:
            command (Mapping[str, Any]): the command to transmit
            target (Iterable[int|str]|None, optional): the target addresses. Defaults to None.
            private (bool, optional): flag to indicate private transmission. Defaults to True.
            priority (bool, optional): flag to indicate high-priority transmission. Defaults to False.
            rank (int, optional): rank of the high-priority transmission. Defaults to None.
            
        Returns:
            str: the request ID
        """
        assert self.role in ('view', 'both'), "Only the view can transmit requests"
        sender = [self.address or str(id(self))] if private else []
        target = list(target) if target is not None else []
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
    
    def receiveData(self, packet: str|bytes|None = None, *, sender: str|None = None, **kwargs):
        """
        Receive data
        
        Args:
            packet (str|bytes, optional): the packet to receive. Defaults to None.
            sender (str|None, optional): the sender of the packet. Defaults to None.
        """
        assert self.role in ('view', 'both'), "Only the view can receive data"
        if packet is None:
            sender = sender or 'main'
            if sender not in self.callbacks['listen']:
                return
            packet = self.callbacks['listen'][sender](**kwargs)
        data = self.interpreter.decodeData(packet)
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
        sender: str|None = None,
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
        data = default
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
                        error_type_name, message = error_message.split('!!', maxsplit=1)
                        error_type = getattr(builtins, error_type_name, Exception)
                        data = error_type(message)
                    all_data.update({(sender,reply_id[-6:]): (data if data_only else response)})
                    count += 1
                    if count >= max_count:
                        break
                    start_time = time.perf_counter()
                continue
            else:
                self.receiveData(sender=sender, request_id=request_id)
        if close_request:
            self.data_buffer.pop(request_id, None)
        if max_count == 1:
            return (data if data_only else response)
        return all_data
    
    def getAttributes(self, target: Iterable[int]|None = None, *, private: bool = True) -> dict:
        """
        Get attributes
        
        Args:
            target (Iterable[int]|None, optional): the target addresses. Defaults to None.
            private (bool, optional): flag to indicate private transmission. Defaults to True.
        
        Returns:
            dict: the attributes
        """
        assert self.role in ('view', 'both'), "Only the view can get attributes"
        command = dict(method='exposeAttributes')
        target = target or list(self.callbacks['request'].keys())
        target = tuple(set(target))
        request_id = self.transmitRequest(command, target, private=private)
        attributes = dict()
        for worker in target:
            data = self.retrieveData(
                request_id, 
                sender=worker,
                default={},
                close_request=False
            )
            time.sleep(0.1)
            if isinstance(data, dict):
                attributes.update(data)
        return attributes
    
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
        target = target or list(self.callbacks['request'].keys())
        target = tuple(set(target))
        request_id = self.transmitRequest(command, target, private=private)
        methods = dict()
        for worker in target:
            data = self.retrieveData(
                request_id, 
                sender=worker,
                default={},
                close_request=False
            )
            time.sleep(0.1)
            if isinstance(data, dict):
                methods.update(data)
        return methods
    
    # Controller side
    def relay(self, packet: str|bytes|None, callback_type:str, addresses: Iterable[int]|None = None):
        """
        Relay a message
        
        Args:
            packet (str|bytes|None): the message to relay
            callback_type (str): the callback type
            addresses (Iterable[int]|None, optional): the target addresses. Defaults to None.
        """
        assert callback_type in self.callbacks, f"Invalid callback type: {callback_type}"
        self_address = self.address or str(id(self))
        addresses = list(set(addresses))
        if self_address in addresses and self.role in ('relay','both'):
            addresses.remove(self_address)
        addresses = addresses or self.callbacks[callback_type].keys()
        for address in set(addresses):
            if address not in self.callbacks[callback_type]:
                if len(self.relays) == 0:
                    logger.warning(f"Callback not found for address: {address}")
                continue
            callback = self.callbacks[callback_type][address]
            callback(packet)
        if self.relay_delay > 0:
            time.sleep(self.relay_delay)
        return
    
    def relayRequest(self, packet: str|bytes|None = None, **kwargs):
        """
        Relay a request
        
        Args:
            packet (str|bytes, optional): the request to relay. Defaults to None.
        """
        # if packet is None:
        #     packet = self.callbacks['listen'](**kwargs)
        content = self.interpreter.decodeRequest(packet)
        addresses = content.get('address', {}).get('target', [])
        self.relay(packet, 'request', addresses=addresses)
        if self.role in ('relay', 'both'):
            logger.debug('Relayed request')
        return
    
    def relayData(self, packet: str|bytes|None = None, **kwargs):
        """
        Relay data
        
        Args:
            packet (str|bytes, optional): the packet to relay. Defaults to None.
        """
        # if packet is None:
        #     packet = self.callbacks['listen'](**kwargs)
        content = self.interpreter.decodeData(packet)
        addresses = content.get('address', {}).get('target', [])
        if self.role in ('relay', 'both') and len(addresses) == 0:
            if content.get('request_id', '') == 'registration':
                if content.get('reply_id', '') != self.address:
                    if 'registration' not in self.data_buffer:
                        self.data_buffer['registration'] = dict()
                    sender = content.get('address', {}).get('sender', ['UNKNOWN'])[0]
                    self.data_buffer['registration'].update({sender: content})
                    target = list(self.callbacks['data'].keys())
                    return self.broadcastRegistry(target=target)
        self.relay(packet, 'data', addresses=addresses)
        if self.role in ('relay', 'both'):
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
        assert callable(callback), f"Invalid callback: {callback}"
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
        if callback_type == 'data' and self.role == 'model':    # Re-broadcast the registry to newly connected views
            self.broadcastRegistry(target=[key])
        elif callback_type == 'data' and self.role == 'relay':  # Prompt all connected models to re-broadcast their registry
            request_keys = list(self.callbacks['request'].keys())
            for key in request_keys:
                _relay = key in self.relays
                _callback = self.unsubscribe('request', key)
                if _callback is not None:
                    self.subscribe(_callback, 'request', key, relay=_relay)
        return
    
    def unsubscribe(self, callback_type: str, address: int|str) -> Callable|None:
        """
        Unsubscribe from a callback
        
        Args:
            callback_type (str): the callback type
            address (int|str): the address
        
        Returns:
            Callable|None: the unsubscribed callback
        """
        assert callback_type in self.callbacks, f"Invalid callback type: {callback_type}"
        key = address
        key = str(key)
        callback = self.callbacks[callback_type].pop(key, None)
        if callback is None:
            logger.warning(f"{key} was not subscribed to {callback_type}")
            return
        if key in self.relays:
            self.relays.remove(key)
        return callback
    
    def setAddress(self, address: int|str):
        """
        Set the address
        
        Args:
            address (int|str): the address
        """
        assert isinstance(address, (int,str)), f"Invalid address: {address}"
        self.address = address
        return
