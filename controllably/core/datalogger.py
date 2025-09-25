# -*- coding: utf-8 -*-
"""
This module provides functions to record and stream data from a streaming device.

## Functions:
    `get_dataframe`: Convert a list of tuples to a pandas DataFrame
    `record`: Record data from a streaming device
    `stream`: Stream data from a streaming device
    `monitor_plot`: Monitor a data stream in real-time

<i>Documentation last updated: 2025-06-11</i>
"""
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

# Configure logging
logger = logging.getLogger(__name__)

def get_dataframe(data_store:Iterable[tuple[NamedTuple,datetime]], fields:Iterable[str]) -> pd.DataFrame:
    """ 
    Convert a list of tuples to a pandas DataFrame.
    The first element of each tuple is a NamedTuple, the second element is a datetime object.
    
    Args:
        data_store (Iterable[tuple[NamedTuple,datetime]]): list of tuples
        fields (Iterable[str]): list of field names
        
    Returns:
        pd.DataFrame: DataFrame object
    """
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
    device: StreamingDevice, 
    data_store: deque|None = None, 
    split_stream: bool = True,
    callback: Callable[[str],Any]|None = None,
    query: Any|None = None,
    event: threading.Event|None = None
 ) -> deque:
    """ 
    Record data from a streaming device.
    
    Args:
        on (bool): start or stop recording
        show (bool, optional): display the data as it is recorded. Defaults to False.
        clear_cache (bool, optional): clear the data cache before starting. Defaults to False.
        device (StreamingDevice): streaming device object
        data_store (deque|None): data cache. If None, the device buffer will be used. Defaults to None.
        split_stream (bool, optional): whether to split the stream and data processing threads. Defaults to True.
        query (Any|None, optional): query to pass to the streaming device. Defaults to None.
        event (threading.Event | None, optional): event to set or clear. Defaults to None.
    
    Returns:
        deque: data cache if provided, else device buffer
    """
    if clear_cache:
        _ = device.buffer.clear() if data_store is None else data_store.clear()
    if isinstance(event, threading.Event):
        _ = event.set() if on else event.clear()
    
    device.stopStream()
    time.sleep(0.1)
    if on:
        device.startStream(data=device.processInput(query), buffer=data_store, split_stream=split_stream, callback=callback)
        device.showStream(show)
    return device.buffer if data_store is None else data_store

def stream( 
    on: bool, 
    show: bool = False, 
    *, 
    device: StreamingDevice, 
    data_store: deque|None = None, 
    split_stream: bool = True,
    callback: Callable[[str],Any]|None = None,
    query: Any|None = None,
    event: threading.Event|None = None
) -> deque:
    """
    Stream data from a streaming device.
    
    Args:
        on (bool): start or stop streaming
        show (bool, optional): display the data as it is streamed. Defaults to False.
        device (StreamingDevice): streaming device object
        data_store (deque|None): data cache. If None, the device buffer will be used. Defaults to None.
        split_stream (bool, optional): whether to split the stream and data processing threads. Defaults to True.
        query (Any|None, optional): query to pass to the streaming device. Defaults to None.
        event (threading.Event | None, optional): event to set or clear. Defaults to None.
    
    Returns:
        deque: data cache if provided, else device buffer
    """
    if isinstance(event, threading.Event):
        _ = event.set() if on else event.clear()
    if on:
        device.startStream(data=device.processInput(query), buffer=data_store, split_stream=split_stream, callback=callback)
        device.showStream(show)
    else:
        device.stopStream()
    return device.buffer if data_store is None else data_store

def monitor_plot(
    data_store: Iterable[tuple[NamedTuple,datetime]]|pd.DataFrame, 
    y: str, 
    x: str = 'timestamp', 
    *,
    kind: str = 'line',
    lapsed_counts: int = 100,
    stop_trigger: threading.Event|None = None,
    dataframe_maker: Callable|None = None
) -> threading.Event:
    """
    Monitor a data stream in real-time.
    
    Args:
        data_store (Iterable[tuple[NamedTuple,datetime]]|pd.DataFrame): list of tuples or dataframe containing the data to plot
        y (str): y-axis field name
        x (str, optional): x-axis field name. Defaults to 'timestamp'.
        kind (str, optional): plot type. Defaults to 'line'.
        lapsed_counts (int, optional): number of counts to wait before stopping. Defaults to 100.
        stop_trigger (threading.Event | None, optional): event to stop the monitoring. Defaults to None.
        dataframe_maker (Callable | None, optional): function to convert data_store to a DataFrame. Defaults to None.
        
    Returns:
        threading.Event: event to stop the monitoring
    """
    if not hasattr(sys,'ps1'):
        logger.warning("`monitor_plot` is intended for use in Python interactive sessions only.")
        return
    assert kind in ('line','scatter'), "kind must be either 'line' or 'scatter'"
    from IPython.display import display, clear_output
    stop_trigger = stop_trigger if isinstance(stop_trigger, threading.Event) else threading.Event()
    # def dataframe_maker(_data_store):
    #     return _data_store if isinstance(_data_store, pd.DataFrame) else None
    dataframe_maker = dataframe_maker if callable(dataframe_maker) else functools.partial(get_dataframe, fields=(x,y))
    def inner():
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        timestamp = None
        count = 0
        initial_state = stop_trigger.is_set()
        while (stop_trigger.is_set() == initial_state) and count<lapsed_counts:
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
