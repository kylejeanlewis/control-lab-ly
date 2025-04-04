# -*- coding: utf-8 -*-
""" 
This module provides classes for handling connections to serial and socket devices.
    
## Classes:
    `SocketUtils`: Socket utility class for handling socket connections
    `Server`: Server class for handling socket connections
    `Client`: Client class for handling socket connections
    
## Functions:
    `get_addresses`: Get the appropriate addresses for current machine
    `get_host`: Get the host IP address for current machine
    `get_node`: Get the unique identifier for current machine
    `get_ports`: Get available serial ports connected to current machine
    `match_current_ip_address`: Match the current IP address of the machine
    
<i>Documentation last updated: 2024-11-12</i>
"""
# Standard library imports
from __future__ import annotations
import ipaddress
import logging
import socket
import uuid

# Third party imports
import serial                       # pip install pyserial

# Local application imports
from .archives._connection import *

_logger = logging.getLogger("controllably.core")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.addFilter(logging.Filter(__name__+'.'))
logger.addHandler(handler)

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
    local_ips = socket.gethostbyname_ex(hostname)[2]
    success = False
    for local_ip in local_ips:
        local_network = f"{'.'.join(local_ip.split('.')[:-1])}.0/24"
        if ipaddress.ip_address(ip_address) in ipaddress.ip_network(local_network):
            success = True
            break
    return success

