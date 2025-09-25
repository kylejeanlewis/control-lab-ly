# %% [markdown]
# # Tutorial: Using the Datalogger Module
# 
# This tutorial will guide you through the main functions of the `datalogger.py` 
# module in the `controllably.core` package. You'll learn how to use `get_dataframe`, 
# `record`, `stream`, and `monitor_plot` to log, process, and visualize data from 
# streaming devices.

# %%
from collections import deque
from datetime import datetime
import threading

from controllably.core.datalogger import get_dataframe, record, stream, monitor_plot

from tutorial_plugins import OTHER_FORMAT, OtherData

# %% [markdown]
# Using the named tuple `OtherData` for our data to create a sample data store.

# %%
print(OTHER_FORMAT)
FIELD_NAMES = OtherData._fields
print(FIELD_NAMES)

# %%
# Example data store: a list of (Data, timestamp) tuples
sample_data = [
    (OtherData('abc', 1, 2.0, True), datetime(2025, 3, 21, 10, 0, 0)),
    (OtherData('def', 3, 4.0, False), datetime(2025, 3, 21, 10, 1, 0))
]
sample_data

# %% [markdown]
# Converting `Data` to a `DataFrame` with columns: `timestamp`, `int_field`, `float_field` and `string_field`.

# %%
df = get_dataframe(sample_data, FIELD_NAMES)
df

# %% [markdown]
# Next, we will demonstrate how to use the `stream` and `record` functions to log data from the mock device.
# 
# We first create a mock connection that simulates a streaming device.

# %%
import time
from controllably.core.device import BaseDevice
from tutorial_plugins import MockConnection

device = BaseDevice(data_type=OtherData, read_format=OTHER_FORMAT)
device.connection = MockConnection()
device.connect()
device.buffer.clear()

# %% [markdown]
# Use `stream` to start and stop data streaming onto the device buffer.

# %%
stream(True, device=device)
time.sleep(3)
buffer = stream(False, device=device)
get_dataframe(buffer, FIELD_NAMES)

# %% [markdown]
# A external iterable can be used as a data store.

# %%
store = deque()

stream(True, device=device, data_store=store)
time.sleep(3)
stream(False, device=device)
get_dataframe(store, FIELD_NAMES)

# %% [markdown]
# An event to signal recording status can be added.

# %%
recording = threading.Event()

record(True, device=device, data_store=store, event=recording)
print(f"{recording.is_set()=}")
time.sleep(3)
record(False, device=device, event=recording)
print(f"{recording.is_set()=}")
get_dataframe(store, FIELD_NAMES)

# %% [markdown]
# The `record` function can also clear the data cache before starting.

# %%
record(True, clear_cache=True, device=device, data_store=store)
time.sleep(3)
record(False, device=device)
get_dataframe(store, FIELD_NAMES)

# %% [markdown]
# ## Monitoring and Plotting Data in Real-Time
# This `monitor_plot` function is intended for use in interactive Python sessions 
# (e.g., Jupyter) to visualize data as it is being recorded or streamed.
# 
# Provide the data store and the field names to plot. 
# The kind of plot can be also specified (i.e. `line` or `scatter`).

# %%
device.buffer.clear()

store = record(True, device=device)
stop_trigger = monitor_plot(store, 'intdata', kind='line')
time.sleep(3)
record(False, device=device)
stop_trigger.set()
time.sleep(1)

# %% [markdown]
# Use an external data store and an event to control recording.

# %%
store = deque(maxlen=100)
recording = threading.Event()

record(True, device=device, data_store=store, event=recording)
monitor_plot(store, 'intdata', stop_trigger=recording)
time.sleep(5)
record(False, device=device, event=recording)
time.sleep(1)

# %% [markdown]
# Multiple fields can be plotted, and the plot type can be changed.
# The `lapsed_counts` parameter sets how many new data points to wait
# before stopping the plot.

# %%
store = deque()
recording = threading.Event()

record(True, device=device, data_store=store, event=recording)
stop_monitor = monitor_plot(
    store, 'intdata', 'floatdata', 
    kind='scatter', lapsed_counts=100
)
time.sleep(3)
record(False, device=device, event=recording)
time.sleep(1)
get_dataframe(store, FIELD_NAMES)

# %% [markdown]
# Note that stopping the plot does not stop the recording, 
# and each can be separately controlled.

# %%
store = deque()
recording = threading.Event()

record(True, device=device, data_store=store, event=recording)
stop_monitor = monitor_plot(store, 'intdata')
time.sleep(3)
stop_monitor.set()
time.sleep(1)

# %%
print(store[-1])
time.sleep(3)
record(False, device=device, event=recording)
print(store[-1])

# %%