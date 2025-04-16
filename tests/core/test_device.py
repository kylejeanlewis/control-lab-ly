import pytest
from collections import deque
from datetime import datetime
import logging
import socket
import threading
import time
from typing import NamedTuple
from unittest.mock import MagicMock, patch, mock_open

import serial

from controllably.core.device import (
    BaseDevice, SerialDevice, SocketDevice, TimedDeviceMixin, Data, READ_FORMAT, WRITE_FORMAT
)

OTHER_DATA = NamedTuple('OtherData', [('strdata', str),('intdata', int),('floatdata', float),('booldata', bool)])
OTHER_FORMAT = '{strdata},{intdata},{floatdata},{booldata}\n'

@pytest.fixture
def base_device():
    device = BaseDevice()
    class MockConnection:
        def __init__(self):
            self._open = False
            self._waiting = False
            self.count = 0
        def open(self):
            self._open = True
        def close(self):
            self._open = False
        def is_open(self):
            return self._open
        def in_waiting(self):
            return self._waiting
        def write(self, data):
            if not self._open:
                raise ConnectionError
            return len(data) if data is not None else None
        def read(self):
            if not self._open:
                raise ConnectionError
            return b'test_output\n'
        def read_all(self):
            if not self._open:
                raise ConnectionError
            self.count += 1
            if self.count > 3:
                return b''
            return b'test_output\ntest_output\ntest_output\n'
    device.connection = MockConnection()
    return device

def test_base_device_init(base_device):
    assert base_device.connection_details == {}
    assert base_device.read_format == READ_FORMAT
    assert base_device.write_format == WRITE_FORMAT
    assert base_device.data_type == Data
    assert not base_device.verbose
    base_device.verbose = True
    assert base_device.verbose

def test_base_device_connect_disconnect(base_device):
    base_device.connect()
    assert base_device.is_connected
    base_device.connect()
    assert base_device.is_connected
    
    assert not base_device.checkDeviceBuffer()
    base_device.clear()
    base_device.disconnect()
    assert not base_device.is_connected
    base_device.disconnect()
    assert not base_device.is_connected

def test_base_device_connect_disconnect_with_exceptions(base_device,monkeypatch,caplog):
    monkeypatch.setattr(base_device.connection, 'open', MagicMock(side_effect=ConnectionError))
    monkeypatch.setattr(base_device.connection, 'close', MagicMock(side_effect=ConnectionError))
    with caplog.at_level(logging.ERROR):
        base_device.connect()
        assert "Failed to connect to" in caplog.text
    base_device.connection._open = True
    with caplog.at_level(logging.ERROR):
        base_device.disconnect()
        assert "Failed to disconnect from" in caplog.text

@pytest.mark.parametrize('connect, data_input', [
    (True, 'True'),
    (False, 'True')
])
def test_base_device_write(base_device, connect, data_input):
    if connect:
        base_device.connect()
        assert base_device.is_connected
    ret = base_device.write(data_input)
    assert ret == connect

def test_base_device_read(base_device):
    assert not base_device.is_connected
    data = base_device.read()
    assert data == ''
    base_device.connect()
    assert base_device.is_connected
    data = base_device.read()
    assert data == 'test_output'

def test_base_device_read_all(base_device):
    assert not base_device.is_connected
    data = base_device.readAll()
    assert data == []
    base_device.connect()
    assert base_device.is_connected
    data = base_device.readAll()
    assert data == ['test_output']*9

def test_base_device_poll(base_device):
    assert not base_device.is_connected
    data = base_device.poll('test_data\n')
    assert data == ''
    data = base_device.poll()
    assert data == ''
    
    base_device.connect()
    assert base_device.is_connected
    data = base_device.poll('test_data\n')
    assert data == 'test_output'
    data = base_device.poll()
    assert data == 'test_output'

@pytest.mark.parametrize('data_input', [None, 'test_data'])
def test_base_device_process_input(base_device,data_input):
    data = base_device.processInput(data_input)
    if data_input is None:
        assert data is None
    else:
        assert data == 'test_data\n'

def test_base_device_process_output(base_device):
    now = datetime.now()
    data, timestamp = base_device.processOutput('test_data\n'.strip(), timestamp=now)
    assert data == Data(data='test_data')
    assert isinstance(timestamp, datetime)
    
    data, timestamp = base_device.processOutput('test_data\n'.strip())
    assert data == Data(data='test_data')
    assert timestamp is None
    
def test_base_device_process_output_with_other_data_format(base_device):
    now = datetime.now()
    data, timestamp = base_device.processOutput(
        'abc,123,4.5,false\n'.strip(), timestamp=now, 
        data_type=OTHER_DATA, format=OTHER_FORMAT
    )
    assert data == OTHER_DATA(strdata='abc',intdata=123,floatdata=4.5,booldata=False)
    assert isinstance(timestamp, datetime)
    
    data, timestamp = base_device.processOutput(
        'abc,123,4.5,false\n'.strip(), 
        data_type=OTHER_DATA, format=OTHER_FORMAT
    )
    assert data == OTHER_DATA(strdata='abc',intdata=123,floatdata=4.5,booldata=False)
    assert timestamp is None 