class SocketUtils:
    """ 
    Socket utility class for handling socket connections
    
    ### Methods:
        `readAll`: read all data from the connection
        `read`: read data from the connection
        `write`: write data to the connection
        `printer`: print data from the print queue
    """
    
    def __init__(self):
        return
    
    @staticmethod
    def readAll(connection: socket.socket, *, bytesize: int = BYTESIZE, encoder: str = ENCODER, ignore: bool = True) -> str|None:
        """ 
        Read all data from the connection
        
        Args:
            connection (socket.socket): connection socket
            bytesize (int, optional): bytesize for reading data. Defaults to BYTESIZE.
            encoder (str, optional): encoder for reading data. Defaults to ENCODER.
            ignore (bool, optional): whether to ignore errors. Defaults to True.
            
        Returns:
            str|None: data read from the connection, if any
        """
        data = ''
        flag = False
        while True:
            out = ''
            try:
                out = connection.recv(bytesize).decode(encoder, "replace").replace('\uFFFD', '')
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
        """
        Read data from the connection
        
        Args:
            connection (socket.socket): connection socket
            bytesize (int, optional): bytesize for reading data. Defaults to BYTESIZE.
            encoder (str, optional): encoder for reading data. Defaults to ENCODER.
            ignore (bool, optional): whether to ignore errors. Defaults to True.
            
        Returns:
            str|None: data read from the connection, if any
        """
        out = ''
        try:
            out = connection.recv(bytesize).decode(encoder, "replace").replace('\uFFFD', '')
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
        """
        Write data to the connection
        
        Args:
            data (str): data to write
            connection (socket.socket): connection socket
            encoder (str, optional): encoder for writing data. Defaults to ENCODER.
            wait (bool, optional): whether to wait after writing data. Defaults to False.
            ignore (bool, optional): whether to ignore errors. Defaults to False.
        """
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
        """
        Print data from the print queue
        
        Args:
            print_queue (queue.Queue): print queue
            jam (threading.Event): jam event
        """
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
    """ 
    Server class for handling socket connections
    
    ### Constructor:
        `host` (str): host for the server
        `port` (int): port for the server
        `terminate` (threading.Event, optional): termination event. Defaults to threading.Event().
        `print_queue` (queue.Queue|None, optional): print queue. Defaults to None.
        `bytesize` (int, optional): bytesize for reading data. Defaults to 1024.
        `encoder` (str, optional): encoder for reading data. Defaults to 'utf-8'.
        `keywords` (Mapping[str,str]|None, optional): keywords for messages. Defaults to None.
        
    ### Attributes and properties:
        `server` (socket.socket): server socket
        `host` (str): server host
        `port` (int): server port
        `address` (str): server address
        `use_external_printer` (bool): whether to use an external printer
        `print_queue` (queue.Queue): print queue
        `connections` (deque): list of active connections
        `removal_list` (deque): list of connections to remove
        `triggers` (dict[str, threading.Event]): triggers for the server
        `bytesize` (int): bytesize for reading data
        `encoder` (str): encoder for reading data
        `keywords` (Mapping[str,str]): keywords for messages
        `client_threads` (dict[str, threading.Thread]): client threads
        `_printer_thread` (threading.Thread): printer thread
        `_listener_thread` (threading.Thread): listener thread
        
    ### Methods:
        `start`: start the server
        `stop`: stop the server
        `startServer`: start the server
        `startPrinter`: start the printer thread
        `listen`: listen for incoming connections
        `handleClient`: handle client connections
        
    ### Static methods:
        `read`: read data from the connection
        `readAll`: read all data from the connection
        `write`: write data to the connection
        `printer`: print data from the print queue
    """
    
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
        """
        Initialize Server class
        
        Args:
            host (str): host for the server
            port (int): port for the server
            terminate (threading.Event, optional): termination event. Defaults to threading.Event().
            print_queue (queue.Queue|None, optional): print queue. Defaults to None.
            bytesize (int, optional): bytesize for reading data. Defaults to 1024.
            encoder (str, optional): encoder for reading data. Defaults to 'utf-8'.
            keywords (Mapping[str]|None, optional): keywords for messages. Defaults to None.
        """
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
        """
        Listen for incoming connections
        
        Args:
            server (socket.socket): server socket
            client_handler (Callable): client handler function
            triggers (dict[str, threading.Event]): termination triggers
            print_queue (queue.Queue): print queue
            connections (deque): list of active connections
            removal_list (deque): list of connections to remove
            threads (dict[str, threading.Thread]): client threads
        """
        while not triggers['terminate'].is_set():
            if triggers['update_connections'].is_set():
                message = f'[CONNECTIONS] {len(connections)}\n'
                message += "\n".join([("- "+a) for a in connections])
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
            addr = ":".join([str(a) for a in addr])
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
        """ 
        Handle client connections
        
        Args:
            conn (socket.socket): connection socket
            addr (str): connection address
            triggers (dict[str, threading.Event]): termination triggers
            print_queue (queue.Queue): print queue
            connections (deque): list of active connections
            removal_list (deque): list of connections to remove
            keywords (Mapping[str,str]): keywords for messages
        """
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
    """
    Client class for handling socket connections
    
    ### Constructor:
        `host` (str): host for the client
        `port` (int): port for the client
        `terminate` (threading.Event, optional): termination event. Defaults to threading.Event().
        `print_queue` (queue.Queue|None, optional): print queue. Defaults to None.
        `bytesize` (int, optional): bytesize for reading data. Defaults to 1024.
        `encoder` (str, optional): encoder for reading data. Defaults to 'utf-8'.
        `keywords` (Mapping[str,str]|None, optional): keywords for messages. Defaults to None.
        
    ### Attributes and properties:
        `conn` (socket.socket): client socket
        `host` (str): client host
        `port` (int): client port
        `address` (str): client address
        `_current_socket_ref` (int): current socket reference
        `bytesize` (int): bytesize for reading data
        `encoder` (str): encoder for reading data
        `keywords` (Mapping[str,str]): keywords for messages
        `use_external_printer` (bool): whether to use an external printer
        `print_queue` (queue.Queue): print queue
        `triggers` (dict[str, threading.Event]): triggers for the client
        `_printer_thread` (threading.Thread): printer thread
        `_listener_thread` (threading.Thread): listener thread
        
    ### Methods:
        `connect`: connect to the client
        `disconnect`: disconnect from the client
        `shutdown`: shutdown the client
        `startClient`: start the client
        `startPrinter`: start the printer thread
        `read`: read data from the client
        `readAll`: read all data from the client
        `query`: query the client (i.e. write and read data)
        `write`: write data to the client
    """
    
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
        """
        Initialize Client class
        
        Args:
            host (str): host for the client
            port (int): port for the client
            terminate (threading.Event, optional): termination event. Defaults to threading.Event().
            print_queue (queue.Queue|None, optional): print queue. Defaults to None.
            bytesize (int, optional): bytesize for reading data. Defaults to 1024.
            encoder (str, optional): encoder for reading data. Defaults to 'utf-8'.
            keywords (Mapping[str, str]|None, optional): keywords for messages. Defaults to None.
        """
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
        """Whether the client is connected"""
        try:
            self.conn.sendall('\n'.encode())
            self.conn.sendall('\n'.encode())
        except OSError:
            return False
        return (self.conn.fileno() == self._current_socket_ref) and (self.conn.fileno() != -1)
    
    def connect(self):
        """Connect to the client"""
        if self.is_connected:
            return
        self.startClient(self.host, self.port)
        return
    
    def disconnect(self):
        """Disconnect from the client"""
        SocketUtils.write(self.keywords['disconnect'], self.conn, encoder=self.encoder, wait=True, ignore=True)
        self.triggers['terminate'].set()
        self.conn.close()
        self._current_socket_ref = -1
        return
    
    def shutdown(self):
        """Shutdown the client"""
        self.query(self.keywords['shutdown'])
        return
    
    def startClient(self, host:str, port:int):
        """ 
        Start the client
        
        Args:
            host (str): host for the client
            port (int): port for the client
        """
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
        """Start the printer thread"""
        if not (isinstance(self._printer_thread, threading.Thread) and self._printer_thread.is_alive()):
            self._printer_thread = threading.Thread(target=SocketUtils.printer, args=(self.print_queue, self.triggers['terminate']), daemon=True)
            self._printer_thread.start()
        return
    
    def read(self) -> str:
        """Read data from the client"""
        return SocketUtils.read(self.conn, bytesize=self.bytesize, encoder=self.encoder)

    def readAll(self) -> str:
        """Read all data from the client"""
        return SocketUtils.readAll(self.conn, bytesize=self.bytesize, encoder=self.encoder)

    def query(self, data: str, multi_line: bool = False) -> str|None:
        """
        Query the client (i.e. write and read data)
        
        Args:
            data (str): data to query
            multi_line (bool, optional): whether to read multiple lines. Defaults to False.
            
        Returns:
            str|None: data read from the client, if any
        """
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
        """
        Write data to the client
        
        Args:
            data (str): data to write
            
        Returns:
            bool: whether the write was successful
        """
        try:
            SocketUtils.write(data, self.conn, encoder=self.encoder, wait=True)
        except OSError:
            return False
        except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
            self.print_queue.put(f'[ERROR] Connection lost {self.host}:{self.port}')
            self.disconnect()
            return False
        return True





