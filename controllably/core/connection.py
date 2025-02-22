# -*- coding: utf-8 -*-
""" 
This module provides classes for handling connections to serial and socket devices.
    
## Classes:
    `Device`: Protocol for device connection classes
    `SerialDevice`: Interface for handling serial devices
    `SocketDevice`: Interface for handling socket devices
    `DeviceFactory`: Factory class for creating devices
    
## Functions:
    `get_addresses`: Get the appropriate addresses for current machine
    `get_node`: Get the unique identifier for current machine
    `get_ports`: Get available serial ports connected to current machine
    
<i>Documentation last updated: 2024-11-12</i>
"""
# Standard library imports
from __future__ import annotations
from collections import deque
from copy import deepcopy
import ipaddress
import logging
import queue
from random import random
import select
import socket
import threading
import time
from types import SimpleNamespace
from typing import Callable, Mapping, Protocol, Any
import uuid

# Third party imports
import serial                       # pip install pyserial
import serial.tools.list_ports

_logger = logging.getLogger("controllably.core")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.addFilter(logging.Filter(__name__+'.'))
logger.addHandler(handler)

BYTESIZE = 1024
ENCODER = 'utf-8'

CONNECT_MESSAGE = '[CONNECTED]'
DISCONNECT_MESSAGE = '!EXIT'
SHUTDOWN_MESSAGE = '!SHUTDOWN'

def get_addresses(registry:dict|None) -> dict|None:
    """
    Get the appropriate addresses for current machine

    Args:
        registry (dict|None): dictionary with serial port addresses and camera ids

    Returns:
        dict|None: dictionary of serial port addresses and camera ids for current machine, if available
    """
    node_id = get_node()
    addresses = registry.get('machine_id',{}).get(node_id,{}) if registry is not None else {}
    if len(addresses) == 0:
        logger.warning("Append machine id and camera ids/port addresses to registry file")
        logger.warning(f"Machine not yet registered. (Current machine id: {node_id})")
        return None
    return addresses

def get_host() -> str:
    """
    Get the host IP address for current machine

    Returns:
        str: machine host IP address
    """
    host = socket.gethostbyname(socket.gethostname())
    host_out = f"Current machine host: {host}"
    logger.info(host_out)
    return host

def get_node() -> str:
    """
    Get the unique identifier for current machine

    Returns:
        str: machine unique identifier
    """
    node_id = str(uuid.getnode())
    node_out = f"Current machine id: {node_id}"
    logger.info(node_out)
    return node_id

def get_ports() -> list[str]:
    """
    Get available serial ports connected to current machine

    Returns:
        list[str]: list of connected serial ports
    """
    ports = []
    for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
        ports.append(str(port))
        port_desc = f"{port}: [{hwid}] {desc}"
        logger.info(port_desc)
    if len(ports) == 0:
        logger.warning("No ports detected!")
    return ports

def match_current_ip_address(ip_address:str) -> bool:
    """
    Match the current IP address of the machine

    Returns:
        bool: whether the IP address matches the current machine
    """
    hostname = socket.gethostname()
    logger.info(f"Current IP address: {hostname}")
    local_ips = socket.gethostbyname_ex(hostname)[2]
    success = False
    for local_ip in local_ips:
        local_network = f"{'.'.join(local_ip.split('.')[:-1])}.0/24"
        if ipaddress.ip_address(ip_address) in ipaddress.ip_network(local_network):
            success = True
            break
    return success

