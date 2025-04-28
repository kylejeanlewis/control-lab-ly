import pytest
import builtins
import logging
import threading
import time

from ..context import controllably
from controllably.core.control import (
    ClassMethods, TwoTierQueue, Proxy, Controller, handle_client, start_server, start_client, BYTESIZE
)
from controllably.core.interpreter import JSONInterpreter
from controllably.core.connection import get_host

HOST = '127.0.0.1'
PORT = 12345
MESSAGING = {
    "request":{
        "object_id": "",
        "method": "",
        "args": [""],
        "kwargs": {"":""},

        "address": {"sender": [""], "target": [""]},
        "request_id": "",
        "priority": False,
        "rank": None
    },
    "reply": {
        "data": None,
        "status": "",

        "address": {"sender": [""], "target": [""]},
        "request_id": "",
        "reply_id": "",
        "priority": False,
        "rank": None
    }
}

class MyClass:
    def __init__(self, prop1:int):
        self.prop1 = prop1
        self.prop2 = 'abc'
    
    @staticmethod
    def static_method(arg1:str) -> str:
        """Test method"""
        return f"Executed {arg1}"
        
    @classmethod
    def class_method(cls, arg1:str) -> str:
        """Test method"""
        return f"Executed {arg1}"
        
    def method(self, arg1:str) -> str:
        """Test method"""
        return f"Executed {arg1}"
    
    def method_exception(self, arg1:str, *args, kwarg1:str, **kwargs):
        """Test method"""
        raise ValueError(f"Executed {arg1} {kwarg1}")

def test_class_methods():
    methods = {'method1': {'parameters': {'args': [('param1', None, 'str')]}}}
    class_methods = ClassMethods(name='MyClass', methods=methods)
    assert class_methods.name == 'MyClass'
    assert class_methods.methods == methods

def test_two_tier_queue():
    queue = TwoTierQueue()
    assert queue.empty()
    queue.put_nowait('item1')
    assert not queue.empty()
    assert queue.qsize() == 1
    assert not queue.full()
    queue.put('impt2', priority=True, rank = 3)
    assert queue.priority_counter == 1
    assert queue.qsize() == 2
    assert queue.normal_queue.qsize() == 1
    assert queue.high_priority_queue.qsize() == 1
    queue.put_first('top')
    
    assert queue.get_nowait() == 'top'
    assert not queue.last_used_queue_normal
    queue.task_done()
    assert queue.get_nowait() == 'impt2'
    queue.task_done()
    assert not queue.empty()
    assert queue.get_nowait() == 'item1'
    assert queue.last_used_queue_normal
    queue.task_done()
    assert queue.empty()
    queue.join()
    
    queue.put_nowait('item1')
    queue.put('impt2', priority=True, rank = 3)
    queue.put_first('top')
    assert queue.qsize() == 3
    assert queue.normal_queue.qsize() == 1
    assert queue.high_priority_queue.qsize() == 2
    assert queue.priority_counter == 2
    queue.get_nowait()
    assert not queue.last_used_queue_normal
    queue.reset()
    assert queue.qsize() == 0
    assert queue.normal_queue.qsize() == 0
    assert queue.high_priority_queue.qsize() == 0
    assert queue.priority_counter == 0
    assert queue.last_used_queue_normal

def test_two_tier_queue_delayed_get():
    queue = TwoTierQueue()
    assert queue.empty()
    timer = threading.Timer(1, queue.put_nowait, args=['item1'])
    timer.start()
    assert queue.get() == 'item1'
    queue.task_done()
    timer.join()
    
    timer = threading.Timer(1, queue.put_nowait, args=['item2'])
    timer.start()
    assert queue.get(timeout=0.5) is None
    timer.join()
    assert queue.get(timeout=0.5) == 'item2'
    queue.task_done()
    
    timer = threading.Timer(1, queue.put_nowait, args=['item3'])
    timer.start()
    assert queue.get(block=False) is None
    timer.join()
    assert queue.get(block=False) == 'item3'
    queue.task_done()

@pytest.fixture
def mock_controllers():
    worker = Controller('model', JSONInterpreter())
    user = Controller('view', JSONInterpreter())
    worker.subscribe(user.receiveData, 'data')
    user.subscribe(worker.receiveRequest, 'request')
    return worker, user

@pytest.fixture
def mock_controllers_hub():
    hub = Controller('relay', JSONInterpreter())
    worker = Controller('model', JSONInterpreter())
    user = Controller('view', JSONInterpreter())
    worker.subscribe(hub.relayData,'data', relay=True)
    hub.subscribe(user.receiveData,'data')
    user.subscribe(hub.relayRequest,'request', relay=True)
    hub.subscribe(worker.receiveRequest,'request')
    return worker, user, hub

