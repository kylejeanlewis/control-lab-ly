# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
import inspect
import logging
import queue
import threading
import time
from typing import Callable, Protocol, Mapping, Any

# Third-party imports
import requests

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

class Message(Protocol):
    ...

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


class Interpreter:
    def __init__(self):
        return
    
    @staticmethod
    def decodeRequest(request: Message) -> dict[str, Any]:
        logger.error("decodeRequest not implemented")
        return request
    
    @staticmethod
    def encodeData(data: Any) -> Message:
        logger.error("encodeData not implemented")
        return data
    
    @staticmethod
    def encodeRequest(command: Mapping[str, Any]) -> Message:
        logger.error("encodeRequest not implemented")
        request = command
        return request
    
    @staticmethod
    def decodeData(package: Message) -> Any:
        logger.error("decodeData not implemented")
        data = package
        return data
    

class Controller:
    def __init__(self, role: str, interpreter: Interpreter):
        assert role in ('model', 'view', 'both'), f"Invalid role: {role}"
        assert isinstance(interpreter, Interpreter), f"Invalid interpreter: {interpreter}"
        self.role = role
        self.interpreter = interpreter
        
        self.callbacks: dict[str, list[Callable]] = dict(request=[], data=[])
        self.command_queue = TwoTierQueue()
        self.data_buffer = deque()
        self.object_methods: dict[str, ClassMethods] = dict()
        
        # self.receiver_event = threading.Event()
        self.execution_event = threading.Event()
        self.threads = {}
        pass
    
    # Model side
    def receiveRequest(self, request: Message):
        assert self.role in ('model', 'both'), "Only the model can receive requests"
        command = self.interpreter.decodeRequest(request)
        priority = command.pop("priority", False)
        rank = command.pop("rank", None)
        self.command_queue.put(command, priority=priority, rank=rank)
        return
    
    def transmitData(self, data: Any):
        assert self.role in ('model', 'both'), "Only the model can transmit data"
        package = self.interpreter.encodeData(data)
        self.relayData(package)
        return
    
    def register(self, tool: Callable):
        assert self.role in ('model', 'both'), "Only the model can register tools"
        key = id(tool)
        if key in self.object_methods:
            logger.warning(f"{tool.__class__}_{key} already registered.")
            return False
        self.object_methods[key] = self.extractMethods(tool)
        return
    
    def unregister(self, tool: Callable) -> bool:
        assert self.role in ('model', 'both'), "Only the model can unregister tools"
        key = id(tool)
        success = False
        try:
            self.object_methods.pop(key)
            success = True
        except KeyError:
            logger.warning(f"{tool.__class__}_{key} was not registered.")
        return success
    
    @staticmethod
    def extractMethods(tool: Callable) -> ClassMethods:
        methods = {}
        for method in dir(tool):
            if method.startswith('_'):
                continue
            is_method = False
            if inspect.ismethod(getattr(tool, method)):
                is_method = True
            elif isinstance(inspect.getattr_static(tool, method), staticmethod):
                is_method = True
            elif isinstance(inspect.getattr_static(tool, method), classmethod):
                is_method = True
            if not is_method:
                continue
            
            methods[method] = dict()
            signature = inspect.signature(getattr(tool, method))
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
            name = tool.__class__.__name__,
            methods = methods
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
    
    # @staticmethod
    def executeCommand(self, command: Mapping[str, Any]) -> Any:
        logger.error("executeCommand not implemented")
        
        # Insert case for getting and exposing methods
        if command.get('class') == 'Controller' and command.get('method') == 'exposeMethods':
            return self.exposeMethods()
        
        # Implement the command execution logic here
        logger.info(f"Executing command: {command}")
        time.sleep(5)
        data = command
        logger.info(f"Completed command: {command}")
        
        return data
    
    def _loop_execution(self):
        assert self.role in ('model', 'both'), "Only the model can execute commands"
        while self.execution_event.is_set():
            try:
                command = self.command_queue.get(timeout=5)
                if command is not None:
                    data = self.executeCommand(command)
                    self.transmitData(data)
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
                    data = self.executeCommand(command)
                    self.transmitData(data)
                    self.command_queue.task_done()
            except queue.Empty:
                break
            except KeyboardInterrupt:
                break
        self.command_queue.join()
        return
    
    # View side
    def transmitRequest(self, command: Mapping[str, Any], *, priority: bool = False, rank: int = None):
        assert self.role in ('view', 'both'), "Only the view can transmit requests"
        command['priority'] = priority
        command['rank'] = rank
        request = self.interpreter.encodeRequest(command)
        self.relayRequest(request)
        return
    
    def receiveData(self, package: Message):
        assert self.role in ('view', 'both'), "Only the view can receive data"
        data = self.interpreter.decodeData(package)
        self.data_buffer.append(data)
        return
    
    def getMethods(self):
        assert self.role in ('view', 'both'), "Only the view can get methods"
        command = {'class':'Controller', 'method':'exposeMethods'}
        return self.transmitRequest(command)
    
    # Controller side
    def relay(self, message: Message, callback_type:str):
        assert callback_type in self.callbacks, f"Invalid callback type: {callback_type}"
        for callback in self.callbacks[callback_type]:
            callback(message)
        return
    
    def relayRequest(self, request: Message):
        return self.relay(request, 'request')
    
    def relayData(self, package: Message):
        return self.relay(package, 'data')
    
    def subscribe(self, callback: Callable, callback_type: str):
        assert callback_type in self.callbacks, f"Invalid callback type: {callback_type}"
        assert isinstance(callback, Callable), f"Invalid callback: {callback}"
        self.callbacks[callback_type].append(callback)
        return
    
    def unsubscribe(self, callback: Callable, callback_type: str):
        if callback in self.callbacks[callback_type]:
            self.callbacks[callback_type].remove(callback)
        return
    
