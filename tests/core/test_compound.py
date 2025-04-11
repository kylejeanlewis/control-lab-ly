import pytest
import time
from unittest.mock import MagicMock

import serial
from controllably.core.compound import Compound, Ensemble, Combined, Multichannel
from controllably.core.device import BaseDevice, SerialDevice

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
       
class MockPart1:
    def __init__(self, port, *args, device=None, **kwargs):
        self.device = device if device is not None else MagicMock()
        self.is_busy = False
        self.is_connected = False
        self.verbose = False
        self.connection_details = {'port':port}
    
    def method5__(self):
        """
        method 5
        
        Returns:
            None
        """
    
    def connect(self):
        self.is_connected = True
        time.sleep(3)
    
    def disconnect(self):
        self.is_connected = False
    
    def resetFlags(self):
        self.is_busy = False
        self.is_connected = False
        self.verbose = False
    
    def shutdown(self):
        self.is_connected = False
        
    def method1(self, order, name, port, **kwargs):
        """
        method 1

        Args:
            order (int): order
            name (int): name
            port (str): port

        Returns:
            str: output
        """
        out = f"{order=}, {name=}, {port=}"
        print(out)
        time.sleep(3)
        return out 
    
    def method3(self):
        """
        method 3
        
        Returns:
            None
        """
        print('method3')
        return 

class MockPart2:
    def __init__(self, port, *args, device=None, **kwargs):
        base_device = SerialDevice(**kwargs)
        self.device = device if device is not None else base_device
        self.is_busy = False
        self.is_connected = False
        self.verbose = False
        self.connection_details = {'port':port}
        self.attribute = kwargs.get('attribute', None)
        
    def method6__(self):
        """
        method 6
        
        Returns:
            None
        """
    
    def connect(self):
        self.is_connected = True
        time.sleep(0.5)
    
    def disconnect(self):
        self.is_connected = False
    
    def resetFlags(self):
        self.is_busy = False
        self.is_connected = False
        self.verbose = False
    
    def shutdown(self):
        self.is_connected = False
    
    def method2(self, order, name, port, **kwargs):
        """
        method 2

        Args:
            order (int): order
            name (int): name
            port (str): port

        Returns:
            str: output
        """
        out = f"{order=}, {name=}, {port=}"
        print(out)
        time.sleep(3)
        return out 
    
    def method4(self):
        """
        method 4
        
        Returns:
            None
        """
        print('method4')
        return 

@pytest.fixture
def mock_ensemble():
    MockEnsemble = Ensemble.factory(MockPart1)
    return MockEnsemble

@pytest.fixture
def mock_multichannel():
    MockMultichannel = Multichannel.factory(MockPart2)
    return MockMultichannel

def test_compound():
    parts = {'part1': MockPart1('COM1'), 'part2': MockPart2('COM2')}
    compound = Compound(parts=parts)
    assert isinstance(compound.parts.part1, MockPart1)
    assert isinstance(compound.parts.part2, MockPart2)
    
    assert not compound.parts.part1.is_connected
    assert not compound.parts.part2.is_connected
    assert not compound.is_connected
    start_time = time.perf_counter()
    compound.connect()
    duration = time.perf_counter() - start_time
    assert abs(duration - (3+0.5)) < (3+0.5)*0.1
    assert compound.connection_details == {'part1':{'port':'COM1'},'part2':{'port':'COM2'}}
    assert compound.parts.part1.is_connected
    assert compound.parts.part2.is_connected
    assert compound.is_connected
    
    assert not compound.verbose
    compound.disconnect()
    assert not compound.is_connected
    compound.resetFlags()
    assert not compound.is_busy
    compound.shutdown()
    assert not compound.is_connected
    
    assert len(repr(compound).split('\n')) == 3
    assert len(str(compound).split('\n')) == 3

def test_ensemble(mock_ensemble):
    ensemble = mock_ensemble(channels=[0,1,2,3],details=[dict(port=f'COM{i}') for i in range(4)])
    assert issubclass(ensemble.__class__, Ensemble)
    assert isinstance(ensemble, mock_ensemble)
    assert all([isinstance(ensemble.channels[i], MockPart1) for i in ensemble.channels.keys()])
    
    assert not ensemble.is_connected
    start_time = time.perf_counter()
    ensemble.connect()
    duration = time.perf_counter() - start_time
    assert duration < 4*3
    assert abs(duration - 3*4) > (3*4)*0.1
    assert ensemble.is_connected
    ensemble.disconnect()
    assert not ensemble.is_connected
    ensemble.resetFlags()
    assert not ensemble.is_busy
    ensemble.shutdown()
    assert not ensemble.is_connected
    
    def kwargs_func(i, key, part):
        return dict(order=i, name=key, port=part.connection_details['port'])
    start_time = time.perf_counter()
    outs = ensemble.parallel('method1', kwargs_func, channels=[0,1,2,3])
    duration = time.perf_counter() - start_time
    assert duration < 4*3
    assert abs(duration - 3*4) > (3*4)*0.1
    expected_out = {
        0:"order=0, name=0, port='COM0'",
        1:"order=1, name=1, port='COM1'",
        2:"order=2, name=2, port='COM2'",
        3:"order=3, name=3, port='COM3'"
    }
    assert outs == expected_out
    
    assert ensemble.method5__.__code__ == ensemble.parts.chn_1.method5__.__code__
    assert ensemble.method3() is None

