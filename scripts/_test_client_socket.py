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

def read_all(connection: socket.socket, *, bytesize: int = BYTESIZE, encoder: str = ENCODER) -> str:
    data = ''
    while True:
        out = read(connection, bytesize=bytesize, encoder=encoder)
        data += out
        if not out or len(data) > bytesize:
            break
    return data

def read(connection: socket.socket, *, bytesize: int = BYTESIZE, encoder: str = ENCODER) -> str:
    out = ''
    try:
        out = connection.recv(bytesize).decode(encoder, "replace")
    except OSError as e:
        pass
    except TimeoutError:
        pass
    except (ConnectionResetError, ConnectionAbortedError):
        pass
    except KeyboardInterrupt:
        pass
    return out

def write(data: str, connection: socket.socket, *, encoder: str = ENCODER, wait: bool = False):
    try:
        connection.sendall(data.encode(encoder))
        if wait:
            time.sleep(1)
    except (ConnectionResetError, ConnectionAbortedError):
        pass
    except KeyboardInterrupt:
        pass
    return

class Client:
    
    _default_keywords = dict(connect=CONNECT_MESSAGE, disconnect=DISCONNECT_MESSAGE, shutdown=SHUTDOWN_MESSAGE)
    def __init__(self,
        host: str, 
        port: int, 
        terminate: threading.Event = threading.Event(), 
        print_queue: queue.Queue = queue.Queue(),
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
        
        self.print_queue = print_queue
        self.triggers = dict(
            terminate = terminate,
        )
        self._printer_thread = None
        return
    
    def __del__(self):
        self.disconnect()
        return
    
    @property
    def is_connected(self) -> bool:
        return (self.conn.fileno() == self._current_socket_ref) and (self.conn.fileno() != -1)
    
    def connect(self):
        if self.is_connected:
            return
        self.start_client(self.host, self.port)
        return
    
    def disconnect(self):
        if not self.is_connected:
            return
        self.query(self.keywords['disconnect'])
        self.triggers['terminate'].set()
        self.conn.close()
        return
    
    def shutdown(self):
        self.query(self.keywords['shutdown'])
        return
    
    def start_client(self, host:str, port:int):
        self.conn = socket.create_connection((host, port))
        success_message = f'{self.keywords["connect"]} {host}:{port}'
        self.print_queue.put(f'{self.keywords["connect"]} {host}:{port}')
        self.conn.settimeout(0)
        self.conn.sendall(success_message.encode(ENCODER))
        time.sleep(1)
        
        data = ''
        while self.keywords["connect"] not in data:
            data += self.read()
        self.print_queue.put(f"[RECV] {data!r}")
        self.address = data.replace(f'{self.keywords["connect"]} ', '')
        self._current_socket_ref = self.conn.fileno()
        
        if not (isinstance(self._printer_thread, threading.Thread) and self._printer_thread.is_alive()):
            self._printer_thread = threading.Thread(target=self.printer, args=(self.print_queue, self.triggers['terminate']), daemon=True)
            self._printer_thread.start()
        return

    def read(self) -> str:
        return read(self.conn, bytesize=self.bytesize, encoder=self.encoder)

    def read_all(self) -> str:
        return read_all(self.conn, bytesize=self.bytesize, encoder=self.encoder)

    def query(self, data: str, multi_line: bool = True) -> str|None:
        assert isinstance(data, str), 'Data must be a string'
        assert self.is_connected, 'Client is not connected'
        
        self.write(data)
        self.print_queue.put(f'[SENT] {data!r}')
        data = self.read().strip() if not multi_line else self.read_all().strip()
        
        if data == self.keywords['disconnect']:
            self.print_queue.put(f'[EXIT] {self.host}:{self.port}')
            self.disconnect()
        elif data == self.keywords['shutdown']:
            self.print_queue.put(f'[SHUTDOWN] {self.host}:{self.port}')
            self.disconnect()
        else:
            self.print_queue.put(f"[RECV] {data!r}")
        return data
    
    def write(self, data: str):
        return write(data, self.conn, encoder=ENCODER)
    
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
        return
    
# %%
import socket
from _test_socket import Client

host_ip = socket.gethostbyname(socket.gethostname())
host_port = 12345

# %%
client = Client(host_ip, host_port)
client.connect()

# %%
client1 = Client(host_ip, host_port)
client1.connect()
client2 = Client(host_ip, host_port)
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
# %%
from _test_socket import Client