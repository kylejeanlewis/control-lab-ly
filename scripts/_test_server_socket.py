# %%
from __future__ import annotations
from collections import deque
import queue
from random import random
import select
import socket
import threading
import time

HOST_IP = socket.gethostbyname(socket.gethostname())
HOST_PORT = 12345
ENCODER = 'utf-8'
BYTESIZE = 1024
DISCONNECT_MESSAGE = '!EXIT'
SHUTDOWN_MESSAGE = '!SHUTDOWN'

class Server:
    def __init__(self, 
        host:str, 
        port:int, 
        trigger:threading.Event = threading.Event(), 
        print_queue:queue.Queue = queue.Queue()
    ):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.address = f'{host}:{port}'
        self.trigger = trigger
        self.print_queue = print_queue
        self.conn_list = deque()
        
        self._printer_thread = None
        self._listener_thread = None
        self._client_threads = dict()
        self._conn_change = threading.Event()
        self._conn_remove = deque()
        self._started = threading.Event()
        return
    
    def __del__(self):
        self.stop()
        return
    
    def start(self):
        if self._started.is_set():
            return
        self.start_server(self.host, self.port, self.trigger, self.print_queue)
        self._started.set()
        return
        
    def stop(self):
        self.trigger.set()
        self._started.clear()
        return
    
    @staticmethod
    def listen(
        server: socket.socket, 
        trigger: threading.Event, 
        print_queue: queue.Queue, 
        threads: dict[str, threading.Thread], 
        conn_list: deque,
        conn_trigger: threading.Event,
        conn_remove: deque,
        started: threading.Event,
        client_handler: callable
    ):
        while not trigger.is_set():
            if conn_trigger.is_set():
                message = f'[CONNECTIONS] {len(conn_list)}\n'
                message += f'{"\n".join([("- "+a) for a in conn_list])}'
                print_queue.put(message)
                while len(conn_remove):
                    del threads[conn_remove.pop()]
                conn_trigger.clear()
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
            thread = threading.Thread(
                target=client_handler, 
                args=(conn,addr,trigger,print_queue,conn_list,conn_trigger,conn_remove)
            )
            thread.start()
            threads[addr] = thread
            
            conn_list.append(addr)
            conn_trigger.set()
        
        trigger.set()
        print_queue.put('[STOP] Termination triggered')
        
        for _,thread in threads.items():
            thread.join()
        server.close()
        print_queue.put('[EXIT] Main')
        
        # Reset
        if conn_trigger.is_set():
            while len(conn_remove):
                del threads[conn_remove.pop()]
            conn_trigger.clear()
        trigger.clear()
        started.clear()
        return
    
    @staticmethod
    def printer(print_queue: queue.Queue, trigger: threading.Event):
        while not trigger.is_set():
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
    
    def start_server(self, 
        host: str, 
        port: int, 
        trigger: threading.Event,
        print_queue: queue.Queue
    ):
        self.server = socket.create_server((host, port))
        print_queue.put(f'[START] Server started {host}:{port}')
        self.server.listen()
        print_queue.put('[START] Listening for incoming connections...')
        
        if isinstance(self._printer_thread, threading.Thread) and self._printer_thread.is_alive():
            pass
        else:
            self._printer_thread = threading.Thread(target=self.printer, args=(print_queue, trigger), daemon=True)
            self._printer_thread.start()
        
        if isinstance(self._listener_thread, threading.Thread) and self._listener_thread.is_alive():
            pass
        else:
            self._listener_thread = threading.Thread(
                target=self.listen, 
                args=(
                    self.server, 
                    trigger, 
                    print_queue, 
                    self._client_threads, 
                    self.conn_list, 
                    self._conn_change,
                    self._conn_remove,
                    self._started,
                    self.handle_client
                )
            )
            self._listener_thread.start()
        return
    
    @staticmethod
    def handle_client(
        conn: socket.socket, 
        addr: str, 
        trigger: threading.Event,
        print_queue: queue.Queue,
        conn_list: deque,
        conn_trigger: threading.Event,
        conn_remove: deque
    ):
        print_queue.put(f'[NEW] {addr}')
        conn.setblocking(False)
        
        while not trigger.is_set():
            try:
                data = conn.recv(BYTESIZE).decode(ENCODER)
            except OSError as e:
                time.sleep(0.01)
                continue
            except (ConnectionResetError, ConnectionAbortedError):
                break
            except KeyboardInterrupt:
                break
            data = data.strip()
            if data:
                print_queue.put(f"[{addr}] {data}")
            
            if data == DISCONNECT_MESSAGE:
                conn.sendall(DISCONNECT_MESSAGE.encode(ENCODER))
                time.sleep(1)
                break
            elif data == SHUTDOWN_MESSAGE:
                conn.sendall(SHUTDOWN_MESSAGE.encode(ENCODER))
                time.sleep(1)
                trigger.set()
                break
            elif data.startswith('[CONNECTED]'):
                time.sleep(1)
                if addr in conn_list:
                    data = f'[CONNECTED] {addr}'
            
            if not data:
                time.sleep(0.01)
                data = f"{random()*10:.3f};{random()*10:.3f};{random()*10:.3f}\n"
            conn.sendall(data.encode(ENCODER))
        
        try:
            conn.sendall(DISCONNECT_MESSAGE.encode(ENCODER))
        except (ConnectionResetError, ConnectionAbortedError):
            pass
        except KeyboardInterrupt:
            pass
        
        conn_remove.append(addr)
        conn_list.remove(addr)
        conn_trigger.set()
        time.sleep(1)
        if len(conn_list) == 0:
            trigger.set()
            print_queue.put('[SHUTDOWN] No active connections')
        print_queue.put(f'[EXIT] {addr}')
        return
    
# %%
server = Server(HOST_IP, HOST_PORT)
server.start()

# %%