def test_ensemble_with_repeated_args(mock_ensemble):
    ensemble = mock_ensemble(channels=[0,1,2,3],details=[dict(port=f'COM0')])
    assert issubclass(ensemble.__class__, Ensemble)
    assert isinstance(ensemble, mock_ensemble)
    assert all([isinstance(ensemble.channels[i], MockPart1) for i in ensemble.channels.keys()])
    assert all([part.connection_details['port'] == 'COM0' for part in ensemble.channels.values()])
    
    ensemble = mock_ensemble(channels=[0,1,2,3],details=dict(port=f'COM0'))
    assert issubclass(ensemble.__class__, Ensemble)
    assert isinstance(ensemble, mock_ensemble)
    assert all([isinstance(ensemble.channels[i], MockPart1) for i in ensemble.channels.keys()])
    assert all([part.connection_details['port'] == 'COM0' for part in ensemble.channels.values()])

def test_ensemble_parallel_execution_with_unexpected_input(mock_ensemble):
    ensemble = mock_ensemble(channels=[0,1,2,3],details=[dict(port=f'COM{i}') for i in range(4)])
    assert issubclass(ensemble.__class__, Ensemble)
    assert isinstance(ensemble, mock_ensemble)
    assert all([isinstance(ensemble.channels[i], MockPart1) for i in ensemble.channels.keys()])
    
    def kwargs_func(i, key, part):
        return dict(order=i, name=key, port=part.connection_details['port'])
    
    outs = ensemble.parallel('method1', kwargs_func, channels=[0,1,2,5])
    assert len(outs) == 3
    
    with pytest.raises(AttributeError):
        outs = ensemble.parallel('method2', kwargs_func, channels=[0,1,2])
        
def test_ensemble_single_channel(mock_ensemble):
    ensemble = mock_ensemble(channels=[0,1,2,3],details=[dict(port=f'COM{i}') for i in range(4)])
    assert issubclass(ensemble.__class__, Ensemble)
    assert isinstance(ensemble, mock_ensemble)
    assert all([isinstance(ensemble.channels[i], MockPart1) for i in ensemble.channels.keys()])
    out = ensemble.method1(order=123, name=456, port='COM789', channel=0)
    assert out == {0:"order=123, name=456, port='COM789'"}
    
def test_ensemble_get_channel(mock_ensemble):
    ensemble = mock_ensemble(channels=[0,1,2,3],details=[dict(port=f'COM{i}') for i in range(4)])
    assert issubclass(ensemble.__class__, Ensemble)
    assert isinstance(ensemble, mock_ensemble)
    assert all([isinstance(ensemble.channels[i], MockPart1) for i in ensemble.channels.keys()])
    
    channels = ensemble._get_channel()
    assert len(channels) == 4
    assert isinstance(channels[0], MockPart1)
    
    channels = ensemble._get_channel(0)
    assert len(channels) == 1
    assert isinstance(channels[0], MockPart1)
    assert channels[0].connection_details['port'] == 'COM0'
    with pytest.raises(KeyError):
        channels = ensemble._get_channel(5)
    
    channels = ensemble._get_channel([1,2])
    assert len(channels) == 2
    assert isinstance(channels[1], MockPart1)
    assert channels[1].connection_details['port'] == 'COM1'
    assert channels[2].connection_details['port'] == 'COM2'
    with pytest.raises(KeyError):
        channels = ensemble._get_channel([1,5])
    with pytest.raises(ValueError):
        channels = ensemble._get_channel(0.1)
    