class SocketUtils:
    def __init__(self):
        return
    
    @staticmethod
    def readAll(connection: socket.socket, *, bytesize: int = BYTESIZE, encoder: str = ENCODER, ignore: bool = True) -> str|None:
        data = ''
        flag = False
        while True:
            out = ''
            try:
                out = connection.recv(bytesize).decode(encoder, "replace")
            except OSError as e:
                if flag:
                    return None
                time.sleep(0.01)
                flag = True
                pass
            except TimeoutError:
                pass
            except (ConnectionError, ConnectionResetError, ConnectionAbortedError) as e:
                if not ignore:
                    raise e
            except KeyboardInterrupt:
                pass
            data += out
            if not out or len(data) > bytesize:
                break
        return data

    @staticmethod
    def read(connection: socket.socket, *, bytesize: int = BYTESIZE, encoder: str = ENCODER, ignore: bool = True) -> str|None:
        out = ''
        try:
            out = connection.recv(bytesize).decode(encoder, "replace")
        except OSError as e:
            return None
        except TimeoutError:
            pass
        except (ConnectionError, ConnectionResetError, ConnectionAbortedError) as e:
            if not ignore:
                raise e
        except KeyboardInterrupt:
            pass
        return out

    @staticmethod
    def write(data: str, connection: socket.socket, *, encoder: str = ENCODER, wait: bool = False, ignore: bool = False):
        try:
            connection.sendall(data.encode(encoder))
            if wait:
                time.sleep(0.1)
        except OSError as e:
            if not ignore:
                raise e
        except (ConnectionError, ConnectionResetError, ConnectionAbortedError) as e:
            if not ignore:
                raise e
        except KeyboardInterrupt:
            pass
        return

    @staticmethod
    def printer(print_queue: queue.Queue, jam: threading.Event):
        while not jam.is_set():
            try:
                print(print_queue.get())
                print_queue.task_done()
            except KeyboardInterrupt:
                break
        time.sleep(1)
        while print_queue.qsize() > 0:
            try:
                print(print_queue.get(timeout=1))
                print_queue.task_done()
            except queue.Empty:
                break
            except KeyboardInterrupt:
                break
        print('[EXIT] Printer')
        jam.clear()
        return


