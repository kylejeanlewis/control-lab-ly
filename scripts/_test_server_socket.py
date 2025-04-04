# %%
from collections import deque
from copy import deepcopy
import queue
from random import random
import select
import socket
import threading
import time
from typing import Mapping, Callable

BYTESIZE = 1024
ENCODER = 'utf-8'

CONNECT_MESSAGE = '[CONNECTED]'
DISCONNECT_MESSAGE = '!EXIT'
SHUTDOWN_MESSAGE = '!SHUTDOWN'

# %%
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
    
# %%
host_ip = socket.gethostbyname(socket.gethostname())
host_port = 12345

# %%
server = Server(host_ip, host_port)
server.start(blocking=True)

# %%
