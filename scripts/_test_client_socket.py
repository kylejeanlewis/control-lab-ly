# %%
from copy import deepcopy
import queue
import socket
import threading
import time
from typing import Mapping

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


# %%
host_ip = socket.gethostbyname(socket.gethostname())
host_port = 12345

# %%
print_queue = queue.Queue()
trigger = threading.Event()
printer_thread = threading.Thread(target=SocketUtils.printer, args=(print_queue, trigger))
printer_thread.start()

# %%
client = Client(host_ip, host_port, print_queue=print_queue)
client.connect()

# %%
client1 = Client(host_ip, host_port)
client1.connect()
client2 = Client(host_ip, host_port, print_queue=print_queue)
client2.connect()

# %%
client.read()
# %%
client.read()
# %%
client.query('Hello World!')
# %%
client.query('')
# %%
client.query(' ')
# %%
client.disconnect()
# %%
# time.sleep(3)
client1.disconnect()
client2.disconnect()
