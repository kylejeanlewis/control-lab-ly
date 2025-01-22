# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
from collections import deque
from datetime import datetime
import logging
import threading
import time
from typing import NamedTuple, Any, Iterable

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

def monitor_plot(data_store: Iterable[tuple[NamedTuple,datetime]], y: str, x: str = 'timestamp', stop_trigger: threading.Event|None = None):
    assert hasattr(__builtins__,'__IPYTHON__'), "This function is intended for use in Jupyter notebooks / IPython sessions"
    from IPython.display import display, clear_output
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    timestamp = None
    stop_trigger = stop_trigger if isinstance(stop_trigger, threading.Event) else threading.Event()
    count = 0
    while not stop_trigger.is_set() and count<10:
        time.sleep(0.1)
        if not len(data_store):
            continue
        if data_store[-1][1] != timestamp:
            count = 0
            timestamp = data_store[-1][1]
            df = get_dataframe(data_store=data_store, fields=(x,y))
            ax.cla()
            ax.plot(df[x], df[y], label=y.title())
            ax.legend(loc='upper left')
            plt.tight_layout()
            display(fig)
            clear_output(wait=True)
        else:
            count += 1
    # display(fig)
    return stop_trigger