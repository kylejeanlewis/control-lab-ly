import pytest
import threading
import time

from controllably.core.control import Controller, Proxy, TwoTierQueue
from controllably.core.interpreter import JSONInterpreter
from controllably.examples.control.socket.utils import SocketClient, SocketServer

HOST = '127.0.0.1'
PORT = 12345

@pytest.mark.socket
def test_client_server():
    worker = Controller('model', JSONInterpreter())
    worker.start()
    worker_terminate = threading.Event()
    worker_thread = threading.Thread(target=SocketServer.start_server, args=[HOST,PORT,worker], kwargs={'terminate':worker_terminate}, daemon=True)
    worker_thread.start()
    time.sleep(1)

    user = Controller('view', JSONInterpreter())
    user_terminate = threading.Event()
    user_thread = threading.Thread(target=SocketClient.start_client, args=[HOST,PORT,user], kwargs={'terminate':user_terminate}, daemon=True)
    user_thread.start()
    time.sleep(2)
    assert worker_thread.is_alive()
    assert user_thread.is_alive()
    
    q = TwoTierQueue()
    worker.register(q, 'TEST1')
    time.sleep(1)
    assert worker.registry == {'TEST1': [worker.address]}
    assert user.registry == {'TEST1': [worker.address]}
    
    p = Proxy(TwoTierQueue, 'TEST1')
    p.bindController(user)
    p.put_nowait('12345')
    assert p.qsize() == 1
    assert p.get() == '12345'
    
    user.callbacks['request'][f"{HOST}:{PORT}"](b'[EXIT]')
    worker_terminate.set()
    user_thread.join()
    worker_thread.join()
    assert not user_thread.is_alive()
    assert not worker_thread.is_alive()

@pytest.mark.socket
def test_hub_spoke():
    hub = Controller('relay', JSONInterpreter())
    hub_terminate = threading.Event()
    hub_thread = threading.Thread(target=SocketServer.start_server, args=[HOST,PORT,hub], kwargs={'terminate':hub_terminate}, daemon=True)
    hub_thread.start()
    time.sleep(1)
    
    worker = Controller('model', JSONInterpreter())
    worker.start()
    worker_terminate = threading.Event()
    worker_thread = threading.Thread(target=SocketClient.start_client, args=[HOST,PORT,worker,True], kwargs={'terminate':worker_terminate}, daemon=True)
    worker_thread.start()

    user = Controller('view', JSONInterpreter())
    user_terminate = threading.Event()
    user_thread = threading.Thread(target=SocketClient.start_client, args=[HOST,PORT,user,True], kwargs={'terminate':user_terminate}, daemon=True)
    user_thread.start()
    time.sleep(3)
    assert hub_thread.is_alive()
    assert worker_thread.is_alive()
    assert user_thread.is_alive()
    
    q = TwoTierQueue()
    worker.register(q, 'TEST1')
    time.sleep(1)
    assert worker.registry == {'TEST1': [worker.address]}
    assert user.registry == {'TEST1': [worker.address]}
    
    p = Proxy(TwoTierQueue, 'TEST1')
    p.bindController(user)
    p.put_nowait('12345')
    assert p.qsize() == 1
    assert p.get() == '12345'
    
    user.callbacks['request'][f"{HOST}:{PORT}"](b'[EXIT]')
    worker.callbacks['data'][f"{HOST}:{PORT}"](b'[EXIT]')
    hub_terminate.set()
    worker_terminate.set()
    user_terminate.set()
    user_thread.join()
    worker_thread.join()
    hub_thread.join()
    assert not user_thread.is_alive()
    assert not worker_thread.is_alive()
    assert not hub_thread.is_alive()
