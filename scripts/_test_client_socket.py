# %%
import queue
import socket
import threading
import time

HOST_IP = socket.gethostbyname(socket.gethostname())
HOST_PORT = 12345
ENCODER = 'utf-8'
BYTESIZE = 1024
DISCONNECT_MESSAGE = '!EXIT'
SHUTDOWN_MESSAGE = '!SHUTDOWN'

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
            print(print_queue.get_nowait())
            print_queue.task_done()
        except queue.Empty:
            pass
        except KeyboardInterrupt:
            break
    print('[EXIT] Printer')
    return

class Client:
    def __init__(self, host:str, port:int, trigger:threading.Event = threading.Event()):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.address = ''
        self.trigger = trigger
        self.print_queue = queue.Queue()
        self._printer_thread = None
        return
    
    def __del__(self):
        self.disconnect()
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
    
    def connect(self):
        self.start_client(self.host, self.port)
        return
    
    def disconnect(self):
        self.query(DISCONNECT_MESSAGE)
        return
    
    def shutdown(self):
        self.query(SHUTDOWN_MESSAGE)
        return
    
    def start_client(self, host:str, port:int):
        self.conn = socket.create_connection((host, port))
        success_message = f'[CONNECTED] {host}:{port}'
        self.print_queue.put(f'[CONNECTED] {host}:{port}')
        self.conn.settimeout(0)
        self.conn.sendall(success_message.encode(ENCODER))
        time.sleep(1)
        data = ''
        while '[CONNECTED]' not in data:
            data += self.read()
        self.print_queue.put(f"[RECV] {data!r}")
        self.address = data.replace('[CONNECTED] ', '')
        
        if isinstance(self._printer_thread, threading.Thread) and self._printer_thread.is_alive():
            pass
        else:
            self._printer_thread = threading.Thread(target=printer, args=(self.print_queue, self.trigger), daemon=True)
            self._printer_thread.start()
        return

    def read(self) -> str:
        conn = self.conn
        data = ''
        flag = False
        while True:
            try:
                out = conn.recv(BYTESIZE).decode("utf-8", "replace")
            except OSError as e:
                if flag:
                    break
                time.sleep(0.01)
                flag = True
                continue
            except TimeoutError:
                break
            except (ConnectionResetError, ConnectionAbortedError):
                break
            except KeyboardInterrupt:
                break
            data += out
            if not out or len(data)>BYTESIZE:
                break
        return data.strip()

    def query(self, data: str) -> str|None:
        assert isinstance(data, str), 'Data must be a string'
        conn = self.conn
        trigger = self.trigger
        
        try:
            conn.sendall(data.encode(ENCODER))
        except (ConnectionResetError, ConnectionAbortedError):
            return
        except KeyboardInterrupt:
            return
        self.print_queue.put(f'[SENT] {data!r}')
        
        time.sleep(1)
        data = self.read()
        
        if data == DISCONNECT_MESSAGE:
            conn.sendall(DISCONNECT_MESSAGE.encode(ENCODER))
            self.print_queue.put(f'[EXIT] {HOST_IP}:{HOST_PORT}')
            time.sleep(1)
            trigger.set()
        elif data == SHUTDOWN_MESSAGE:
            conn.sendall(SHUTDOWN_MESSAGE.encode(ENCODER))
            self.print_queue.put(f'[SHUTDOWN] {HOST_IP}:{HOST_PORT}')
            time.sleep(1)
            trigger.set()
        else:
            self.print_queue.put(f"[RECV] {data!r}")
        return data
    
# %%
client = Client(HOST_IP, HOST_PORT)
client.connect()

# %%
client1 = Client(HOST_IP, HOST_PORT)
client1.connect()
client2 = Client(HOST_IP, HOST_PORT)
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
time.sleep(3)
client1.shutdown()
# %%