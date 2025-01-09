# -*- coding: utf-8 -*-
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
from typing import Any, NamedTuple, Callable, Protocol

# Third party imports
import parse
import serial

_logger = logging.getLogger("controllably.core")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
# handler.setLevel(logging.INFO)
# handler.addFilter(logging.Filter(__name__+'.'))
# logger.addHandler(handler)

# def get_host() -> str:
#     """
#     Get the host IP address for current machine

#     Returns:
#         str: machine host IP address
#     """
#     host = socket.gethostbyname(socket.gethostname())
#     host_out = f"Current machine host: {host}"
#     logger.info(host_out)
#     return host

# def match_current_ip_address(ip_address:str) -> bool:
#     """
#     Match the current IP address of the machine

#     Returns:
#         bool: whether the IP address matches the current machine
#     """
#     hostname = socket.gethostname()
#     logger.info(f"Current IP address: {hostname}")
#     local_ips = socket.gethostbyname_ex(hostname)[2]
#     success = False
#     for local_ip in local_ips:
#         local_network = f"{'.'.join(local_ip.split('.')[:-1])}.0/24"
#         if ipaddress.ip_address(ip_address) in ipaddress.ip_network(local_network):
#             success = True
#             break
#     return success

class Device(Protocol):
    """Protocol for device connection classes"""
    connection_details: dict
    is_connected: bool
    verbose: bool
    def clear(self):
        """Clear the input and output buffers"""
        raise NotImplementedError

    def connect(self):
        """Connect to the device"""
        raise NotImplementedError

    def disconnect(self):
        """Disconnect from the device"""
        raise NotImplementedError

    def query(self, data:Any, multi_out:bool = True) -> Any:
        """Query the device"""
        raise NotImplementedError

    def read(self) -> str|None:
        """Read data from the device"""
        raise NotImplementedError

    def write(self, data:str) -> bool:
        """Write data to the device"""
        raise NotImplementedError