@pytest.mark.parametrize('data_input', [None, '123abc', 'abc,12.3,4.5,false', 'abc,123,4.5,false', 'abc,abc,4.5,false'])
def test_base_device_process_output_exceptions(base_device,data_input):
    data, timestamp = base_device.processOutput(
        data_input, data_type=OTHER_DATA, format=OTHER_FORMAT
    )
    if data_input == 'abc,123,4.5,false':
        assert data == OTHER_DATA(strdata='abc',intdata=123,floatdata=4.5,booldata=False)
        assert timestamp is None
    elif data_input == 'abc,12.3,4.5,false':
        assert data == OTHER_DATA(strdata='abc',intdata=12,floatdata=4.5,booldata=False)
        assert timestamp is None
    else:
        assert data is None
        assert timestamp is None
    
def test_base_device_query(base_device, monkeypatch):
    buffer = ['out1', 'out2', 'out3']
    buffer_iter = iter(buffer)
    count = 0
    now = datetime.now()
    collect_now = []
    def buffer_read():
        nonlocal count, now, collect_now
        count += 1
        now = datetime.now()
        collect_now.append(now)
        try:
            return next(buffer_iter)
        except StopIteration:
            return ''
    monkeypatch.setattr(base_device, 'read', buffer_read)
    monkeypatch.setattr(base_device, 'checkDeviceBuffer', lambda: bool(len(buffer)-count))
    assert not base_device.is_connected
    out = base_device.query('test_data')
    assert out == []
    out = base_device.query('test_data', timestamp=True)
    assert out == []
    
    base_device.connect()
    assert base_device.is_connected
    out = base_device.query('test_data')
    assert out == [Data(data=d) for d in buffer]
    
    buffer_iter = iter(buffer)
    collect_now = []
    out = base_device.query('test_data', timestamp=True)
    assert out == [(Data(data=d), n) for d,n in zip(buffer,collect_now)]

def test_base_device_query_other_format(base_device, monkeypatch):
    buffer = ['abc,123,4.5,false', 'abc,abc,4.5,false', 'abc,123,4.5,false']
    buffer_iter = iter(buffer)
    count = 0
    now = datetime.now()
    collect_now = []
    def buffer_read():
        nonlocal count, now, collect_now
        count += 1
        now = datetime.now()
        collect_now.append(now)
        try:
            return next(buffer_iter)
        except StopIteration:
            return ''
    monkeypatch.setattr(base_device, 'read', buffer_read)
    monkeypatch.setattr(base_device, 'checkDeviceBuffer', lambda: bool(len(buffer)-count))

    base_device.connect()
    base_device.data_type = OTHER_DATA
    base_device.read_format = OTHER_FORMAT
    assert base_device.is_connected
    out = base_device.query('test_data')
    assert out == [OTHER_DATA(strdata='abc',intdata=123,floatdata=4.5,booldata=False)]*2

def test_base_device_query_single_out(base_device):
    assert not base_device.is_connected
    out = base_device.query('test_data', multi_out=False)
    assert out is None
    now = datetime.now()
    out = base_device.query('test_data', multi_out=False, timestamp=True)
    assert out == (None, now)
    
    base_device.connect()
    assert base_device.is_connected
    data = base_device.query('test_data', multi_out=False)
    assert data == Data(data='test_output')
    now = datetime.now()
    out = base_device.query('test_data', multi_out=False, timestamp=True)
    assert out == (Data(data='test_output'), now)

def test_base_device_show_stream(base_device):
    base_device.showStream(True)
    assert base_device.show_event.is_set()
    base_device.showStream(False)
    assert not base_device.show_event.is_set()
    
def test_base_device_stream(base_device):
    base_device.stream_event.set()
    assert base_device.stream_event.is_set()
    thread = threading.Thread(target=base_device._loop_stream)
    thread.start()
    time.sleep(0.1)
    base_device.stream_event.clear()
    assert not base_device.stream_event.is_set()
    assert not base_device.data_queue.empty()

def test_base_device_stream_process(base_device):
    base_device.connect()
    assert base_device.is_connected
    base_device.stream_event.set()
    assert base_device.stream_event.is_set()
    assert base_device.data_queue.empty()
    assert len(base_device.buffer) == 0
    thread1 = threading.Thread(target=base_device._loop_stream,daemon=True)
    thread2 = threading.Thread(target=base_device._loop_process_data, daemon=True)
    thread1.start()
    time.sleep(1)
    assert not base_device.data_queue.empty()
    thread2.start()
    base_device.stream_event.clear()
    assert not base_device.stream_event.is_set()
    assert not base_device.data_queue.empty()
    thread2.join()
    assert base_device.data_queue.empty()
    assert len(base_device.buffer)
    
