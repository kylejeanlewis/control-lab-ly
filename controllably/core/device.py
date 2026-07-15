# -*- coding: utf-8 -*-
""" 
This module provides base classes for device connections.

Attributes:
    READ_FORMAT (str): default read format for device connections
    WRITE_FORMAT (str): default write format for device connections
    Data (NamedTuple): default data type for device connections

## Classes:
    `Device`: Protocol for device connection classes
    `StreamingDevice`: Protocol for streaming device connection classes
    `TimedDeviceMixin`: Mixin class for timed device operations
    `BaseDevice`: Base class for device connections
    `SerialDevice`: Class for serial device connections
    `SocketDevice`: Class for socket device connections
    `WebsocketDevice`: Class for WebSocket device connections

<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
from collections import deque
from copy import deepcopy
from datetime import datetime
import logging
import queue
import socket
from string import Formatter
import threading
import time
from types import SimpleNamespace
from typing import Any, NamedTuple, Protocol, Callable, Type

# Third party imports
import parse
import serial
import websockets
from websockets.sync import client

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)

READ_FORMAT = "{data}\n"
WRITE_FORMAT = "{data}\n"
Data = NamedTuple("Data", [("data", str)])

class Device(Protocol):
    connection: Any|None
    connection_details: dict
    is_connected: bool
    verbose: bool
    def clear(self):...
    def connect(self):...
    def disconnect(self):...
    def processInput(self, data:Any, format_in:str, **kwargs) -> str|None:...
    def processOutput(self, data:str, format_out:str, data_type:NamedTuple, timestamp: datetime|None, **kwargs) -> tuple[Any, datetime]:...
    def query(self, data:Any, multi_out:bool = True, **kwargs) -> Any|None:...
    def read(self) -> str|None:...
    def write(self, data:str) -> bool:...


class StreamingDevice(Protocol):
    connection: Any|None
    connection_details: dict
    is_connected: bool
    verbose: bool
    buffer: deque
    data_type: NamedTuple
    data_queue: queue.Queue
    show_event: threading.Event
    stream_event: threading.Event
    threads: dict
    def clear(self):...
    def clearDeviceBuffer(self):...
    def connect(self):...
    def disconnect(self):...
    def processInput(self, data:Any, format_in:str|None=None, **kwargs) -> str|None:...
    def processOutput(self, data:str, format_out:str|None=None, data_type:NamedTuple|None=None, timestamp: datetime|None=None, **kwargs) -> tuple[Any, datetime]:...
    def query(self, data:Any, multi_out:bool = True, **kwargs) -> Any|None:...
    def read(self) -> str|None:...
    def write(self, data:str) -> bool:...
    def startStream(self, data:str|None = None, buffer:deque|None = None, **kwargs):...
    def stopStream(self):...
    def stream(self, on:bool, data:str|None = None, buffer:deque|None = None, **kwargs):...
    def showStream(self, on:bool):...


class TimedDeviceMixin:
    """ 
    Mixin class for timed device operations
    
    ### Methods:
        `stopTimer`: stop a timer
        `setValue`: set a value
        `setValueDelayed`: set a value after a delay
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        return
    
    def stopTimer(self, timer: threading.Timer|None = None, event: threading.Event|None = None):
        """ 
        Stop a timer
        
        Args:
            timer (threading.Timer|None, optional): timer to stop. Defaults to None.
            event (threading.Event|None, optional): event to clear. Defaults to None
        """
        if isinstance(timer, threading.Timer):
            timer.cancel()
        if isinstance(event, threading.Event):
            event.clear()
        return
        
    def setValue(self, value: Any, event: threading.Event|None = None, **kwargs) -> bool:
        """ 
        Set a value
        
        Args:
            value (Any): value to set
            event (threading.Event|None, optional): event to set or clear. Defaults to None.
            
        Returns:
            bool: whether the value was set
        """
        ...
        if isinstance(event, threading.Event):
            _ = event.clear() if event.is_set() else event.set()
        raise NotImplementedError
    
    def setValueDelayed(self, 
        duration: int|float,
        initial: Any|None = None, 
        final: Any|None = None,
        blocking: bool = True, 
        *, 
        event: threading.Event|None = None,
        **kwargs
    ) -> threading.Timer|None:
        """ 
        Set a value after a delay
        
        Args:
            duration (int|float): duration of the delay
            initial (Any|None, optional): initial value. Defaults to None.
            final (Any|None, optional): final value. Defaults to None.
            blocking (bool, optional): whether to block the main thread. Defaults to True.
            event (threading.Event|None, optional): event to set or clear. Defaults to None.
            
        Returns:
            threading.Timer|None: timer object if blocking is False
        """
        assert duration >= 0, "Ensure duration is a non-negative number"
        success = self.setValue(initial, **kwargs)
        if not success:
            return
        event.set()
        if blocking:
            time.sleep(duration)
            self.stopTimer(event=event)
            self.setValue(final, **kwargs)
            return
        timer = threading.Timer(duration, self.setValue, args=(final,event), kwargs=kwargs)
        timer.start()
        return timer
    