class BaseDevice:
    
    _default_flags: SimpleNamespace = SimpleNamespace(verbose=False, connected=False, simulation=False)
    def __init__(self, 
        *, 
        connection_details:dict = dict(), 
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
        self.connection_details = connection_details
        self.flags = deepcopy(self._default_flags)
        self.init_timeout = init_timeout
        self.flags.simulation = simulation
        
        # IO attributes
        self.data_type = data_type
        self.read_format = read_format
        self.write_format = write_format
        fields = set([field for _, field, _, _ in Formatter().parse(read_format) if field])
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
    
    def poll(self, data:str|None = None) -> str:
        if data is not None:
            ret = self.write(data)
        if data is None or ret:
            out: str = self.read()
        return out
    
    def process_input(self, 
        data: Any = None,
        format: str|None = None,
        **kwargs
    ) -> str:
        """Process the input"""
        format = format or self.write_format
        assert isinstance(format, str), "Ensure format is a string"
        
        kwargs.update(dict(data=data))
        processed_data = format.format(**kwargs)
        return processed_data
    
    def process_output(self, 
        data: str, 
        format: str|None = None, 
        data_type: NamedTuple|None = None, 
        timestamp: datetime|None = None,
        condition: Callable[[Any,datetime], bool]|None = None
    ) -> tuple[Any, datetime|None]:
        """Process the output"""
        format = format or self.read_format
        format = format.strip()
        data_type = data_type or self.data_type
        fields = set([field for _, field, _, _ in Formatter().parse(format) if field])
        assert set(data_type._fields) == fields, "Ensure data type fields match read format fields"
        
        parse_out =parse.parse(format, data)
        if parse_out is None:
            self._logger.warning(f"Failed to parse data: {data!r}")
            return data, timestamp
        parsed = parse_out.named
        for key, value in data_type.__annotations__.items():
            if value == int and not parsed[key].isnumeric():
                parsed[key] = float(parsed[key])
            parsed[key] = value(parsed[key])
        processed_data = data_type(**parsed) 
        
        if self.show_event.is_set():
            print(processed_data)
        if callable(condition) and condition(processed_data, timestamp):
            self.stopStream()
        return processed_data, timestamp
    
    def query(self, 
        data: Any, 
        multi_out: bool = True, 
        format_in: str|None = None, 
        format_out: str|None = None,
        data_type: NamedTuple|None = None
    ) -> Any:
        """Query the device"""
        data_in = self.process_input(data, format_in)
        if not multi_out:
            raw_out = self.poll(data_in)
            return self.process_output(raw_out, format_out, data_type)
        
        all_data = []
        ret = self.write(data_in)
        if not ret:
            return
        while True:
            raw_out = self.read()
            if raw_out is None or raw_out.strip() == '':
                break
            data_out = self.process_output(raw_out, format_out, data_type)
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
                out, now = self.data_queue.get()#(block=False)
                out, now = self.process_output(out, format=format, data_type=data_type, timestamp=now)
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
                out, now = self.process_output(out, format=format, data_type=data_type, timestamp=now)
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


class SerialDevice(BaseDevice):
    """
    SerialDevice provides an interface for handling serial devices
    
    ### Constructor:
        `port` (str|None, optional): serial port for the device. Defaults to None.
        `baudrate` (int, optional): baudrate for the device. Defaults to 9600.
        `timeout` (int, optional): timeout for the device. Defaults to 1.
        `init_timeout` (int, optional): timeout for initialization. Defaults to 2.
        `message_end` (str, optional): message end character. Defaults to '\\n'.
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
        `clear`: clear the input and output buffers
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `query`: query the device (i.e. write and read data)
        `read`: read data from the device
        `write`: write data to the device
    """
    
    def __init__(self,
        port: str|None = None, 
        baudrate: int = 9600, 
        timeout: int = 1, 
        *,
        init_timeout:int = 1, 
        data_type: NamedTuple = NamedTuple("Data", [("data", str)]),
        read_format:str = "{data}",
        write_format:str = "{data}\n",
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
            message_end (str, optional): message end character. Defaults to '\\n'.
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
    
    def __del__(self):
        self.disconnect()
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
        return self.connection_details.get('baudrate', '')
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
        return self.connection_details.get('timeout', '')
    @timeout.setter
    def timeout(self, value:int):
        self.connection_details['timeout'] = value
        self.serial.timeout = value
        return
    
    def checkDeviceBuffer(self) -> bool:
        """Check the connection buffer"""
        return self.serial.out_waiting
    
    def checkDeviceConnection(self):
        """Check the connection to the device"""
        return self.serial.is_open
    
    def clear(self):
        """Clear the input and output buffers"""
        super().clear()
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
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
        try:
            self.serial.close()
        except serial.SerialException as e:
            self._logger.error(f"Failed to disconnect from {self.port}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Disconnected from {self.port}")
        self.flags.connected = False
        return
    
    def read(self) -> str|None:
        """Read data from the device"""
        data = None
        try:
            data = self.serial.readline().decode("utf-8", "replace")
            data = data.strip()
            self._logger.debug(f"Received: {data!r}")
        except serial.SerialException as e:
            self._logger.debug(f"Failed to receive data")
        except KeyboardInterrupt:
            self._logger.debug("Received keyboard interrupt")
            self.disconnect()
        return data
    
    def write(self, data:str) -> bool:
        """Write data to the device"""
        assert isinstance(data, str), "Ensure data is a string"
        try:
            self.serial.write(data.encode())
            self._logger.debug(f"Sent: {data!r}")
        except serial.SerialException as e:
            self._logger.debug(f"Failed to send: {data!r}")
            return False
        return True


class SocketDevice(BaseDevice):
    """
    SocketDevice provides an interface for handling socket devices
    
    ### Constructor:
        `host` (str): host for the device
        `port` (int): port for the device
        `timeout` (int, optional): timeout for the device. Defaults to 1.
        `simulation` (bool, optional): whether to simulate the device. Defaults to False.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes and properties:
        `host` (str): device host
        `port` (int): device port
        `timeout` (int): device timeout
        `connection_details` (dict): connection details for the device
        `socket` (socket.socket): socket object for the device
        `flags` (SimpleNamespace[str, bool]): flags for the device
        `is_connected` (bool): whether the device is connected
        `verbose` (bool): verbosity of class
        
    ### Methods:
        `clear`: clear the input and output buffers
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `query`: query the device (i.e. write and read data)
        `read`: read data from the device
        `write`: write data to the device
    """
    
    _default_flags: SimpleNamespace = SimpleNamespace(verbose=False, connected=False, simulation=False)
    def __init__(self, 
        host:str, 
        port:int, 
        timeout:int=0, 
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
        return (self.socket.fileno() == self._current_socket_ref) and (self.socket.fileno() != -1)
    
    def clear(self):
        """Clear the input and output buffers"""
        super().clear()
        self._stream_buffer = ""
        while True:
            try:
                self.socket.recv(self.byte_size).decode("utf-8", "replace").strip('\r\n')
            except OSError:
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
    
    def read(self) -> str|None:
        """Read data from the device"""
        delimiter = self.read_format.replace(self.read_format.rstrip(), '')
        data = self._stream_buffer
        self._stream_buffer = ''
        try:
            out = self.socket.recv(self.byte_size).decode("utf-8", "replace").strip(delimiter)
            data += out
            # if not out or delimiter in data:
            #     break
        except OSError as e:
            if not data:
                self._logger.debug(f"Failed to receive data")
                self._logger.debug(e)
        except KeyboardInterrupt:
            self._logger.debug("Received keyboard interrupt")
            self.disconnect()
        if delimiter in data:
            data, self._stream_buffer = data.split(delimiter, 1)
        data = data.strip()
        self._logger.debug(f"Received: {data!r}")
        return data
    
    def read_all(self) -> list[str]|None:
        """Read all data from the device"""
        delimiter = self.read_format.replace(self.read_format.rstrip(), '')
        data = self._stream_buffer
        self._stream_buffer = ''
        try:
            while True:
                out = self.socket.recv(self.byte_size).decode("utf-8", "replace")
                data += out
                if not out or len(data)>self.byte_size:
                    break
        except OSError as e:
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
            self.socket.sendall(data.encode())
            self._logger.debug(f"Sent: {data!r}")
        except OSError as e:
            self._logger.debug(f"Failed to send: {data!r}")
            self._logger.debug(e)
            return False
        return True
