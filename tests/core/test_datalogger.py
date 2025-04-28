import pytest
from collections import deque
from datetime import datetime
import logging
import sys
import threading
import time
from typing import NamedTuple
from unittest.mock import MagicMock

import pandas as pd

from ..context import controllably
from controllably.core.datalogger import get_dataframe, record, stream, monitor_plot
from controllably.core.device import StreamingDevice, BaseDevice

Data = NamedTuple('Data', [('field1', int), ('field2', float)])
data_store = [(Data(1, 2.0), datetime(2025, 3, 21, 10, 0, 0)), (Data(3, 4.0), datetime(2025, 3, 21, 10, 1, 0))]
fields = ['field1', 'field2']

def test_get_dataframe():
    df = get_dataframe(data_store, fields)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ['timestamp', 'field1', 'field2']
    assert len(df) == 2
    assert df['field1'][0] == 1
    assert df['field2'][0] == 2.0
    assert df['timestamp'][0] == datetime(2025, 3, 21, 10, 0, 0)
    assert df['field1'][1] == 3
    assert df['field2'][1] == 4.0
    assert df['timestamp'][1] == datetime(2025, 3, 21, 10, 1, 0)

def test_get_dataframe_with_error():
    data_store_error = data_store.copy()
    data_store_error.append((Data(1, '2.0'), datetime(2025, 3, 21, 10, 0, 0)))
    df = get_dataframe([], fields)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ['timestamp', 'field1', 'field2']
    assert len(df) == 0

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
        def is_open(self):
            return self._open
        def read(self):
            time.sleep(0.01)
            return b'test_output\n'
    device.connection = MockConnection()
    return device

def test_record():
    device = MagicMock(spec=StreamingDevice)
    data_store = deque()
    event = threading.Event()
    
    record(True, device=device, data_store=data_store, event=event)
    device.startStream.assert_called_once()
    device.stopStream.assert_called_once()
    assert event.is_set()
    
    time.sleep(0.5)
    device.stopStream.reset_mock()
    record(False, device=device, data_store=data_store, event=event)
    device.stopStream.assert_called_once()
    assert not event.is_set()
    
def test_record_with_clear_cache(base_device):
    base_device.connect()
    data_store = deque()
    for i in range(100):
        data_store.append((i, datetime(2025, 3, 21, 10, i%60, 0)))
    data_count = len(data_store)
    assert data_count == 100
    
    record(True, clear_cache=True, device=base_device, data_store=data_store)
    second_data_count = len(data_store)
    assert second_data_count < data_count
    time.sleep(3)
    record(False, device=base_device, data_store=data_store)
    assert len(data_store) > data_count

def test_stream():
    device = MagicMock(spec=StreamingDevice)
    data_store = deque()
    event = threading.Event()
    
    stream(True, device=device, data_store=data_store, event=event)
    device.startStream.assert_called_once()
    assert event.is_set()
    
    stream(False, device=device, data_store=data_store, event=event)
    device.stopStream.assert_called_once()
    assert not event.is_set()

@pytest.mark.skip(reason="Requires IPython environment")
def test_monitor_plot(monkeypatch, caplog):
    Data = NamedTuple('Data', [('field1', int), ('field2', float)])
    data_store = [(Data(1, 2.0), datetime(2025, 3, 21, 10, 0, 0)), (Data(3, 4.0), datetime(2025, 3, 21, 10, 1, 0))]
    stop_trigger = threading.Event()
    
    with caplog.at_level(logging.WARNING):
        monitor_plot(data_store, 'field1', stop_trigger=None)
    assert "intended for use in Python interactive sessions only" in caplog.text
    
    import matplotlib
    matplotlib.use('agg')
    sys.ps1 = "::: "
    monkeypatch.setattr("IPython.display.display", MagicMock())
    monkeypatch.setattr("IPython.display.clear_output", MagicMock())
    monkeypatch.setattr("matplotlib.pyplot.figure", MagicMock())
    stop_trigger = monitor_plot(data_store, 'field1', stop_trigger=stop_trigger)
    assert isinstance(stop_trigger, threading.Event)
    stop_trigger.set()
    stop_trigger = monitor_plot(data_store, 'field1', stop_trigger=stop_trigger,kind='scatter')
    assert isinstance(stop_trigger, threading.Event)
    stop_trigger.set()
    
    empty_data_store = []
    stop_trigger = monitor_plot(empty_data_store, 'field1', stop_trigger=stop_trigger,kind='scatter')
    assert isinstance(stop_trigger, threading.Event)
    time.sleep(0.5)
    empty_data_store.extend(data_store)
    stop_trigger.set()
