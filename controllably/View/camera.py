# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
from collections import deque
from copy import deepcopy
from datetime import datetime
import logging
import queue
from string import Formatter
import threading
import time
from types import SimpleNamespace
from typing import Any, NamedTuple, Callable

# Third party imports
import cv2 # pip install opencv-python
import numpy as np
import parse
import PIL

# Local application imports
from .placeholder import PLACEHOLDER

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class Camera:
        _default_flags: SimpleNamespace = SimpleNamespace(verbose=False, connected=False, simulation=False)
    def __init__(self, 
        *, 
        connection_details:dict|None = None, 
        init_timeout:int = 1, 
        data_type: NamedTuple = NamedTuple("Data", [("data", str)]),
        read_format:str = "{data}\n",
        write_format:str = "{data}\n",
        simulation:bool = False, 
        verbose:bool = False, 
        **kwargs
    ):
        # Connection attributes
        self.connection: Any|None = None
        self.connection_details = dict() if connection_details is None else connection_details
        self.flags = deepcopy(self._default_flags)
        self.init_timeout = init_timeout
        self.flags.simulation = simulation
        
        # IO attributes
        self.data_type = data_type
        self.read_format = read_format
        self.write_format = write_format
        fields = set([field for _, field, _, _ in Formatter().parse(read_format) if field and not field.startswith('_')])
        assert set(data_type._fields) == fields, "Ensure data type fields match read format fields"
        
        # Streaming attributes
        self.buffer = deque()
        self.data_queue = queue.Queue()
        self.show_event = threading.Event()
        self.stream_event = threading.Event()
        self.threads = dict()
        
        # Logging attributes
        self._logger = logger.getChild(f"{self.__class__.__name__}_{id(self)}")
        self._logger.addHandler(logging.StreamHandler())
        self.verbose = verbose
        return
    
    @property
    def is_connected(self) -> bool:
        """Whether the device is connected"""
        connected = self.flags.connected if self.flags.simulation else self.checkDeviceConnection()
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
    def checkDeviceConnection(self) -> bool:
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
    def checkDeviceBuffer(self) -> bool:
        """Check the connection buffer"""
        ...
        raise NotImplementedError
    
    def clear(self):
        """Clear the input and output buffers"""
        self.stopStream()
        self.buffer = deque()
        self.data_queue = queue.Queue()
        if self.flags.simulation:
            return
        ... # Replace with specific implementation to clear input and output buffers
        return

    def read(self) -> str|None:
        """Read data from the device"""
        data = None
        try:
            data = ... # Replace with specific implementation
            data = data.strip()
            self._logger.debug(f"Received: {data!r}")
        except ... as e: # Replace with specific exception
            self._logger.debug(f"Failed to receive data")
        except KeyboardInterrupt:
            self._logger.debug("Received keyboard interrupt")
            self.disconnect()
        return data
    
    def readAll(self) -> list[str]|None:
        """Read all data from the device"""
        delimiter = self.read_format.replace(self.read_format.rstrip(), '')
        data = ''
        try:
            while True:
                out = ... # Replace with specific implementation
                data += out
                if not out:
                    break
        except ... as e: # Replace with specific exception
            self._logger.debug(f"Failed to receive data")
            self._logger.debug(e)
        except KeyboardInterrupt:
            self._logger.debug("Received keyboard interrupt")
            self.disconnect()
        data = data.strip()
        self._logger.debug(f"Received: {data!r}")
        return data.split(delimiter)
    
    def write(self, data:str) -> bool:
        """Write data to the device"""
        assert isinstance(data, str), "Ensure data is a string"
        try:
            ... # Replace with specific implementation
            self._logger.debug(f"Sent: {data!r}")
        except ... as e: # Replace with specific exception
            self._logger.debug(f"Failed to send: {data!r}")
            return False
        return True
    
    def poll(self, data:str|None = None) -> str|None:
        out = None
        if data is not None:
            ret = self.write(data)
        if data is None or ret:
            out: str = self.read()
        return out
    
    def processInput(self, 
        data: Any = None,
        format: str|None = None,
        **kwargs
    ) -> str|None:
        """Process the input"""
        if data is None:
            return None
        format = format or self.write_format
        assert isinstance(format, str), "Ensure format is a string"
        
        kwargs.update(dict(data=data))
        processed_data = format.format(**kwargs)
        return processed_data
    
    def processOutput(self, 
        data: str, 
        format: str|None = None, 
        data_type: NamedTuple|None = None, 
        timestamp: datetime|None = None,
        *,
        condition: Callable[[Any,datetime], bool]|None = None
    ) -> tuple[Any, datetime|None]:
        """Process the output"""
        format = format or self.read_format
        format = format.strip()
        data_type = data_type or self.data_type
        fields = set([field for _, field, _, _ in Formatter().parse(format) if field and not field.startswith('_')])
        assert set(data_type._fields) == fields, "Ensure data type fields match read format fields"
        
        parse_out = parse.parse(format, data)
        if parse_out is None:
            self._logger.warning(f"Failed to parse data: {data!r}")
            return None, timestamp
        parsed = {k:v for k,v in parse_out.named.items() if not k.startswith('_')}
        for key, value in data_type.__annotations__.items():
            try:
                if value == int and not parsed[key].isnumeric():
                    parsed[key] = float(parsed[key])
                elif value == bool:
                    parsed[key] = parsed[key].lower() not in ['false', '0', 'no']
                parsed[key] = value(parsed[key])
            except ValueError:
                self._logger.warning(f"Failed to convert {key}: {parsed[key]} to type {value}")
                # parsed[key] = None
                return None ,timestamp
        processed_data = data_type(**parsed) 
        
        if self.show_event.is_set():
            print(processed_data)
        if callable(condition) and condition(processed_data, timestamp):
            self.stopStream()
        return processed_data, timestamp
    
    def query(self, 
        data: Any, 
        multi_out: bool = True,
        *, 
        timeout: int|float = 1,
        format_in: str|None = None, 
        format_out: str|None = None,
        data_type: NamedTuple|None = None,
        timestamp: bool = False,
        **kwargs
    ) -> Any | None:
        """Query the device"""
        data_type: NamedTuple = data_type or self.data_type
        # if self.flags.simulation:
        #     field_types = data_type.__annotations__
        #     data_defaults = data_type._field_defaults
        #     defaults = [data_defaults.get(f, ('' if t==str else 0)) for f,t in field_types.items()]
        #     data_out = data_type(*defaults)
        #     response = (data_out, datetime.now()) if timestamp else data_out
        #     return [response] if multi_out else response
        
        data_in = self.processInput(data, format_in, **kwargs)
        if not multi_out:
            raw_out = self.poll(data_in)
            if raw_out is None:
                return (None, now) if timestamp else None
            out, now = self.processOutput(raw_out, format_out, data_type)
            return (out, now) if timestamp else out
        
        all_data = []
        ret = self.write(data_in) if data_in is not None else True
        if not ret:
            return all_data
        start_time = time.perf_counter()
        while True:
            if time.perf_counter() - start_time > timeout:
                break
            raw_out = self.read()
            if raw_out is None or raw_out.strip() == '':
                continue
            start_time = time.perf_counter()
            out, now = self.processOutput(raw_out, format_out, data_type)
            data_out = (out, now) if timestamp else out
            all_data.append(data_out)
            if not self.checkDeviceBuffer():
                break
        return all_data

    # Streaming methods
    def showStream(self, on: bool):
        """Show the stream"""
        _ = self.show_event.set() if on else self.show_event.clear()
        return
    
    def startStream(self, 
        data: str|None = None, 
        buffer: deque|None = None,
        *, 
        format: str|None = None, 
        data_type: NamedTuple|None = None,
        show: bool = False,
        sync_start: threading.Barrier|None = None
    ):
        """Start the stream"""
        sync_start = sync_start or threading.Barrier(2, timeout=2)
        assert isinstance(sync_start, threading.Barrier), "Ensure sync_start is a threading.Barrier"
        
        self.stream_event.set()
        self.threads['stream'] = threading.Thread(
            target=self._loop_stream, 
            kwargs=dict(data=data, sync_start=sync_start), 
            daemon=True
        )
        self.threads['process'] = threading.Thread(
            target=self._loop_process_data, 
            kwargs=dict(buffer=buffer, format=format, data_type=data_type, sync_start=sync_start), 
            daemon=True
        )
        self.showStream(show)
        self.threads['stream'].start()
        self.threads['process'].start()
        return
    
    def stopStream(self):
        """Stop the stream"""
        self.stream_event.clear()
        self.showStream(False)
        for thread in self.threads.values():
            _ = thread.join() if isinstance(thread, threading.Thread) else None
        return
    
    def stream(self, 
        on:bool, 
        data: str|None = None, 
        buffer: deque|None = None, 
        *,
        sync_start:threading.Barrier|None = None,
        **kwargs
    ):
        """Toggle the stream"""
        return self.startStream(data=data, buffer=buffer, sync_start=sync_start, **kwargs) if on else self.stopStream()
    
    def _loop_process_data(self, 
        buffer: deque|None = None,
        format:str|None = None, 
        data_type: NamedTuple|None = None, 
        sync_start:threading.Barrier|None = None
    ) -> Any:
        if buffer is None:
            buffer = self.buffer
        assert isinstance(buffer, deque), "Ensure buffer is a deque"
        if isinstance(sync_start, threading.Barrier):
            sync_start.wait()
        
        while self.stream_event.is_set():
            try:
                out, now = self.data_queue.get(timeout=5)
                out, now = self.processOutput(out, format=format, data_type=data_type, timestamp=now)
                if out is not None:
                    buffer.append((out, now))
                self.data_queue.task_done()
            except queue.Empty:
                time.sleep(0.01)
                continue
            except KeyboardInterrupt:
                self.stream_event.clear()
                break
        time.sleep(1)
        
        while self.data_queue.qsize() > 0:
            try:
                out, now = self.data_queue.get(timeout=1)
                out, now = self.processOutput(out, format=format, data_type=data_type, timestamp=now)
                if out is not None:
                    buffer.append((out, now))
                self.data_queue.task_done()
            except queue.Empty:
                break
            except KeyboardInterrupt:
                break
        self.data_queue.join()
        return
    
    def _loop_stream(self,
        data:str|None = None, 
        sync_start:threading.Barrier|None = None
    ):
        """Stream loop"""
        if isinstance(sync_start, threading.Barrier):
            sync_start.wait()
        
        while self.stream_event.is_set():
            try:
                out = self.poll(data)
                now = datetime.now()
                self.data_queue.put((out, now), block=False)
            except queue.Full:
                time.sleep(0.01)
                continue
            except KeyboardInterrupt:
                self.stream_event.clear()
                break
        return

