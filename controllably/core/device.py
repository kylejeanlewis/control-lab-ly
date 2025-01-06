# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
from copy import deepcopy
import logging
import queue
import threading
import time
from types import SimpleNamespace
from typing import Any

_logger = logging.getLogger("controllably.core")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.addFilter(logging.Filter(__name__+'.'))
logger.addHandler(handler)

class BaseDevice:
    
    _default_flags: SimpleNamespace = SimpleNamespace(verbose=False, connected=False, simulation=False)
    def __init__(self, *args, 
        connection_details:dict = dict(), 
        init_timeout:int = 1, 
        simulation:bool = False, 
        verbose:bool = False, 
        **kwargs
    ):
        # Connection attributes
        self.connection: Any|None = None
        self.connection_details = connection_details
        self.flags = deepcopy(self._default_flags)
        self.init_timeout = init_timeout
        self.flags.simulation = simulation
        
        # IO attributes
        self.read_format = kwargs.get("read_format", "{data}\n")
        self.write_format = kwargs.get("write_format", "{data}\n")
        
        # Streaming attributes
        self.buffer = list()
        self.queue = queue.Queue()
        self.streaming = threading.Event()
        self.threads = dict()
        
        # Logging attributes
        self._logger = logger.getChild(f"{self.__class__.__name__}_{id(self)}")
        self._logger.addHandler(logging.StreamHandler())
        self.verbose = verbose
        return
    
    @property
    def is_connected(self) -> bool:
        """Whether the device is connected"""
        connected = self.flags.connected if self.flags.simulation else self.checkConnection()
        return connected
    
    @property
    def verbose(self) -> bool:
        """Verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        level = logging.DEBUG if value else logging.INFO
        for handler in self._logger.handlers:
            if not isinstance(handler, logging.StreamHandler):
                continue
            handler.setLevel(level)
        return
    
    # Connection methods
    def checkConnection(self) -> bool:
        """Check the connection to the device"""
        ...
        raise NotImplementedError
    
    def connect(self):
        """Connect to the device"""
        if self.is_connected:
            return
        try:
            ... # Replace with specific implementation
        except ... as e:
            self._logger.error(f"Failed to connect to {...}") # Replace with specific log message
            self._logger.debug(e)
        else:
            self._logger.info(f"Connected to {...}") # Replace with specific log message
            time.sleep(self.init_timeout)
        self.flags.connected = True
        return

    def disconnect(self):
        """Disconnect from the device"""
        if not self.is_connected:
            return
        try:
            ... # Replace with specific implementation
        except ... as e: # Replace with specific exception
            self._logger.error(f"Failed to disconnect from {...}") # Replace with specific log message
            self._logger.debug(e)
        else:
            self._logger.info(f"Disconnected from {...}") # Replace with specific log message
        self.flags.connected = False
        return
    
    # IO methods
    def clear(self):
        """Clear the input and output buffers"""
        self.stopStream()
        self.buffer = list()
        self.queue = queue.Queue()
        if self.flags.simulation:
            return
        ... # Replace with specific implementation to clear input and output buffers
        return

    def read(self) -> str|None:
        """Read data from the device"""
        data = None
        try:
            data = ... # Replace with specific implementation
            self._logger.debug(f"Received: {data!r}")
        except ... as e: # Replace with specific exception
            self._logger.debug(f"Failed to receive data")
        return data
    
    def write(self, data:str) -> bool:
        """Write data to the device"""
        assert isinstance(data, str), "Ensure data is a string"
        data = ... # Replace with specific formatting
        try:
            ... # Replace with specific implementation
            self._logger.debug(f"Sent: {data!r}")
        except ... as e: # Replace with specific exception
            self._logger.debug(f"Failed to send: {data!r}")
            return False
        return True
    
    def poll(self, data:str|None = None) -> str:
        if data is not None:
            ret = self.write(data)
        if data is None or ret:
            out: str = self.read()
        return out
    
    def process_data(self, data:str) -> Any:
        """Process the data"""
        ... # Replace with specific implementation
        return data
    
    def query(self, data:Any, lines:bool = True) -> Any:
        """Query the device"""
        ... # Replace with specific implementation
        return self.process_data(self.poll(data))

    # Streaming methods
    def startStream(self, sync_start:threading.Event|None = None):
        """Start the stream"""
        self.streaming.set()
        self.threads['stream'] = threading.Thread(target=self._loop_stream, args=[sync_start], daemon=True)
        self.threads['process'] = threading.Thread(target=self._loop_process_data, args=[sync_start], daemon=True)
        
        self.threads['stream'].start()
        self.threads['process'].start()
        return
    
    def stopStream(self):
        """Stop the stream"""
        self.streaming.clear()
        for thread in self.threads.values():
            _ = thread.join() if isinstance(thread, threading.Thread) else None
        return
    
    def toggleStream(self, on:bool, sync_start:threading.Event|None = None):
        """Toggle the stream"""
        return self.startStream(sync_start) if on else self.stopStream()
    
    def _loop_process_data(self, sync_start:threading.Event|None = None) -> Any:
        while isinstance(sync_start, threading.Event) and not sync_start.is_set():
            time.sleep(0.01)
        
        while self.streaming.is_set():
            try:
                out = self.queue.get(block=False)
                self.process_data(out)
                self.queue.task_done()
            except queue.Empty:
                time.sleep(0.01)
                continue
            except KeyboardInterrupt:
                self.streaming.clear()
                break
        time.sleep(1)
        
        while not self.queue.empty():
            try:
                out = self.queue.get(timeout=1)
                self.process_data(out)
                self.queue.task_done()
            except queue.Empty:
                break
            except KeyboardInterrupt:
                break
        self.queue.join()
        return
    
    def _loop_stream(self, data:str|None = None, sync_start:threading.Event|None = None):
        """Stream loop"""
        while isinstance(sync_start, threading.Event) and not sync_start.is_set():
            time.sleep(0.01)
        
        while self.streaming.is_set():
            try:
                out = self.poll(data)
                self.queue.put(out, block=False)
            except queue.Full:
                time.sleep(0.01)
                continue
            except KeyboardInterrupt:
                self.streaming.clear()
                break
        return