def test_base_device_stream_process_synced(base_device):
    base_device.connect()
    assert base_device.is_connected
    base_device.stream_event.set()
    assert base_device.stream_event.is_set()
    assert base_device.data_queue.empty()
    assert len(base_device.buffer) == 0
    sync_start = threading.Barrier(2)
    thread1 = threading.Thread(
        target=base_device._loop_stream, 
        kwargs=dict(sync_start=sync_start), daemon=True
    )
    thread2 = threading.Thread(
        target=base_device._loop_process_data, 
        kwargs=dict(sync_start=sync_start), daemon=True
    )
    thread1.start()
    time.sleep(1)
    assert base_device.data_queue.empty()
    thread2.start()
    time.sleep(1)
    base_device.stream_event.clear()
    assert not base_device.stream_event.is_set()
    thread1.join()
    thread2.join()
    assert base_device.data_queue.empty()
    assert len(base_device.buffer)

def test_base_device_start_stop_stream(base_device):
    base_device.connect()
    assert base_device.is_connected
    assert not base_device.stream_event.is_set()
    base_device.startStream()
    assert base_device.stream_event.is_set()
    time.sleep(1)
    base_device.startStream(show=True)
    assert base_device.show_event.is_set()
    base_device.stream(on=False)
    assert not base_device.stream_event.is_set()
    assert len(base_device.buffer)
    base_device.clear()
    assert len(base_device.buffer) == 0



@pytest.fixture
def timed_device():
    class TestDevice(TimedDeviceMixin, BaseDevice):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.value = '0'
            
        def setValue(self, value, event=None):
            try:
                self.value = value
                super().setValue(value, event)
            except NotImplementedError:
                return isinstance(value,str)
    return TestDevice()

def test_timed_device_mixin_set_value_delayed(timed_device):
    event = threading.Event()
    event.set()
    assert event.is_set()
    assert timed_device.value == '0'
    timed_device.setValue('1',event)
    assert not event.is_set()
    assert timed_device.value == '1'
    
    timer = timed_device.setValueDelayed(1, initial=10, final='100', event=event, blocking=False)
    assert timer is None
    
    delay = 1
    start_time = time.perf_counter()
    timer = timed_device.setValueDelayed(delay, initial='100', final='1000', event=event, blocking=True)
    assert (time.perf_counter() - start_time) - delay < 0.1*delay
    assert timed_device.value == '1000'
    assert timer is None
    
    start_time = time.perf_counter()
    timer = timed_device.setValueDelayed(delay, initial='10', final='100', event=event, blocking=False)
    assert timed_device.value == '10'
    assert isinstance(timer, threading.Timer)
    assert event.is_set()
    time.sleep(0.1)
    assert timed_device.value == '10'
    timer.join()
    assert (time.perf_counter() - start_time) - delay < 0.1*delay
    assert timed_device.value == '100'
    assert not event.is_set()
    
    start_time = time.perf_counter()
    timer = timed_device.setValueDelayed(delay, initial='10', final='100', event=event, blocking=False)
    assert timed_device.value == '10'
    assert isinstance(timer, threading.Timer)
    time.sleep(0.1)
    timed_device.stopTimer(timer, event)
    assert (time.perf_counter() - start_time) < 0.9*delay
    assert timed_device.value == '10'



@pytest.fixture
def serial_device(monkeypatch):
    class MockSerial(serial.Serial):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._open = False
            self._waiting = False
            self.count = 0
        def open(self):
            self._open = True
        def close(self):
            self._open = False
        @property
        def is_open(self):
            return self._open
        @is_open.setter
        def is_open(self, value):
            self._open = value
        @property
        def in_waiting(self):
            return self._waiting
        def write(self, data):
            if not self._open:
                raise serial.SerialException
            return len(data) if data is not None else None
        def readline(self):
            if not self._open:
                raise serial.SerialException
            return b'test_output\n'
        def read_all(self):
            if not self._open:
                raise serial.SerialException
            self.count += 1
            if self.count > 3:
                return b''
            return b'test_output\ntest_output\ntest_output\n'
    monkeypatch.setattr(serial, 'Serial', MockSerial)
    device = SerialDevice(port='COM3', baudrate=9600, timeout=1)
    device._logger.handlers.clear()
    return device

def test_serial_device_init(serial_device):
    assert serial_device.port == 'COM3'
    assert serial_device.baudrate == 9600
    assert serial_device.timeout == 1
    assert serial_device.serial.port == 'COM3'
    assert serial_device.serial.baudrate == 9600
    assert serial_device.serial.timeout == 1
    serial_device.serial = serial.Serial('COM4', 115200, timeout=2)
    assert serial_device.serial.port == 'COM4'
    assert serial_device.serial.baudrate == 115200
    assert serial_device.serial.timeout == 2

