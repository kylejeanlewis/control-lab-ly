# %% -*- coding: utf-8 -*-
# Standard Library imports
from __future__ import annotations
from collections import deque
from copy import deepcopy
import queue
from random import random
import select
import socket
import threading
import time
from typing import Callable, Mapping

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

class Server:
    
    _default_keywords = dict(connect=CONNECT_MESSAGE, disconnect=DISCONNECT_MESSAGE, shutdown=SHUTDOWN_MESSAGE)
    def __init__(self, 
        host: str, 
        port: int,
        terminate: threading.Event = threading.Event(), 
        print_queue: queue.Queue = queue.Queue(),
        *,
        bytesize: int = 1024,
        encoder: str = 'utf-8',
        keywords: Mapping[str]|None = None
    ):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.address = f'{host}:{port}'
        
        self.print_queue = print_queue
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
        time.sleep(1)
        return
    
    def start(self, blocking: bool = False):
        if self.triggers['started'].is_set():
            return
        self.start_server(
            self.host, 
            self.port, 
            triggers = self.triggers['terminate'], 
            print_queue = self.print_queue,
            blocking = blocking
        )
        return
        
    def stop(self):
        self.triggers['terminate'].set()
        self.triggers['started'].clear()
        return
    
    def start_server(self, 
        host: str, 
        port: int, 
        client_handler: Callable|None = None,
        *,
        terminate: threading.Event|None = None,
        print_queue: queue.Queue|None = None,
        blocking: bool = False,
        **kwargs
    ):
        client_handler = self.handle_client if client_handler is None else client_handler
        self.triggers['terminate'] = self.triggers['terminate'] if terminate is None else terminate
        print_queue = self.print_queue if print_queue is None else print_queue
        
        self.server = socket.create_server((host, port))
        self.triggers['started'].set()
        print_queue.put(f'[START] Server started {host}:{port}')
        
        self.server.listen()
        print_queue.put('[START] Listening for incoming connections...')
        
        if not (isinstance(self._printer_thread, threading.Thread) and self._printer_thread.is_alive()):
            self._printer_thread = threading.Thread(target=self.printer, args=(print_queue, self.triggers['jam']), daemon=True)
            self._printer_thread.start()
        
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
            thread = threading.Thread(
                target=client_handler, 
                args=(conn, addr),
                kwargs=kwargs
            )
            thread.start()
            threads[addr] = thread
            
            connections.append(addr)
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
    
    @staticmethod
    def handle_client(
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
            data = read(conn, bytesize=bytesize, encoder=encoder)
            if not data:
                time.sleep(0.01)
                continue
            elif data.strip():
                print_queue.put(f"[{addr}] {data}")
            data = data.strip()
            
            if data == disconnect_message:
                break
            elif data == shutdown_message:
                write(shutdown_message, conn, encoder=encoder, wait= True)
                triggers['terminate'].set()
                break
            elif data.startswith(connect_message):
                time.sleep(1)
                if addr in connections:
                    data = f'{connect_message} {addr}'
            
            if not data:
                time.sleep(0.01)
                data = f"{random()*10:.3f};{random()*10:.3f};{random()*10:.3f}\n"
            write(data, conn, encoder=encoder)
        
        write(disconnect_message, conn, encoder=encoder, wait= True)
        
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
  
    