class BaseDevice:
    """
    BaseDevice provides an interface for handling device connections
    
    ### Constructor:
        `connection_details` (dict|None, optional): connection details for the device. Defaults to None.
        `init_timeout` (int, optional): timeout for initialization. Defaults to 1.
        `data_type` (NamedTuple, optional): data type for the device. Defaults to Data.
        `read_format` (str, optional): read format for the device. Defaults to READ_FORMAT.
        `write_format` (str, optional): write format for the device. Defaults to WRITE_FORMAT.
        `simulation` (bool, optional): whether to simulate the device. Defaults to False.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
        
    ### Attributes and properties:
        `connection` (Any|None): connection object for the device
        `connection_details` (dict): connection details for the device
        `flags` (SimpleNamespace[str, bool]): flags for the device
        `init_timeout` (int): timeout for initialization
        `data_type` (NamedTuple): data type for the device
        `read_format` (str): read format for the device
        `write_format` (str): write format for the device
        `eol` (str): end of line character for the read format
        `buffer` (deque): buffer for storing streamed data
        `data_queue` (queue.Queue): queue for storing processed data
        `show_event` (threading.Event): event for showing streamed data
        `stream_event` (threading.Event): event for controlling streaming
        `threads` (dict): dictionary of threads used in streaming
        
    ### Methods:
        `clear`: clear the input and output buffers, and reset the data queue and buffer
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `checkDeviceConnection`: check the connection to the device
        `checkDeviceBuffer`: check the connection buffer
        `clearDeviceBuffer`: clear the device input and output buffers
        `read`: read data from the device
        `readAll`: read all data from the device
        `write`: write data to the device
        `poll`: poll the device (i.e. write and read data)
        `processInput`: process the input data
        `processOutput`: process the output data
        `query`: query the device (i.e. write and read data)
        `startStream`: start the stream
        `stopStream`: stop the stream
        `stream`: toggle the stream
        `showStream`: show the stream
    """
    
    _default_flags: SimpleNamespace = SimpleNamespace(verbose=False, connected=False, simulation=False)
    def __init__(self, 
        *, 
        connection_details:dict|None = None, 
        init_timeout:int = 1, 
        data_type: NamedTuple =  Data,
        read_format:str = READ_FORMAT,
        write_format:str = WRITE_FORMAT,
        simulation:bool = False, 
        verbose:bool = False, 
        **kwargs
    ):
        """
        Initialize BaseDevice class
        
        Args:
            connection_details (dict|None, optional): connection details for the device. Defaults to None.
            init_timeout (int, optional): timeout for initialization. Defaults to 1.
            data_type (NamedTuple, optional): data type for the device. Defaults to Data.
            read_format (str, optional): read format for the device. Defaults to READ_FORMAT.
            write_format (str, optional): write format for the device. Defaults to WRITE_FORMAT.
            simulation (bool, optional): whether to simulate the device. Defaults to False.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
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
        self.eol = self.read_format.replace(self.read_format.rstrip(), '')
        fields = set([field for _, field, _, _ in Formatter().parse(read_format) if field and not field.startswith('_')])
        assert set(data_type._fields) == fields, "Ensure data type fields match read format fields"
        
        # Streaming attributes
        self.buffer = deque()
        self.data_queue = queue.Queue()
        self.show_event = threading.Event()
        self.stream_event = threading.Event()
        self.threads = dict()
        
        # Logging attributes
        self._logger = logger.getChild(f"{self.__class__.__name__}.{id(self)}")
        self.verbose = verbose
        return
    
    def __del__(self):
        self.disconnect()
        return
    
    def __enter__(self):
        """Context manager enter method"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit method"""
        self.disconnect()
        return False
    
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
        CustomLevelFilter().setModuleLevel(self._logger.name, level)
        return
    
    # Connection methods
    def checkDeviceConnection(self) -> bool:
        """
        Check the connection to the device
        
        Returns:
            bool: whether the device is connected
        """
        if hasattr(self.connection, 'is_open'):
            return self.connection.is_open() # Replace with specific implementation
        return self.flags.connected # Replace with specific implementation
    
    def connect(self):
        """Connect to the device"""
        if self.is_connected:
            return
        connection_details = repr(self.connection_details) if self.connection_details else '{...}'
        try:
            self.connection.open() # Replace with specific implementation
        except Exception as e: # Replace with specific exception
            self._logger.error(f"Failed to connect to {connection_details}") # Replace with specific log message
            self._logger.debug(e)
        else:
            self._logger.info(f"Connected to {connection_details}") # Replace with specific log message
            time.sleep(self.init_timeout)
        self.flags.connected = True
        return

    def disconnect(self):
        """Disconnect from the device"""
        if not self.is_connected:
            return
        self.stopStream()
        connection_details = repr(self.connection_details) if self.connection_details else '{...}'
        try:
            self.connection.close() # Replace with specific implementation
        except Exception as e: # Replace with specific exception
            self._logger.error(f"Failed to disconnect from {connection_details}") # Replace with specific log message
            self._logger.debug(e)
        else:
            self._logger.info(f"Disconnected from {connection_details}") # Replace with specific log message
        self.flags.connected = False
        return
    
    # IO methods
    def checkDeviceBuffer(self) -> bool:
        """
        Check the connection buffer
        
        Returns:
            bool: whether there is data in the connection buffer
        """
        return self.connection.in_waiting() # Replace with specific implementation
    
    def clearDeviceBuffer(self):
        """Clear the device input and output buffers"""
        ... # Replace with specific implementation to clear input and output buffers
        return
    
    def clear(self):
        """Clear the input and output buffers, and reset the data queue and buffer"""
        self.stopStream()
        self.buffer = deque()
        self.data_queue = queue.Queue()
        if self.flags.simulation:
            return
        self.clearDeviceBuffer()
        # time.sleep(0.01)
        return

    def read(self) -> str:
        """
        Read data from the device
        
        Returns:
            str|None: data read from the device
        """
        data = ''
        try:
            data = self.connection.read().decode("utf-8", "replace") # Replace with specific implementation
            data = data.strip()
            self._logger.debug(f"Received: {data!r}")
        except Exception: # Replace with specific exception
            self._logger.debug("Failed to receive data")
        except KeyboardInterrupt:
            self._logger.debug("Received keyboard interrupt")
            self.disconnect()
        return data
    
    def readAll(self) -> list[str]:
        """
        Read all data from the device
        
        Returns:
            list[str]|None: data read from the device
        """
        delimiter = self.eol
        data = ''
        try:
            while True:
                out = self.connection.read_all().decode("utf-8", "replace") # Replace with specific implementation
                data += out
                if not out:
                    break
        except Exception as e: # Replace with specific exception
            self._logger.debug("Failed to receive data")
            self._logger.debug(e)
        except KeyboardInterrupt:
            self._logger.debug("Received keyboard interrupt")
            self.disconnect()
        data = data.strip()
        self._logger.debug(f"Received: {data!r}")
        return [d for d in data.split(delimiter) if len(d)]
    
    def write(self, data:str) -> bool:
        """
        Write data to the device
        
        Args:
            data (str): data to write to the device
            
        Returns:
            bool: whether the data was written successfully
        """
        assert isinstance(data, str), "Ensure data is a string"
        try:
            self.connection.write(data.encode('utf-8')) # Replace with specific implementation
            self._logger.debug(f"Sent: {data!r}")
        except Exception: # Replace with specific exception
            self._logger.debug(f"Failed to send: {data!r}")
            return False
        return True
    
    def poll(self, data:str|None = None) -> str:
        """
        Poll the device
        
        Args:
            data (str|None, optional): data to write to the device. Defaults to None.
            
        Returns:
            str|None: data read from the device
        """
        out = ''
        if data is not None:
            ret = self.write(data)
        if data is None or ret:
            out: str = self.read()
        return out
    
    def processInput(self, 
        data: Any = None,
        format_in: str|None = None,
        **kwargs
    ) -> str|None:
        """
        Process the input
        
        Args:
            data (Any, optional): data to process. Defaults to None.
            format_in (str|None, optional): format for the data. Defaults to None.
            
        Returns:
            str|None: processed input data
        """
        if data is None:
            return None
        format_in = format_in or self.write_format
        assert isinstance(format_in, str), "Ensure format is a string"
        
        kwargs.update(dict(data=data))
        processed_data = format_in.format(**kwargs)
        return processed_data
    
    def processOutput(self, 
        data: str, 
        format_out: str|None = None, 
        data_type: NamedTuple|None = None, 
        timestamp: datetime|None = None
    ) -> tuple[Any, datetime|None]:
        """
        Process the output
        
        Args:
            data (str): data to process
            format_out (str|None, optional): format for the data. Defaults to None.
            data_type (NamedTuple|None, optional): data type for the data. Defaults to None.
            timestamp (datetime|None, optional): timestamp for the data. Defaults to None.
            
        Returns:
            tuple[Any, datetime|None]: processed output data and timestamp
        """
        format_out = format_out or self.read_format
        format_out = format_out.strip()
        data_type = data_type or self.data_type
        fields = set([field for _, field, _, _ in Formatter().parse(format_out) if field and not field.startswith('_')])
        assert set(data_type._fields) == fields, "Ensure data type fields match read format fields"
        
        try:
            parse_out = parse.parse(format_out, data)
        except TypeError:
            if data:
                self._logger.warning(f"Failed to parse data: {data!r}")
            # self.clearDeviceBuffer()
            # time.sleep(0.01)
            return None, timestamp
        if parse_out is None:
            if data:
                self._logger.warning(f"Failed to parse data: {data!r}")
            # self.clearDeviceBuffer()
            # time.sleep(0.01)
            return None, timestamp
        parsed = {k:v for k,v in parse_out.named.items() if not k.startswith('_')}
        for key, value in data_type.__annotations__.items():
            try:
                if value is int and not parsed[key].isnumeric():
                    parsed[key] = float(parsed[key])
                elif value is bool:
                    parsed[key] = parsed[key].lower() not in ['false', '0', 'no']
                parsed[key] = value(parsed[key])
            except ValueError:
                self._logger.warning(f"Failed to convert {key}: {parsed[key]} to type {value}")
                # self.clearDeviceBuffer()
                # time.sleep(0.01)
                # parsed[key] = None
                return None ,timestamp
        processed_data = data_type(**parsed) 
        
        if self.show_event.is_set():
            print(processed_data)
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
        """
        Query the device
        
        Args:
            data (Any): data to query
            multi_out (bool, optional): whether to return multiple outputs. Defaults to True.
            timeout (int|float, optional): timeout for the query. Defaults to 1.
            format_in (str|None, optional): format for the input data. Defaults to None.
            format_out (str|None, optional): format for the output data. Defaults to None.
            data_type (NamedTuple|None, optional): data type for the data. Defaults to None.
            timestamp (bool, optional): whether to return the timestamp. Defaults to False.
            
        Returns:
            Any|None: queried data
        """
        data_type: NamedTuple = data_type or self.data_type
        data_in = self.processInput(data, format_in, **kwargs)
        now = datetime.now() if timestamp else None
        if not multi_out:
            raw_out = self.poll(data_in)
            if raw_out == '':
                return (None, now) if timestamp else None
            out, now = self.processOutput(raw_out, format_out, data_type, now)
            return (out, now) if timestamp else out
        
        all_data = []
        ret = self.write(data_in) if data_in is not None else True
        if not ret:
            return all_data
        start_time = time.perf_counter()
        while True:
            if time.perf_counter() - start_time > timeout:
                break
            raw_out = self.readAll()
            now = datetime.now() if timestamp else None
            start_time = time.perf_counter()
            
            processed_out = [self.processOutput(out, format_out, data_type, now) for out in raw_out]
            processed_out = [(out, now) for out, now in processed_out if out is not None]
            all_data.extend([(out, now) if timestamp else out for out,now in processed_out])
            if not self.checkDeviceBuffer():
                break
        return all_data

    # Streaming methods
    def showStream(self, on: bool):
        """
        Show the stream
        
        Args:
            on (bool): whether to show the stream
        """
        _ = self.show_event.set() if on else self.show_event.clear()
        return
    
    def startStream(self, 
        data: str|None = None, 
        buffer: deque|None = None,
        *, 
        format_out: str|None = None, 
        data_type: NamedTuple|None = None,
        show: bool = False,
        sync_start: threading.Barrier|None = None,
        split_stream: bool = True,
        callback: Callable[[str],Any]|None = None
    ):
        """
        Start the stream
        
        Args:
            data (str|None, optional): data to stream. Defaults to None.
            buffer (deque|None, optional): buffer to store the streamed data. Defaults to None.
            format_out (str|None, optional): format for the data. Defaults to None.
            data_type (NamedTuple|None, optional): data type for the data. Defaults to None.
            show (bool, optional): whether to show the stream. Defaults to False.
            sync_start (threading.Barrier|None, optional): synchronization barrier. Defaults to None.
            split_stream (bool, optional): whether to split the stream and data processing threads. Defaults to True.
            callback (Callable[[str],Any]|None, optional): callback function to call with the streamed data. Defaults to None.
        """
        sync_start = sync_start or threading.Barrier(2, timeout=2)
        assert isinstance(sync_start, threading.Barrier), "Ensure sync_start is a threading.Barrier"
        if self.stream_event.is_set():
            self.showStream(show)
            return
        self.stream_event.set()
        if split_stream:
            self.threads['stream'] = threading.Thread(
                target=self._loop_stream, 
                args=(data,sync_start),
                kwargs=dict(callback=callback),
                daemon=True
            )
            self.threads['process'] = threading.Thread(
                target=self._loop_process_data, 
                kwargs=dict(buffer=buffer, format_out=format_out, data_type=data_type, sync_start=sync_start), 
                daemon=True
            )
        else:
            self.threads['stream'] = threading.Thread(
                target=self._loop_stream, 
                args=(data,),
                kwargs=dict(buffer=buffer, format_out=format_out, data_type=data_type, split_stream=split_stream, callback=callback), 
                daemon=True
            )
        self.showStream(show)
        self.threads['stream'].start()
        if split_stream:
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
        split_stream: bool = True,
        callback: Callable[[str],Any]|None = None,
        **kwargs
    ):
        """
        Toggle the stream
        
        Args:
            on (bool): whether to start or stop the stream
            data (str|None, optional): data to stream. Defaults to None.
            buffer (deque|None, optional): buffer to store the streamed data. Defaults to None.
            sync_start (threading.Barrier|None, optional): synchronization barrier. Defaults to None.
            split_stream (bool, optional): whether to split the stream and data processing threads. Defaults to True.
            callback (Callable[[str],Any]|None, optional): callback function to call with the streamed data. Defaults to None.
        """
        return self.startStream(data=data, buffer=buffer, sync_start=sync_start, split_stream=split_stream, callback=callback, **kwargs) if on else self.stopStream()
    
    def _loop_process_data(self, 
        buffer: deque|None = None,
        format_out: str|None = None, 
        data_type: NamedTuple|None = None, 
        sync_start: threading.Barrier|None = None
    ):
        """ 
        Process the data
        
        Args:
            buffer (deque|None, optional): buffer to store the streamed data. Defaults to None.
            format_out (str|None, optional): format for the data. Defaults to None.
            data_type (NamedTuple|None, optional): data type for the data. Defaults to None.
            sync_start (threading.Barrier|None, optional): synchronization barrier. Defaults to None.
        """
        if buffer is None:
            buffer = self.buffer
        assert isinstance(buffer, deque), "Ensure buffer is a deque"
        if isinstance(sync_start, threading.Barrier):
            sync_start.wait()
        
        while self.stream_event.is_set():
            try:
                out, now = self.data_queue.get(timeout=5)
                out, now = self.processOutput(out, format_out=format_out, data_type=data_type, timestamp=now)
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
                out, now = self.processOutput(out, format_out=format_out, data_type=data_type, timestamp=now)
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
        sync_start:threading.Barrier|None = None,
        *,
        buffer: deque|None = None,
        format_out: str|None = None, 
        data_type: NamedTuple|None = None,
        split_stream: bool = True,
        callback: Callable[[str],Any]|None = None
    ):
        """
        Stream loop
        
        Args:
            data (str|None, optional): data to stream. Defaults to None.
            sync_start (threading.Barrier|None, optional): synchronization barrier. Defaults to None.
            buffer (deque|None, optional): buffer to store the streamed data. Defaults to None.
            format_out (str|None, optional): format for the data. Defaults to None.
            data_type (NamedTuple|None, optional): data type for the data. Defaults to None.
            split_stream (bool, optional): whether to split the stream and data processing threads. Defaults to True.
            callback (Callable[[str],Any]|None, optional): callback function to call with the streamed data. Defaults to None.
        """
        if not split_stream:
            if buffer is None:
                buffer = self.buffer
            assert isinstance(buffer, deque), "Ensure buffer is a deque"
        if isinstance(sync_start, threading.Barrier):
            sync_start.wait()
        if not callable(callback):
            def callback(_):
                return None
        
        while self.stream_event.is_set():
            try:
                out = self.poll(data)
                now = datetime.now()
                if split_stream:
                    self.data_queue.put((out, now), block=False)
                else:
                    out, now = self.processOutput(out, format_out=format_out, data_type=data_type, timestamp=now)
                    if out is not None:
                        buffer.append((out, now))
                        callback((out, now))
            except queue.Full:
                time.sleep(0.01)
                continue
            except KeyboardInterrupt:
                self.stream_event.clear()
                break
        return


