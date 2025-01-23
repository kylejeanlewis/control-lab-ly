# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
from collections import deque
from datetime import datetime
import functools
import logging
import sys
import threading
import time
from typing import NamedTuple, Any, Iterable, Callable

# Third party imports
import matplotlib.pyplot as plt
import pandas as pd

# Local application imports
from .device import StreamingDevice

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

def get_dataframe(data_store:Iterable[tuple[NamedTuple,datetime]], fields:Iterable[str]) -> pd.DataFrame:
    try:
        data,timestamps = list([x for x in zip(*data_store)])
    except ValueError:
        columns = ['timestamp']
        columns.extend(fields)
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(data, index=timestamps).reset_index(names='timestamp')

def record( 
    on: bool, 
    show: bool = False, 
    clear_cache: bool = False, 
    *, 
    query: Any|None = None,
    data_store: deque, 
    device: StreamingDevice, 
    event: threading.Event|None = None
):
    if clear_cache:
        data_store.clear()
    if isinstance(event, threading.Event):
        _ = event.set() if on else event.clear()
    
    device.stopStream()
    time.sleep(0.1)
    if on:
        device.startStream(data=device.processInput(query), buffer=data_store)
        device.showStream(show)
    return

def stream( 
    on: bool, 
    show: bool = False, 
    *, 
    query: Any|None = None,
    data_store: deque, 
    device: StreamingDevice, 
    event: threading.Event|None = None
):
    if on:
        device.startStream(data=device.processInput(query), buffer=data_store)
        device.showStream(show)
    else:
        device.stopStream()
        event.clear()
    return

def monitor_plot(
    data_store: Iterable[tuple[NamedTuple,datetime]], 
    y: str, 
    x: str = 'timestamp', 
    kind: str = 'line',
    stop_trigger: threading.Event|None = None,
    dataframe_maker: Callable|None = None
):
    assert hasattr(sys,'ps1'), "This function is intended for use in Python interactive sessions"
    assert kind in ('line','scatter'), "kind must be either 'line' or 'scatter'"
    from IPython.display import display, clear_output
    stop_trigger = stop_trigger if isinstance(stop_trigger, threading.Event) else threading.Event()
    dataframe_maker = dataframe_maker if callable(dataframe_maker) else functools.partial(get_dataframe, fields=(x,y))
    def inner():
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        timestamp = None
        count = 0
        initial_state = stop_trigger.is_set()
        while (stop_trigger.is_set() == initial_state) and count<10:
            time.sleep(0.1)
            if not len(data_store):
                continue
            if data_store[-1][1] == timestamp:
                count += 1
                continue
            count = 0
            timestamp = data_store[-1][1]
            df = dataframe_maker(data_store=data_store)
            ax.cla()
            if kind == 'line':
                ax.plot(df[x], df[y], label=y.title())
            else:
                ax.scatter(df[x], df[y], label=y.title())
            ax.legend(loc='upper left')
            plt.tight_layout()
            display(fig)
            clear_output(wait=True)
        display(fig)
        return
    thread = threading.Thread(target=inner)
    thread.start()
    return stop_trigger