class Server:
    
    _default_keywords = dict(connect=CONNECT_MESSAGE, disconnect=DISCONNECT_MESSAGE, shutdown=SHUTDOWN_MESSAGE)
    def __init__(self, 
        host: str, 
        port: int,
        terminate: threading.Event = threading.Event(), 
        print_queue: queue.Queue|None = None,
        *,
        bytesize: int = 1024,
        encoder: str = 'utf-8',
        keywords: Mapping[str]|None = None
    ):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.address = f'{host}:{port}'
        
        self.use_external_printer = isinstance(print_queue, queue.Queue)
        self.print_queue = print_queue if self.use_external_printer else queue.Queue()
        self.connections = deque()
        self.removal_list = deque()
        self.triggers = dict(
            started = threading.Event(),
            update_connections = threading.Event(),
            terminate = terminate,
            jam = threading.Event()
        )
        
        self.bytesize = bytesize
        self.encoder = encoder
        self.keywords = deepcopy(self._default_keywords) if keywords is None else keywords
        
        self.client_threads = dict()
        self._printer_thread = None
        self._listener_thread = None
        return
    
    def __del__(self):
        self.stop()
        return
    
    def start(self, blocking: bool = False):
        """ 
        Start the server
        
        Args:
            blocking (bool, optional): whether to run the server in blocking mode. Defaults to False.
        """
        if self.triggers['started'].is_set():
            return
        self.startServer(
            self.host, 
            self.port, 
            triggers = self.triggers['terminate'], 
            print_queue = self.print_queue,
            blocking = False
        )
        if blocking:
            try:
                while not (input('Kill server? [y/n]: ').strip().lower() == 'y'):
                    time.sleep(1)
                    if not self.triggers['started'].is_set():
                        break
            except KeyboardInterrupt:
                pass
            self.stop()
        return
        
    def stop(self):
        """Stop the server"""
        self.triggers['terminate'].set()
        self.triggers['started'].clear()
        return
    
    def startServer(self, 
        host: str, 
        port: int, 
        client_handler: Callable|None = None,
        *,
        terminate: threading.Event|None = None,
        print_queue: queue.Queue|None = None,
        blocking: bool = False,
        **kwargs
    ):
        """
        Start the server
        
        Args:
            host (str): host for the server
            port (int): port for the server
            client_handler (Callable|None, optional): client handler function. Defaults to None.
            terminate (threading.Event|None, optional): termination event. Defaults to None.
            print_queue (queue.Queue|None, optional): print queue. Defaults to None.
            blocking (bool, optional): whether to run the server in blocking mode. Defaults to False.
        """
        client_handler = self.handleClient if client_handler is None else client_handler
        self.triggers['terminate'] = self.triggers['terminate'] if terminate is None else terminate
        print_queue = self.print_queue if print_queue is None else print_queue
        
        self.server = socket.create_server((host, port))
        self.triggers['started'].set()
        print_queue.put(f'[START] Server started {host}:{port}')
        
        self.server.listen()
        print_queue.put('[START] Listening for incoming connections...')
        
        if not self.use_external_printer:
            self.startPrinter()
        
        kwargs.update(
            triggers=self.triggers, print_queue=print_queue,
            connections=self.connections, removal_list=self.removal_list,
            threads=self.client_threads, keywords=self.keywords
        )
        if blocking:
            self.listen(self.server, client_handler, **kwargs)
        elif not (isinstance(self._listener_thread, threading.Thread) and self._listener_thread.is_alive()):
            self._listener_thread = threading.Thread(
                target=self.listen, 
                args=(self.server, client_handler),
                kwargs=kwargs
            )
            self._listener_thread.start()
        return
    
    def startPrinter(self):
        """Start the printer thread"""
        if not (isinstance(self._printer_thread, threading.Thread) and self._printer_thread.is_alive()):
            self._printer_thread = threading.Thread(target=SocketUtils.printer, args=(self.print_queue, self.triggers['jam']), daemon=True)
            self._printer_thread.start()
        return
    
    @staticmethod
    def listen(
        server: socket.socket, 
        client_handler: Callable,
        *,
        triggers: dict[str, threading.Event],
        print_queue: queue.Queue, 
        connections: deque,
        removal_list: deque,
        threads: dict[str, threading.Thread], 
        **kwargs
    ):
        while not triggers['terminate'].is_set():
            if triggers['update_connections'].is_set():
                message = f'[CONNECTIONS] {len(connections)}\n'
                message += f'{"\n".join([("- "+a) for a in connections])}'
                print_queue.put(message)
                while len(removal_list):
                    del threads[removal_list.pop()]
                triggers['update_connections'].clear()
                continue
            
            read_list, _, _ = select.select([server], [], [], 1)
            if server not in read_list:
                time.sleep(0.01)
                continue
            try:
                conn, addr = server.accept()
            except TimeoutError:
                time.sleep(0.01)
                continue
            except KeyboardInterrupt:
                break
            addr = f'{":".join([str(a) for a in addr])}'
            kwargs.update(
                triggers=triggers, print_queue=print_queue, 
                connections=connections, removal_list=removal_list
            )
            connections.append(addr)
            thread = threading.Thread(
                target=client_handler, 
                args=(conn, addr),
                kwargs=kwargs
            )
            thread.start()
            threads[addr] = thread
            triggers['update_connections'].set()
        
        triggers['terminate'].set()
        print_queue.put('[STOP] Termination triggered')
        
        for _,thread in threads.items():
            thread.join()
        addr = f'{":".join([str(a) for a in server.getsockname()])}'
        server.close()
        print_queue.put(f'[EXIT:SERVER] {addr}')
        
        # Reset
        if triggers['update_connections'].is_set():
            while len(removal_list):
                del threads[removal_list.pop()]
            triggers['update_connections'].clear()
        triggers['terminate'].clear()
        triggers['started'].clear()
        triggers['jam'].set()
        return
    
    @staticmethod
    def handleClient(
        conn: socket.socket, 
        addr: str, 
        *,
        triggers: dict[str, threading.Event],
        print_queue: queue.Queue,
        connections: deque,
        removal_list: deque,
        keywords: Mapping[str,str],
        **kwargs
    ):
        bytesize = kwargs.get('bytesize', BYTESIZE)
        encoder = kwargs.get('encoder', ENCODER)
        connect_message = keywords.get('connect', CONNECT_MESSAGE)
        disconnect_message = keywords.get('disconnect', DISCONNECT_MESSAGE)
        shutdown_message = keywords.get('shutdown', SHUTDOWN_MESSAGE)
        
        print_queue.put(f'[NEW] {addr}')
        conn.setblocking(False)
        
        while not triggers['terminate'].is_set():
            data = SocketUtils.read(conn, bytesize=bytesize, encoder=encoder)
            if not data:
                time.sleep(0.01)
                continue
            elif data.strip():
                print_queue.put(f"[{addr}] {data}")
            empty = (data == '\n') or (data == '\r\n')
            data = data.strip()
            
            if data == disconnect_message:
                break
            elif data == shutdown_message:
                SocketUtils.write(shutdown_message, conn, encoder=encoder, wait=True, ignore=True)
                triggers['terminate'].set()
                break
            elif data.startswith(connect_message):
                time.sleep(0.1)
                if addr in connections:
                    data = f'{connect_message} {addr}'
            
            if not data and not empty:
                time.sleep(0.01)
                data = f"{random()*10:.3f};{random()*10:.3f};{random()*10:.3f}\n"
            try:
                SocketUtils.write(data, conn, encoder=encoder)
            except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
                print_queue.put(f'[ERROR] Connection lost {addr}')
                break
        SocketUtils.write(disconnect_message, conn, encoder=encoder, wait=True, ignore=True)
        
        removal_list.append(addr)
        connections.remove(addr)
        triggers['update_connections'].set()
        time.sleep(1)
        if len(connections) == 0:
            triggers['terminate'].set()
            print_queue.put('[SHUTDOWN] No active connections')
        print_queue.put(f'[EXIT:CLIENT] {addr}')
        return
    