class AnyDevice(BaseDevice):
    def __new__(cls, *args, **kwargs):
        class_ = cls.__determine_subclass(*args, **kwargs)
        name = f'{cls.__name__}_{class_.__name__}'
        attrs = dict()
        base_attrs = {attr: getattr(BaseDevice, attr) for attr in BaseDevice.__dict__}
        subclass_attrs = {attr: getattr(class_, attr) for attr in class_.__dict__}
        cls_attrs = {attr: getattr(cls, attr) for attr in cls.__dict__}
        attrs.update(base_attrs)
        attrs.update(subclass_attrs)
        attrs.update(cls_attrs)
        attrs.pop('__dict__', None)
        new_class = type(name, (cls, class_), attrs)
        return super(AnyDevice,cls).__new__(new_class)
    
    def __init__(self, *args, **kwargs):
        if isinstance(self,WebsocketDevice):
            kwargs['timeout'] = 0.1
        return super().__init__(*args, **kwargs)

    @classmethod
    def __determine_subclass(cls, *args, **kwargs) -> Type[BaseDevice]:
        """Determine the appropriate subclass based on the provided arguments"""
        if 'host' in kwargs:
            if 'bytesize' in kwargs:
                return SocketDevice
            else:
                return WebsocketDevice
        elif 'baudrate' in kwargs:
            return SerialDevice
        return BaseDevice
    