def test_proxy_with_instance(mock_controllers):
    worker, user = mock_controllers
    # with instance
    test_obj_worker = MyClass(0)
    worker.register(test_obj_worker)
    worker.start()
    assert len(worker.registry) == 1
    
    test_obj_user = MyClass(1)
    object_id = str(id(test_obj_worker))
    proxy1 = Proxy(test_obj_user, object_id)
    assert proxy1.object_id == object_id
    assert proxy1.prime == test_obj_user
    assert proxy1.controller is None
    assert not proxy1.remote
    assert proxy1.method("1") == "Executed 1"
    assert proxy1.prop1 == 1
    proxy1.prop1 = 2
    assert proxy1.prop1 == 2
    
    proxy1.bindController(user)
    assert proxy1.controller == user
    assert proxy1.remote
    assert proxy1.class_method("1") == "Executed 1"
    assert proxy1.prop1 == 0
    proxy1.prop1 = 3
    assert proxy1.prop1 == 3
    assert test_obj_worker.prop1 == 3
    
    outs = []
    for i in range(10):
        out = proxy1.static_method(str(i))
        outs.append(out)
    assert outs == [f"Executed {i}" for i in range(10)]
    
    with pytest.raises(ValueError):
        proxy1.method_exception("1", kwarg1="2")
    
    methods = user.getMethods()
    assert len(methods) == 1
    assert list(methods.keys())[0] == object_id
    assert methods[object_id].get('name') == 'MyClass'
    assert set(methods[object_id].get('methods',{}).keys()) == {'method', 'method_exception', 'class_method', 'static_method'}
    
    worker.stop()
    worker.unregister(object_id)
    assert len(worker.registry) == 0
    
    controller = proxy1.releaseController()
    assert controller == user
    assert proxy1.controller is None
    assert not proxy1.remote
    
def test_proxy_with_class(mock_controllers):
    worker, user = mock_controllers
    
    # with class
    test_obj_worker = MyClass(10)
    worker.register(test_obj_worker, 'TEST2')
    worker.start()
    
    proxy2 = Proxy(MyClass, 'TEST2')
    assert proxy2.prime == MyClass
    assert proxy2.object_id == 'TEST2'
    assert proxy2.controller is None
    assert not proxy2.remote
    with pytest.raises(TypeError):
        proxy2.method("1")
    with pytest.raises(AttributeError):
        _ = proxy2.prop1
    
    proxy2.bindController(user)
    assert proxy2.controller == user
    assert proxy2.remote
    assert proxy2.method("1") == "Executed 1"
    assert proxy2.prop1 == 10
    proxy2.prop1 = 20
    assert proxy2.prop1 == 20
    
    proxy2.remote = False
    with pytest.raises(TypeError):
        _ = proxy2.prop1
    with pytest.raises(TypeError):
        proxy2.prop1 = 1
    
    controller = proxy2.releaseController()
    assert controller == user
    assert proxy2.controller is None
    assert not proxy2.remote
    
def test_proxy_class_inheritance(mock_controllers):
    worker, user = mock_controllers
    worker.start()
    test_obj_worker = MyClass(10)
    worker.register(test_obj_worker, 'TEST2')
    
    proxy2 = Proxy(MyClass, 'TEST2')
    new_class = proxy2.__class__
    assert issubclass(new_class, Proxy)
    assert issubclass(new_class, MyClass)
    proxy2.bindController(user)
    proxy2.static_method('1')
    
def test_controller(mock_controllers_hub,caplog):
    worker, user, hub = mock_controllers_hub
    assert worker.registry == {}
    assert user.registry == {}
    assert hub.registry == {}
    
    test_obj = MyClass(10)
    worker.register(test_obj, 'TEST1')
    with caplog.at_level(logging.WARNING):
        worker.register(test_obj, 'TEST1')
        assert "MyClass_TEST1 already registered" in caplog.text
    registry = {'TEST1': [str(id(worker))]}
    assert worker.registry == registry
    assert user.registry == registry
    assert hub.registry == {}
    
    other_worker = Controller('model', JSONInterpreter())
    other_worker.subscribe(hub.relayData,'data', relay=True)
    hub.subscribe(other_worker.receiveRequest,'request')
    test_obj_other = MyClass(10)
    other_worker.register(test_obj_other, 'TEST1')
    with pytest.raises(LookupError):
        _ = user.registry

    with caplog.at_level(logging.WARNING):
        other_worker.unregister(old_object=test_obj_other)
        assert f"Object not found: MyClass [{str(id(test_obj_other))}]" in caplog.text
    with caplog.at_level(logging.WARNING):
        other_worker.unregister('TEST2')
        assert f"Object not found: TEST2" in caplog.text