class Client:
    
    _default_keywords = dict(connect=CONNECT_MESSAGE, disconnect=DISCONNECT_MESSAGE, shutdown=SHUTDOWN_MESSAGE)
    def __init__(self,
        host: str, 
        port: int, 
        terminate: threading.Event = threading.Event(), 
        print_queue: queue.Queue|None = None,
        *,
        bytesize: int = 1024,
        encoder: str = 'utf-8',
        keywords: Mapping[str, str]|None = None
    ):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.address = ''
        self._current_socket_ref = -1
        
        self.bytesize = bytesize
        self.encoder = encoder
        self.keywords = deepcopy(self._default_keywords) if keywords is None else keywords
        
        self.use_external_printer = isinstance(print_queue, queue.Queue)
        self.print_queue = print_queue if self.use_external_printer else queue.Queue()
        self.triggers = dict(
            terminate = terminate,
        )
        
        self._printer_thread = None
        self._listener_thread = None
        return
    
    def __del__(self):
        self.disconnect()
        return
    
    @property
    def is_connected(self) -> bool:
        try:
            self.conn.sendall('\n'.encode())
            self.conn.sendall('\n'.encode())
        except OSError:
            return False
        return (self.conn.fileno() == self._current_socket_ref) and (self.conn.fileno() != -1)
    
    def connect(self):
        if self.is_connected:
            return
        self.startClient(self.host, self.port)
        return
    
    def disconnect(self):
        SocketUtils.write(self.keywords['disconnect'], self.conn, encoder=self.encoder, wait=True, ignore=True)
        self.triggers['terminate'].set()
        self.conn.close()
        self._current_socket_ref = -1
        return
    
    def shutdown(self):
        self.query(self.keywords['shutdown'])
        return
    
    def startClient(self, host:str, port:int):
        self.conn = socket.create_connection((host, port))
        success_message = f'{self.keywords["connect"]} {host}:{port}'
        self.print_queue.put(f'{self.keywords["connect"]} {host}:{port}')
        self.conn.settimeout(0)
        try:
            self.write(success_message)
        except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
            self.print_queue.put(f'[ABORT] Unsuccessful connection to {host}:{port}')
            return
        
        data = ''
        while self.keywords["connect"] not in data:
            out = self.read()
            if not out:
                continue
            data += out
        self.print_queue.put(f"[RECV] {data!r}")
        self.address = data.replace(f'{self.keywords["connect"]} ', '')
        self._current_socket_ref = self.conn.fileno()
        while self.read() is not None:
            pass
        
        if not self.use_external_printer:
            self.startPrinter()
        return
    
    def startPrinter(self):
        if not (isinstance(self._printer_thread, threading.Thread) and self._printer_thread.is_alive()):
            self._printer_thread = threading.Thread(target=SocketUtils.printer, args=(self.print_queue, self.triggers['terminate']), daemon=True)
            self._printer_thread.start()
        return
    
    def read(self) -> str:
        return SocketUtils.read(self.conn, bytesize=self.bytesize, encoder=self.encoder)

    def readAll(self) -> str:
        return SocketUtils.readAll(self.conn, bytesize=self.bytesize, encoder=self.encoder)

    def query(self, data: str, multi_line: bool = False) -> str|None:
        assert isinstance(data, str), 'Data must be a string'
        assert self.is_connected, 'Client is not connected'
        
        self.write(data)
        self.print_queue.put(f'[SENT] {data!r}')
        data = self.read()if not multi_line else self.readAll()
        if data is not None:
            data = data.strip()
        
        if data == self.keywords['disconnect']:
            self.print_queue.put(f'[EXIT] {self.host}:{self.port}')
            self.disconnect()
        elif data == self.keywords['shutdown']:
            self.print_queue.put(f'[SHUTDOWN] {self.host}:{self.port}')
            self.disconnect()
        else:
            self.print_queue.put(f"[RECV] {data!r}")
        return data
    
    def write(self, data: str) -> bool:
        try:
            SocketUtils.write(data, self.conn, encoder=self.encoder, wait=True)
        except OSError:
            return False
        except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
            self.print_queue.put(f'[ERROR] Connection lost {self.host}:{self.port}')
            self.disconnect()
            return False
        return True