class SerialDevice(BaseDevice):
    """
    SerialDevice provides an interface for handling serial devices
    
    ### Constructor:
        `port` (str|None, optional): serial port for the device. Defaults to None.
        `baudrate` (int, optional): baudrate for the device. Defaults to 9600.
        `timeout` (int, optional): timeout for the device. Defaults to 1.
        `init_timeout` (int, optional): timeout for initialization. Defaults to 2.
        `data_type` (NamedTuple, optional): data type for the device. Defaults to Data.
        `read_format` (str, optional): read format for the device. Defaults to READ_FORMAT.
        `write_format` (str, optional): write format for the device. Defaults to WRITE_FORMAT.
        `simulation` (bool, optional): whether to simulate the device. Defaults to False.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes and properties:
        `port` (str): device serial port
        `baudrate` (int): device baudrate
        `timeout` (int): device timeout
        `connection_details` (dict): connection details for the device
        `serial` (serial.Serial): serial object for the device
        `init_timeout` (int): timeout for initialization
        `message_end` (str): message end character
        `flags` (SimpleNamespace[str, bool]): flags for the device
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
        
    ### Methods:
        `clear`: clear the input and output buffers, and reset the data queue and buffer
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `checkDeviceConnection`: check the connection to the device
        `checkDeviceBuffer`: check the connection buffer
        `clearDeviceBuffer`: clear the device input and output buffers
        `read`: read data from the device
        `readAll`: read all data from the device
        `write`: write data to the device
        `poll`: poll the device (i.e. write and read data)
        `processInput`: process the input data
        `processOutput`: process the output data
        `query`: query the device (i.e. write and read data)
        `startStream`: start the stream
        `stopStream`: stop the stream
        `stream`: toggle the stream
        `showStream`: show the stream
    """
    
    def __init__(self,
        port: str|None = None, 
        baudrate: int = 9600, 
        timeout: int = 1, 
        *,
        init_timeout:int = 1, 
        data_type: NamedTuple = Data,
        read_format:str = READ_FORMAT,
        write_format:str = WRITE_FORMAT,
        simulation:bool = False, 
        verbose:bool = False,
        **kwargs
    ):
        """ 
        Initialize SerialDevice class
        
        Args:
            port (str|None, optional): serial port for the device. Defaults to None.
            baudrate (int, optional): baudrate for the device. Defaults to 9600.
            timeout (int, optional): timeout for the device. Defaults to 1.
            init_timeout (int, optional): timeout for initialization. Defaults to 2.
            data_type (NamedTuple, optional): data type for the device. Defaults to Data.
            read_format (str, optional): read format for the device. Defaults to READ_FORMAT.
            write_format (str, optional): write format for the device. Defaults to WRITE_FORMAT.
            simulation (bool, optional): whether to simulate the device. Defaults to False.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        super().__init__(
            init_timeout=init_timeout, simulation=simulation, verbose=verbose, 
            data_type=data_type, read_format=read_format, write_format=write_format, **kwargs
        )
        self.connection: serial.Serial = serial.Serial()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        return
    
    @property
    def serial(self) -> serial.Serial:
        """Serial object for the device"""
        return self.connection
    @serial.setter
    def serial(self, value:serial.Serial):
        assert isinstance(value, serial.Serial), "Ensure connection is a serial object"
        self.connection = value
        return
    
    @property
    def port(self) -> str:
        """Device serial port"""
        return self.connection_details.get('port', '')
    @port.setter
    def port(self, value:str):
        self.connection_details['port'] = value
        self.serial.port = value
        return
    
    @property
    def baudrate(self) -> int:
        """Device baudrate"""
        return self.connection_details.get('baudrate', 0)
    @baudrate.setter
    def baudrate(self, value:int):
        assert isinstance(value, int), "Ensure baudrate is an integer"
        assert value in serial.Serial.BAUDRATES, f"Ensure baudrate is one of the standard values: {serial.Serial.BAUDRATES}"
        self.connection_details['baudrate'] = value
        self.serial.baudrate = value
        return
    
    @property
    def timeout(self) -> int:
        """Device timeout"""
        return self.connection_details.get('timeout', 0)
    @timeout.setter
    def timeout(self, value:int):
        self.connection_details['timeout'] = value
        self.serial.timeout = value
        return
    
    def checkDeviceBuffer(self) -> bool:
        """Check the connection buffer"""
        return self.serial.in_waiting
    
    def checkDeviceConnection(self):
        """Check the connection to the device"""
        self.flags.connected = self.serial.is_open
        return self.flags.connected
    
    def clearDeviceBuffer(self):
        """Clear the device input and output buffers"""
        try:
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
        except serial.PortNotOpenError as e:
            self._logger.error(e)
        return

    def connect(self):
        """Connect to the device"""
        if self.is_connected:
            return
        try:
            self.serial.open()
        except serial.SerialException as e:
            self._logger.error(f"Failed to connect to {self.port} at {self.baudrate} baud")
            self._logger.debug(e)
        else:
            self._logger.info(f"Connected to {self.port} at {self.baudrate} baud")
            time.sleep(self.init_timeout)
        self.flags.connected = True
        return

    def disconnect(self):
        """Disconnect from the device"""
        if not self.is_connected:
            return
        self.stopStream()
        try:
            self.serial.close()
        except serial.SerialException as e:
            self._logger.error(f"Failed to disconnect from {self.port}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Disconnected from {self.port}")
        self.flags.connected = False
        return
    
    def read(self) -> str:
        """Read data from the device"""
        data = ''
        try:
            data = self.serial.readline().decode("utf-8", "replace").replace('\uFFFD', '')
            # eol = self.eol if len(self.eol) else '\n'
            # data = self.serial.read_until(eol.encode()).decode("utf-8", "replace").replace('\uFFFD', '')
            data = data.strip()
            self._logger.debug(f"[{self.port}] Received: {data!r}")
            self.serial.reset_output_buffer()
        except serial.SerialException:
            self._logger.debug(f"[{self.port}] Failed to receive data")
        except KeyboardInterrupt:
            self._logger.debug("Received keyboard interrupt")
            self.disconnect()
        return data
    
    def readAll(self) -> list[str]:
        """Read all data from the device"""
        delimiter = self.read_format.replace(self.read_format.rstrip(), '')
        data = ''
        try:
            while True:
                out = self.serial.read_all().decode("utf-8", "replace").replace('\uFFFD', '')
                data += out
                if not out:
                    break
        except serial.SerialException as e:
            self._logger.debug(f"[{self.port}] Failed to receive data")
            self._logger.debug(e)
        except KeyboardInterrupt:
            self._logger.debug("Received keyboard interrupt")
            self.disconnect()
        data = data.strip()
        self._logger.debug(f"[{self.port}] Received: {data!r}")
        return [d.strip() for d in data.split(delimiter) if len(d.strip())]
    
    def write(self, data:str) -> bool:
        """Write data to the device"""
        assert isinstance(data, str), "Ensure data is a string"
        try:
            self.serial.write(data.encode('utf-8'))
            self._logger.debug(f"[{self.port}] Sent: {data!r}")
        except serial.SerialException:
            self._logger.debug(f"[{self.port}] Failed to send: {data!r}")
            return False
        return True


class SocketDevice(BaseDevice):
    """
    SocketDevice provides an interface for handling socket devices
    
    ### Constructor:
        `host` (str): host for the device
        `port` (int): port for the device
        `timeout` (int, optional): timeout for the device. Defaults to 1.
        `byte_size` (int, optional): size of the byte buffer. Defaults to 1024.
        `simulation` (bool, optional): whether to simulate the device. Defaults to False.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes and properties:
        `host` (str): device host
        `port` (int): device port
        `timeout` (int): device timeout
        `byte_size` (int): size of the byte buffer
        `connection_details` (dict): connection details for the device
        `socket` (socket.socket): socket object for the device
        `flags` (SimpleNamespace[str, bool]): flags for the device
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
        
    ### Methods:
        `clear`: clear the input and output buffers, and reset the data queue and buffer
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `checkDeviceConnection`: check the connection to the device
        `checkDeviceBuffer`: check the connection buffer
        `clearDeviceBuffer`: clear the device input and output buffers
        `read`: read data from the device
        `readAll`: read all data from the device
        `write`: write data to the device
        `poll`: poll the device (i.e. write and read data)
        `processInput`: process the input data
        `processOutput`: process the output data
        `query`: query the device (i.e. write and read data)
        `startStream`: start the stream
        `stopStream`: stop the stream
        `stream`: toggle the stream
        `showStream`: show the stream
    """
    
    _default_flags: SimpleNamespace = SimpleNamespace(verbose=False, connected=False, simulation=False)
    def __init__(self, 
        host:str, 
        port:int, 
        timeout:int=1, 
        *, 
        byte_size: int = 1024,
        simulation:bool=False, 
        verbose:bool = False, 
        **kwargs
    ):
        """
        Initialize SocketDevice class
        
        Args:
            host (str): host for the device
            port (int): port for the device
            timeout (int, optional): timeout for the device. Defaults to 1.
            byte_size (int, optional): size of the byte buffer. Defaults to 1024.
            simulation (bool, optional): whether to simulate the device. Defaults to False.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        super().__init__(simulation=simulation, verbose=verbose, **kwargs)
        self.connection: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.timeout = timeout
        self.byte_size = byte_size
        
        self._current_socket_ref = -1
        self._stream_buffer = ""
        # self.connect()
        return

    @property
    def socket(self) -> socket.socket:
        """Socket object for the device"""
        return self.connection
    @socket.setter
    def socket(self, value:socket.socket):
        assert isinstance(value, socket.socket), "Ensure connection is a socket object"
        self.connection = value
        return
    
    @property
    def address(self) -> tuple[str,int]:
        """Device address"""
        return (self.host, self.port)
    
    @property
    def host(self) -> str:
        """Device socket host"""
        return self.connection_details.get('host', '')
    @host.setter
    def host(self, value:str):
        self.connection_details['host'] = value
        return
    
    @property
    def port(self) -> str:
        """Device socket port"""
        return self.connection_details.get('port', '')
    @port.setter
    def port(self, value:str):
        self.connection_details['port'] = value
        return
    
    @property
    def timeout(self) -> int:
        """Device timeout"""
        return self.connection_details.get('timeout', '')
    @timeout.setter
    def timeout(self, value:int):
        self.connection_details['timeout'] = value
        return
    
    def checkDeviceBuffer(self) -> bool:
        """Check the connection buffer"""
        return self.stream_event.is_set() or self._stream_buffer
    
    def checkDeviceConnection(self):
        """Check the connection to the device"""
        try:
            self.socket.sendall('\n'.encode('utf-8'))
            self.socket.sendall('\n'.encode('utf-8'))
        except OSError:
            self.flags.connected = False
            return False
        self.flags.connected =(self.socket.fileno() == self._current_socket_ref) and (self.socket.fileno() != -1)
        return self.flags.connected
    
    def clearDeviceBuffer(self):
        """Clear the device input and output buffers"""
        self._stream_buffer = ""
        while True:
            try:
                out = self.socket.recv(self.byte_size).decode("utf-8", "replace").strip('\r\n').replace('\uFFFD', '')
            except OSError:
                break
            if not out:
                break
        return

    def connect(self):
        """Connect to the device"""
        if self.is_connected:
            return
        try:
            self.socket = socket.create_connection(self.address)
            self.socket.settimeout(self.timeout)
            self._current_socket_ref = self.socket.fileno()
            self.clear()
        except OSError as e:
            self._logger.error(f"Failed to connect to {self.host}:{self.port}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Connected to {self.host}:{self.port}")
            time.sleep(self.init_timeout)
        self.flags.connected = True
        return

    def disconnect(self):
        """Disconnect from the device"""
        if not self.is_connected:
            return
        self.stopStream()
        try:
            self.socket.close()
            self._current_socket_ref = -1
        except OSError as e:
            self._logger.error(f"Failed to disconnect from {self.host}:{self.port}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Disconnected from {self.host}:{self.port}")
        self.flags.connected = False
        return
    
    def read(self) -> str:
        """Read data from the device"""
        delimiter = self.read_format.replace(self.read_format.rstrip(), '')
        data = self._stream_buffer
        self._stream_buffer = ''
        try:
            out = self.socket.recv(self.byte_size).decode("utf-8", "replace").strip(delimiter).replace('\uFFFD', '')
            data += out
            # if not out or delimiter in data:
            #     break
        except OSError as e:
            if not data:
                self._logger.debug(f"[{self.host}] Failed to receive data")
                self._logger.debug(e)
        except KeyboardInterrupt:
            self._logger.debug("Received keyboard interrupt")
            self.disconnect()
        if delimiter and delimiter in data:
            data, self._stream_buffer = data.split(delimiter, 1)
        data = data.strip()
        self._logger.debug(f"[{self.host}] Received: {data!r}")
        return data
    
    def readAll(self) -> list[str]:
        """Read all data from the device"""
        delimiter = self.read_format.replace(self.read_format.rstrip(), '')
        data = self._stream_buffer
        self._stream_buffer = ''
        try:
            while True:
                out = self.socket.recv(self.byte_size).decode("utf-8", "replace").replace('\uFFFD', '')
                data += out
                if not out or len(data)>self.byte_size:
                    break
        except OSError as e:
            self._logger.debug(f"[{self.host}] Failed to receive data")
            self._logger.debug(e)
        except KeyboardInterrupt:
            self._logger.debug("Received keyboard interrupt")
            self.disconnect()
        data = data.strip()
        self._logger.debug(f"[{self.host}] Received: {data!r}")
        return [d for d in data.split(delimiter) if len(d)] if delimiter else [data]
    
    def write(self, data:str) -> bool:
        """Write data to the device"""
        assert isinstance(data, str), "Ensure data is a string"
        try:
            self.socket.sendall(data.encode('utf-8'))
            self._logger.debug(f"[{self.host}] Sent: {data!r}")
        except OSError as e:
            self._logger.debug(f"[{self.host}] Failed to send: {data!r}")
            self._logger.debug(e)
            return False
        return True