@pytest.mark.parametrize("object_id, method_name, args, kwargs, outcome", [
    ('WRONG_ID', 'method_unknown', ['abc'], {}, KeyError),
    ('TEST1', 'method_unknown', ['abc'], {}, AttributeError),
    ('TEST1', 'method', ['abc'], {}, None)
])
def test_controller_execute_method(object_id, method_name, args, kwargs, outcome, mock_controllers):
    worker, user = mock_controllers
    worker.start()
    test_obj = MyClass(10)
    worker.register(test_obj, 'TEST1')
    
    command = dict(
        object_id = object_id,
        method = method_name,
        args = args,
        kwargs = kwargs
    )
    request_id = user.transmitRequest(command, target=[str(id(worker))])
    response: dict = user.retrieveData(request_id, data_only=False)
    data = response.get('data')
    if response.get('status', '') != 'completed':
        error_type_name, message = data.split('!!', maxsplit=1)
        error_type = getattr(builtins, error_type_name, Exception)
        exception = error_type(message)
        assert isinstance(exception, outcome)
    else:
        assert data == "Executed abc"
    worker.stop()

@pytest.mark.parametrize("method_name, args, kwargs, outcome", [
    ('getattr', ['WRONG_ID','abc'], {}, KeyError),
    ('getattr', ['TEST1','abc'], {}, AttributeError),
    ('getattr', ['TEST1','prop1'], {}, 10),
    ('getattr', ['TEST1',['prop1','prop2']], {}, {'prop1': 10, 'prop2': 'abc'}),
    ('setattr', ['TEST1','prop1'], {}, ValueError),
    ('setattr', ['TEST1','prop1', 1000], {}, 1000),
    ('delattr', ['TEST1','prop1'], {}, None),
    ('getattr', [], {'object_id':'WRONG_ID','name':'abc'}, KeyError),
    ('getattr', [], {'object_id':'TEST1','name':'abc'}, AttributeError),
    ('getattr', [], {'object_id':'TEST1','name':'prop1'}, 10),
    ('getattr', [], {'object_id':'TEST1','name':['prop1','prop2']}, {'prop1': 10, 'prop2': 'abc'}),
    ('setattr', [], {'object_id':'TEST1','name':'prop1'}, ValueError),
    ('setattr', [], {'object_id':'TEST1','name':'prop1','value':1000}, 1000),
    ('delattr', [], {'object_id':'TEST1','name':'prop1'}, None)
])
def test_controller_execute_property(method_name, args, kwargs, outcome, mock_controllers):
    worker, user = mock_controllers
    worker.start()
    test_obj = MyClass(10)
    worker.register(test_obj, 'TEST1')
    
    command = dict(
        method = method_name,
        args = args,
        kwargs = kwargs
    )
    request_id = user.transmitRequest(command, target=[str(id(worker))])
    response: dict = user.retrieveData(request_id, data_only=False)
    data = response.get('data')
    if response.get('status', '') != 'completed':
        error_type_name, message = data.split('!!', maxsplit=1)
        error_type = getattr(builtins, error_type_name, Exception)
        exception = error_type(message)
        assert isinstance(exception, outcome)
    elif method_name == 'getattr':
        assert data == outcome
    elif method_name == 'setattr':
        assert test_obj.prop1 == outcome
    elif method_name == 'delattr':
        assert not hasattr(test_obj, 'prop1')
    worker.stop()

def test_client_server():
    worker = Controller('model', JSONInterpreter())
    worker.start()
    worker_terminate = threading.Event()
    worker_thread = threading.Thread(target=start_server, args=[HOST,PORT,worker], kwargs={'terminate':worker_terminate}, daemon=True)
    worker_thread.start()
    time.sleep(1)

    user = Controller('view', JSONInterpreter())
    user_terminate = threading.Event()
    user_thread = threading.Thread(target=start_client, args=[HOST,PORT,user], kwargs={'terminate':user_terminate}, daemon=True)
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

def test_hub_spoke():
    hub = Controller('relay', JSONInterpreter())
    hub_terminate = threading.Event()
    hub_thread = threading.Thread(target=start_server, args=[HOST,PORT,hub], kwargs={'terminate':hub_terminate}, daemon=True)
    hub_thread.start()
    time.sleep(1)
    
    worker = Controller('model', JSONInterpreter())
    worker.start()
    worker_terminate = threading.Event()
    worker_thread = threading.Thread(target=start_client, args=[HOST,PORT,worker,True], kwargs={'terminate':worker_terminate}, daemon=True)
    worker_thread.start()

    user = Controller('view', JSONInterpreter())
    user_terminate = threading.Event()
    user_thread = threading.Thread(target=start_client, args=[HOST,PORT,user,True], kwargs={'terminate':user_terminate}, daemon=True)
    user_thread.start()
    time.sleep(5)
    assert hub_thread.is_alive()
    assert worker_thread.is_alive()
    assert user_thread.is_alive()
    
    q = TwoTierQueue()
    time.sleep(5)
    worker.register(q, 'TEST1')
    time.sleep(5)
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
    user_thread.join()
    worker_thread.join()
    hub_thread.join()
    assert not user_thread.is_alive()
    assert not worker_thread.is_alive()
    assert not hub_thread.is_alive()

if __name__ == "__main__":
    pytest.main()