def test_serial_device_connect_disconnect(serial_device):
    serial_device.connect()
    assert serial_device.is_connected
    serial_device.connect()
    assert serial_device.is_connected
    
    assert not serial_device.checkDeviceBuffer()
    serial_device.clear()
    serial_device.disconnect()
    assert not serial_device.is_connected
    serial_device.disconnect()
    assert not serial_device.is_connected

def test_serial_device_connect_disconnect_with_exceptions(serial_device,monkeypatch,caplog):
    monkeypatch.setattr(serial_device.connection, 'open', MagicMock(side_effect=serial.SerialException))
    monkeypatch.setattr(serial_device.connection, 'close', MagicMock(side_effect=serial.SerialException))
    with caplog.at_level(logging.ERROR):
        serial_device.connect()
        assert "Failed to connect to" in caplog.text
    serial_device.connection._open = True
    with caplog.at_level(logging.ERROR):
        serial_device.disconnect()
        assert "Failed to disconnect from" in caplog.text
        
def test_serial_device_read_write(serial_device, caplog):
    assert not serial_device.is_connected
    success = serial_device.write('test_data\n')
    assert not success
    with caplog.at_level(logging.DEBUG):
        data = serial_device.read()
        assert data == ''
        assert "Failed to receive data" in caplog.text
    
    serial_device.connect()
    assert serial_device.is_connected
    success = serial_device.write('test_data\n')
    assert success
    data = serial_device.read()
    assert data == 'test_output'
    
def test_serial_device_read_all(serial_device):
    assert not serial_device.is_connected
    data = serial_device.readAll()
    assert data == []
    serial_device.connect()
    assert serial_device.is_connected
    data = serial_device.readAll()
    assert data == ['test_output']*9
    
@pytest.fixture
def socket_device(monkeypatch):
    class MockSocket(socket.socket):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._open = True
            self._waiting = False
            self.count = 0
        def close(self):
            self._open = False
        def connect(self, address):
            return None
        def sendall(self, data):
            if not self._open:
                raise OSError
            return len(data) if data is not None else None
        def recv(self, bytesize = 1024):
            if not self._open:
                raise OSError
            self.count += 1
            if self.count > 3:
                return b''
            return b'test_output\ntest_output\ntest_output\n'
        def fileno(self):
            return 1 if self._open else -1
    monkeypatch.setattr(socket, 'socket', MockSocket)
    device = SocketDevice(host='127.0.0.1', port=12345, timeout=1)
    device._logger.handlers.clear()
    return device

def test_socket_device_init(socket_device):
    assert socket_device.host == '127.0.0.1'
    assert socket_device.port == 12345
    assert socket_device.timeout == 1

def test_socket_device_connect_disconnect(socket_device):
    socket_device.connect()
    assert socket_device.is_connected
    socket_device.connect()
    assert socket_device.is_connected
    
    socket_device.disconnect()
    assert not socket_device.is_connected
    socket_device.disconnect()
    assert not socket_device.is_connected

def test_socket_device_connect_with_exceptions(socket_device,monkeypatch,caplog):
    assert not socket_device.is_connected
    monkeypatch.setattr(socket, 'create_connection', MagicMock(side_effect=OSError))
    with caplog.at_level(logging.ERROR):
        socket_device.connect()
        assert "Failed to connect to" in caplog.text
        
def test_socket_device_disconnect_with_exceptions(socket_device,monkeypatch,caplog):
    socket_device.connect()
    assert socket_device.is_connected
    
    monkeypatch.setattr(socket_device.connection, 'close', MagicMock(side_effect=OSError))
    with caplog.at_level(logging.ERROR):
        socket_device.disconnect()
        assert "Failed to disconnect from" in caplog.text
        
def test_socket_device_read_write(socket_device, caplog):
    socket_device.connection._open = False
    assert not socket_device.is_connected
    success = socket_device.write('test_data\n')
    assert not success
    with caplog.at_level(logging.DEBUG):
        data = socket_device.read()
        assert data == ''
        assert "Failed to receive data" in caplog.text
    
    socket_device.connect()
    socket_device.connection.count = 0
    assert socket_device.is_connected
    success = socket_device.write('test_data\n')
    assert success
    data = socket_device.read()
    assert data == 'test_output'
    
def test_socket_device_read_all(socket_device):
    socket_device.connection._open = False
    assert not socket_device.is_connected
    data = socket_device.readAll()
    assert data == []
    socket_device.connect()
    socket_device.connection.count = 0
    assert socket_device.is_connected
    data = socket_device.readAll()
    assert data == ['test_output']*9

if __name__ == "__main__":
    pytest.main()