class WebsocketDevice(BaseDevice):
    """
    WebsocketDevice provides an interface for handling websocket devices
    
    ### Constructor:
        `host` (str): host for the device
        `port` (int): port for the device
        `timeout` (int, optional): timeout for the device. Defaults to 1.
        `simulation` (bool, optional): whether to simulate the device. Defaults to False.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes and properties:
        `host` (str): device host
        `port` (int): device port
        `uri` (str): URI for the device
        `timeout` (int): device timeout
        `connection_details` (dict): connection details for the device
        `websocket` (websockets.sync.client.ClientConnection): client object for the device
        `flags` (SimpleNamespace[str, bool]): flags for the device
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
        
    ### Methods:
        `clear`: clear the input and output buffers, and reset the data queue and buffer
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `checkDeviceConnection`: check the connection to the device
        `checkDeviceBuffer`: check the connection buffer
        `clearDeviceBuffer`: clear the device input and output buffers
        `read`: read data from the device
        `readAll`: read all data from the device
        `write`: write data to the device
        `poll`: poll the device (i.e. write and read data)
        `processInput`: process the input data
        `processOutput`: process the output data
        `query`: query the device (i.e. write and read data)
        `startStream`: start the stream
        `stopStream`: stop the stream
        `stream`: toggle the stream
        `showStream`: show the stream
    """
    
    _default_flags: SimpleNamespace = SimpleNamespace(verbose=False, connected=False, simulation=False)
    def __init__(self, 
        host:str, 
        port:int, 
        timeout:int=0.1, 
        *,
        simulation:bool=False, 
        verbose:bool = False, 
        **kwargs
    ):
        """
        Initialize SocketDevice class
        
        Args:
            host (str): host for the device
            port (int): port for the device
            timeout (int, optional): timeout for the device. Defaults to 1.
            simulation (bool, optional): whether to simulate the device. Defaults to False.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        super().__init__(simulation=simulation, verbose=verbose, **kwargs)
        
        self.host = host
        self.port = port
        self.uri = f"wss://{host}:{port}/" if self.port is not None else f"wss://{host}/"
        self.timeout = timeout
        self.connection: client.ClientConnection = client.connect(uri=self.uri)
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # p = websockets.client.ClientProtocol('localhost')
        # self.connection: client.ClientConnection = client.ClientConnection(s,p)
        
        self._stream_buffer = ""
        # self.connect()
        return

    @property
    def websocket(self) -> client.ClientConnection:
        """Socket object for the device"""
        return self.connection
    @websocket.setter
    def websocket(self, value:client.ClientConnection):
        assert isinstance(value, client.ClientConnection), "Ensure connection is a ClientConnection object"
        self.connection = value
        return
    
    @property
    def host(self) -> str:
        """Device socket host"""
        return self.connection_details.get('host', '')
    @host.setter
    def host(self, value:str):
        self.connection_details['host'] = value
        return
    
    @property
    def port(self) -> str:
        """Device socket port"""
        return self.connection_details.get('port', '')
    @port.setter
    def port(self, value:str):
        self.connection_details['port'] = value
        return
    
    @property
    def timeout(self) -> int:
        """Device timeout"""
        return self.connection_details.get('timeout', '')
    @timeout.setter
    def timeout(self, value:int):
        self.connection_details['timeout'] = value
        return
   
    def checkDeviceBuffer(self) -> bool:
        """Check the connection buffer"""
        return self.stream_event.is_set() or self._stream_buffer
    
    def checkDeviceConnection(self):
        """Check the connection to the device"""
        try:
            connected = self.websocket.state == websockets.protocol.State.OPEN
        except OSError:
            self.flags.connected = False
            return False
        self.flags.connected = connected
        return self.flags.connected
    
    def clearDeviceBuffer(self):
        """Clear the device input and output buffers"""
        self._stream_buffer = ""
        # self.readAll()
        while True:
            try:
                out = self.websocket.recv(self.timeout)
                if isinstance(out, bytes):
                    out = out.decode("utf-8", "replace")
                out = out.strip('\r\n').replace('\uFFFD', '')
            except OSError:
                break
            except websockets.exceptions.ConnectionClosed:
                break
            if not out:
                break
        return

    def connect(self):
        """Connect to the device"""
        if self.is_connected:
            return
        try:
            self.websocket = client.connect(self.uri)
            # self.clear()
        except OSError as e:
            self._logger.error(f"Failed to connect to {self.uri}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Connected to {self.uri}")
            time.sleep(self.init_timeout)
        self.flags.connected = True
        return

    def disconnect(self):
        """Disconnect from the device"""
        if not self.is_connected:
            return
        self.stopStream()
        try:
            self.websocket.close()
        except OSError as e:
            self._logger.error(f"Failed to disconnect from {self.uri}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Disconnected from {self.uri}")
        self.flags.connected = False
        return
    
    def read(self) -> str:
        """Read data from the device"""
        delimiter = self.read_format.replace(self.read_format.rstrip(), '')
        data = self._stream_buffer
        self._stream_buffer = ''
        try:
            out = self.websocket.recv(self.timeout)
            if isinstance(out, bytes):
                out = out.decode("utf-8", "replace")
            out = out.strip(delimiter).replace('\uFFFD', '')
            data += out
            # if not out or delimiter in data:
            #     break
        except OSError as e:
            if not data:
                self._logger.debug(f"[{self.host}] Failed to receive data")
                self._logger.debug(e)
        except websockets.exceptions.ConnectionClosed as e:
            # self._logger.debug(f"[{self.host}] Connection closed while reading: {data!r}")
            # self._logger.debug(e)
            # self.flags.connected = False
            self.connect()
            if self.is_connected:
                self.read()
                return self.read()
            return False
        except KeyboardInterrupt:
            self._logger.debug("Received keyboard interrupt")
            self.disconnect()
        if delimiter and delimiter in data:
            data, self._stream_buffer = data.split(delimiter, 1)
        data = data.strip()
        self._logger.debug(f"[{self.host}] Received: {data!r}")
        return data
    
    def readAll(self) -> list[str]:
        """Read all data from the device"""
        delimiter = self.read_format.replace(self.read_format.rstrip(), '')
        data = self._stream_buffer
        self._stream_buffer = ''
        try:
            while True:
                out = self.websocket.recv(self.timeout)
                if isinstance(out, bytes):
                    out = out.decode("utf-8", "replace")
                out = out.replace('\uFFFD', '')
                if not out:
                    break
                data += out
        except OSError as e:
            if not data:
                self._logger.debug(f"[{self.host}] Failed to receive data")
                self._logger.debug(e)
        except websockets.exceptions.ConnectionClosed as e:
            # self._logger.debug(f"[{self.host}] Connection closed while reading: {data!r}")
            # self._logger.debug(e)
            # self.flags.connected = False
            self.connect()
            if self.is_connected:
                self.read()
                return self.readAll()
            return False
        except KeyboardInterrupt:
            self._logger.debug("Received keyboard interrupt")
            self.disconnect()
        data = data.strip()
        self._logger.debug(f"[{self.host}] Received: {data!r}")
        return [d for d in data.split(delimiter) if len(d)] if delimiter else [data]
    
    def write(self, data:str) -> bool:
        """Write data to the device"""
        assert isinstance(data, str), "Ensure data is a string"
        try:
            self.websocket.send(data)
            # self.websocket.send(data.encode('utf-8'))
            self._logger.debug(f"[{self.host}] Sent: {data!r}")
        except OSError as e:
            self._logger.debug(f"[{self.host}] Failed to send: {data!r}")
            self._logger.debug(e)
            return False
        except websockets.exceptions.ConnectionClosed as e:
            # self._logger.debug(f"[{self.host}] Connection closed while sending: {data!r}")
            # self._logger.debug(e)
            # self.flags.connected = False
            self.connect()
            if self.is_connected:
                self.read()
                return self.write(data)
            return False
        return True