def test_combined(monkeypatch):
    monkeypatch.setattr(serial, 'Serial', MockSerial)
    parts = {'part1': MockPart1(port='COM0'), 'part2': MockPart2(port='COM0')}
    combined = Combined(parts=parts, port='COM0', baudrate=9600)
    monkeypatch.setattr(combined.parts.part1, 'device', combined.device)
    monkeypatch.setattr(combined.parts.part2, 'device', combined.device)
    assert isinstance(combined.parts.part1, MockPart1)
    assert isinstance(combined.parts.part2, MockPart2)
    assert isinstance(combined.device, SerialDevice)
    assert isinstance(combined.parts.part2.device, SerialDevice)
    assert combined.device == combined.parts.part1.device
    assert combined.device == combined.parts.part2.device
    
    assert not combined.parts.part1.is_connected
    assert not combined.parts.part2.is_connected
    assert not combined.is_connected
    combined.connect()
    assert combined.connection_details == {'port':'COM0', 'baudrate':9600, 'timeout':1}
    assert combined.is_connected
    
    assert not combined.verbose
    combined.disconnect()
    assert not combined.is_connected
    combined.resetFlags()
    assert not combined.is_busy
    combined.shutdown()
    assert not combined.is_connected
    
    assert len(repr(combined).split('\n')) == 3
    assert len(str(combined).split('\n')) == 3

def test_multichannel(mock_multichannel, monkeypatch):
    monkeypatch.setattr(serial, 'Serial', MockSerial)
    multichannel = mock_multichannel(channels=[0,1,2,3],details=[dict(port=f'COM0')], port='COM0', baudrate=9600)
    assert issubclass(multichannel.__class__, Multichannel)
    assert isinstance(multichannel, mock_multichannel)
    assert all([isinstance(multichannel.channels[i], MockPart2) for i in multichannel.channels.keys()])
    assert isinstance(multichannel.device, SerialDevice)
    assert isinstance(multichannel.parts.chn_1.device, SerialDevice)
    
    assert not multichannel.is_connected
    multichannel.connect()
    assert multichannel.is_connected
    
    assert multichannel.active_channel == 0
    multichannel.setActiveChannel(3)
    assert multichannel.active_channel == 3
    with pytest.raises(KeyError):
        multichannel.setActiveChannel(5)
    
    multichannel.disconnect()
    assert not multichannel.is_connected
    multichannel.resetFlags()
    assert not multichannel.is_busy
    multichannel.shutdown()
    assert not multichannel.is_connected
    
    outs = multichannel.method2(order=123, name=456, port='COM789')
    expected_out = {
        0:"order=123, name=456, port='COM789'",
        1:"order=123, name=456, port='COM789'",
        2:"order=123, name=456, port='COM789'",
        3:"order=123, name=456, port='COM789'"
    }
    assert outs == expected_out
    
    assert multichannel.method6__.__code__ == multichannel.parts.chn_1.method6__.__code__
    assert multichannel.method4() is None
    
    multichannel = mock_multichannel(channels=[0,1,2,3],details=dict(port=f'COM0'), port='COM0', baudrate=9600)
    assert issubclass(multichannel.__class__, Multichannel)
    assert isinstance(multichannel, mock_multichannel)

def test_multichannel_single_channel(mock_multichannel, monkeypatch):
    monkeypatch.setattr(serial, 'Serial', MockSerial)
    multichannel = mock_multichannel(channels=[0,1,2,3],details=[dict(port=f'COM0')], port='COM0', baudrate=9600)
    assert issubclass(multichannel.__class__, Multichannel)
    assert isinstance(multichannel, mock_multichannel)
    assert all([isinstance(multichannel.channels[i], MockPart2) for i in multichannel.channels.keys()])
    out = multichannel.method2(order=123, name=456, port='COM789', channel=0)
    assert out == {0:"order=123, name=456, port='COM789'"}
  
def test_multichannel_get_channel(mock_multichannel, monkeypatch):
    monkeypatch.setattr(serial, 'Serial', MockSerial)
    multichannel = mock_multichannel(channels=[0,1,2,3],details=[dict(port='COM0', attribute=i) for i in range(4)], port='COM0', baudrate=9600)
    assert issubclass(multichannel.__class__, Multichannel)
    assert isinstance(multichannel, mock_multichannel)
    assert all([isinstance(multichannel.channels[i], MockPart2) for i in multichannel.channels.keys()])
    
    channels = multichannel._get_channel()
    assert len(channels) == 4
    assert isinstance(channels[0], MockPart2)
    
    channels = multichannel._get_channel(0)
    assert len(channels) == 1
    assert isinstance(channels[0], MockPart2)
    assert channels[0].attribute == 0
    with pytest.raises(KeyError):
        channels = multichannel._get_channel(5)
    
    channels = multichannel._get_channel([1,2])
    assert len(channels) == 2
    assert isinstance(channels[1], MockPart2)
    assert channels[1].attribute == 1
    assert channels[2].attribute == 2
    with pytest.raises(KeyError):
        channels = multichannel._get_channel([1,5])
    with pytest.raises(ValueError):
        channels = multichannel._get_channel(0.1)

if __name__ == "__main__":
    pytest.main()