# Deprecated
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

    def query(self, data:Any, lines:bool = True) -> list[str]|None:
        """Query the device"""
        raise NotImplementedError

    def read(self, lines:bool = False) -> str|list[str]:
        """Read data from the device"""
        raise NotImplementedError

    def write(self, data:str) -> bool:
        """Write data to the device"""
        raise NotImplementedError


class SerialDevice:
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
    
    _default_flags: SimpleNamespace = SimpleNamespace(verbose=False, connected=False, simulation=False)
    def __init__(self,
        port: str|None = None, 
        baudrate: int = 9600, 
        timeout: int = 1, 
        *,
        init_timeout: int = 2,
        message_end: str = '\n',
        simulation: bool = False,
        verbose: bool = False,
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
        self._port = ''
        self._baudrate = 0
        self._timeout = 0
        self.init_timeout = init_timeout
        self.message_end = message_end
        self.flags = deepcopy(self._default_flags)
        
        self.serial = serial.Serial()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        
        self.flags.simulation = simulation
        
        self._logger = logger.getChild(f"{self.__class__.__name__}.{id(self)}")
        self._logger.addHandler(logging.StreamHandler())
        self.verbose = verbose
        return
    
    def __del__(self):
        self.disconnect()
        return
    
    @property
    def port(self) -> str:
        """Device serial port"""
        return self._port
    @port.setter
    def port(self, value:str):
        self._port = value
        self.serial.port = value
        return
    
    @property
    def baudrate(self) -> int:
        """Device baudrate"""
        return self._baudrate
    @baudrate.setter
    def baudrate(self, value:int):
        assert isinstance(value, int), "Ensure baudrate is an integer"
        assert value in serial.Serial.BAUDRATES, f"Ensure baudrate is one of the standard values: {serial.Serial.BAUDRATES}"
        self._baudrate = value
        self.serial.baudrate = value
        return
    
    @property
    def timeout(self) -> int:
        """Device timeout"""
        return self._timeout
    @timeout.setter
    def timeout(self, value:int):
        self._timeout = value
        self.serial.timeout = value
        return
    
    @property
    def connection_details(self) -> dict:
        """Connection details for the device"""
        return {
            'port': self.port,
            'baudrate': self.baudrate,
            'timeout': self.timeout
        }
    
    @property
    def is_connected(self) -> bool:
        """Whether the device is connected"""
        connected = self.flags.connected if self.flags.simulation else self.serial.is_open
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
    
    def clear(self):
        """Clear the input and output buffers"""
        if self.flags.simulation:
            return
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
    
    def query(self, data:Any, lines:bool = True) -> list[str]|None:
        """
        Query the device (i.e. write and read data)

        Args:
            data (Any): data to query
            lines (bool, optional): whether to read multiple lines. Defaults to True.

        Returns:
            list[str]|None: data read from the device, if any
        """
        ret = self.write(str(data))
        if ret:
            response = self.read(lines=lines)
            return response if isinstance(response, list) else [response]
        return
    
    def read(self, lines:bool = False) -> str|list[str]:
        """
        Read data from the device
        
        Args:
            lines (bool, optional): whether to read multiple lines. Defaults to False.

        Returns:
            str|list[str]: line(s) of data read from the device
        """
        data = '' if not lines else []
        try:
            if lines:
                data = self.serial.readlines()
                data = [d.decode("utf-8", "replace").strip() for d in data]
            else:
                data = self.serial.readline().decode("utf-8", "replace").strip()
            self._logger.debug(f"Received: {data!r}")
            self.serial.reset_output_buffer()
        except serial.SerialException as e:
            self._logger.debug(f"Failed to receive data")
        return data

    def write(self, data:str) -> bool:
        """
        Write data to the device

        Args:
            data (str): data to write
        
        Returns:
            bool: whether the write was successful
        """
        assert isinstance(data, str), "Ensure data is a string"
        data = f"{data}{self.message_end}" if not data.endswith(self.message_end) else data
        try:
            self.serial.write(data.encode())
            self._logger.debug(f"Sent: {data!r}")
        except serial.SerialException as e:
            self._logger.debug(f"Failed to send: {data!r}")
            return False
        return True


class SocketDevice:
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
    def __init__(self, host:str, port:int, timeout:int=1, *, simulation:bool=False, verbose:bool = False, **kwargs):
        """
        Initialize SocketDevice class
        
        Args:
            host (str): host for the device
            port (int): port for the device
            timeout (int, optional): timeout for the device. Defaults to 1.
            simulation (bool, optional): whether to simulate the device. Defaults to False.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.flags = deepcopy(self._default_flags)
        
        self.socket.settimeout(self.timeout)
        self.flags.simulation = simulation
        
        self._logger = logger.getChild(f"{self.__class__.__name__}.{id(self)}")
        self._logger.addHandler(logging.StreamHandler())
        self.verbose = verbose
        return

    @property
    def connection_details(self) -> dict:
        """Connection details for the device"""
        return {
            'host': self.host,
            'port': self.port,
            'timeout': self.timeout
        }
    
    @property
    def is_connected(self) -> bool:
        """Whether the device is connected"""
        connected = self.flags.connected if self.flags.simulation else (self.socket.fileno() != -1)
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
    
    def clear(self):
        """Clear the input and output buffers"""
        if self.flags.simulation:
            return
        self.socket.settimeout(0)
        self.socket.recv(1024)
        self.socket.settimeout(self.timeout)
        return

    def connect(self):
        """Connect to the device"""
        if self.is_connected:
            return
        try:
            self.socket.connect((self.host, self.port))
        except socket.error as e:
            self._logger.error(f"Failed to connect to {self.host} at {self.port}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Connected to {self.host} at {self.port}")
        self.flags.connected = True
        return

    def disconnect(self):
        """Disconnect from the device"""
        if not self.is_connected:
            return
        try:
            self.socket.close()
        except socket.error as e:
            self._logger.error(f"Failed to disconnect from {self.host}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Disconnected from {self.host}")
        self.flags.connected = False
        return
    
    def query(self, data:Any, lines:bool = True) -> list[str]|None:
        """
        Query the device

        Args:
            data (Any): data to query

        Returns:
            list[str]|None: data read from the device, if any
        """
        ret = self.write(str(data))
        if ret:
            response = self.read(lines=lines)
            return response if isinstance(response, list) else [response]
        return

    def read(self, lines:bool = False) -> str|list[str]:
        """
        Read data from the device
        
        Args:
            lines (bool, optional): whether to read multiple lines. Defaults to False.
            
        Returns:
            str|list[str]: line(s) of data read from the device
        """
        data = []
        try:
            data = self.socket.recv(1024).decode("utf-8", "replace").strip().split('\n')
            self._logger.debug(f"Received: {data!r}")
        except socket.error as e:
            self._logger.debug(f"Failed to receive data")
        return data

    def write(self, data:str) -> bool:
        """
        Write data to the device

        Args:
            data (str): data to write
        
        Returns:
            bool: whether the write was successful
        """
        data = f"{data}\n" if not data.endswith('\n') else data
        try:
            self.socket.sendall(data.encode())
            self._logger.debug(f"Sent: {data!r}")
        except socket.error as e:
            self._logger.debug(f"Failed to send: {data!r}")
        return False


class DeviceFactory:
    """
    Factory class for creating devices
    
    ## Class methods:
        `createDevice`: create a device
        `createDeviceFromDict`: create a device from a dictionary
    """
    @staticmethod
    def createDevice(device_type:Callable, *args, **kwargs) -> Device:
        """
        Create a device

        Args:
            device_type (Callable): device class to be created

        Returns:
            Device: created device
        """
        return device_type(*args, **kwargs)
    
    @staticmethod
    def createDeviceFromDict(device_dict:dict) -> Device:
        """
        Create a device from a dictionary

        Args:
            device_dict (dict): dictionary containing device details

        Returns:
            Device: created device
        """
        device_type = device_dict.pop('device_type', None)
        if device_type is not None:
            assert callable(device_type), "Ensure device_type is a callable class"
            return DeviceFactory.createDevice(device_type, **device_dict)
        if 'baudrate' in device_dict:
            device_type = SerialDevice
        elif 'host' in device_dict:
            device_type = SocketDevice
        return DeviceFactory.createDevice(device_type, **device_dict)
