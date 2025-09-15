# %% [markdown]
# # Device Tutorial
#
# This tutorial demonstrates how to use the `BaseDevice` class from the `controllably` package.

# %%
from datetime import datetime
import time
from typing import NamedTuple

from controllably.core.device import BaseDevice
from controllably.core.logging import start_logging

from tutorial_plugins import MockConnection

start_logging('output')

# %% [markdown]
#
# We will use a mock connection to simulate a device connection, which 
# will have basic open, close, read, and write methods.
# The `MockConnection` class is defined in the `tutorial_plugins` module.
# We open and read from the connection to see what output it returns.

# %%
conn = MockConnection()
conn.open()
conn.read()

# %% [markdown]
# After seeing the output, we can determine the appropriate read format 
# for the device, and we create the corresponding `NamedTuple` for the data structure.

# %%
READ_FORMAT = '{strdata};{intdata};{floatdata};{booldata}\n'
OtherData = NamedTuple('OtherData', [
    ('strdata', str),('intdata', int),('floatdata', float),('booldata', bool)
])

# %% [markdown]
## Base Device
# Here we create an example write format for the device.
# We then create a `BaseDevice` instance using the connection, read format, and write format.
# We also check the connection status of both the device and the connection.

# %%
WRITE_FORMAT = '{channel};{code};{data}\n'
device = BaseDevice(
    data_type=OtherData, read_format=READ_FORMAT, write_format=WRITE_FORMAT,
    verbose=True
)
device.connection = conn
print(f'{device.is_connected=}')
print(f'{conn.is_open()=}')

# %% [markdown]
# We can disconnect the device, which closes the connection.

# %%
device.disconnect()
print(f'{device.is_connected=}')
print(f'{conn.is_open()=}')

# %% [markdown]
# We can use the device as a context manager to automatically handle connection and disconnection.

# %%
print(f'{device.is_connected=}')
with device:
    print(f'{device.is_connected=}')
print(f'{device.is_connected=}')

# %% [markdown]
# We can manually connect the device again.

# %% 
device.connect()
print(f'{device.is_connected=}')
print(f'{conn.is_open()=}')

# %% [markdown]
# We can write to the device using the defined write format.
# The `write` method sends a string as-is to the device.

# %%
device.write('1;X;sample_data\n')

# %% [markdown]
# We can read from the device in the defined read format.

# %%
output = device.read()
output

# %% [markdown]
# We can read all available data from the device.

# %%
device.readAll()

# %% [markdown]
# We can poll the device, which writes a command as-is and reads data as a string.
# The `poll` method is useful for devices that require a command to be sent before they respond with data,
# and is basically a combination of `write` and `read`.

# %%
device.poll('1;X;sample_data\n')

# %% [markdown]
# We can process input data to format it according to the write format, and 
# process output data to parse it according to the read format.

# %%
formatted_input = device.processInput(data='sample_data', channel=1, code='X')
formatted_output = device.processOutput(output)

print(f'Formatted Input: {formatted_input}')
print(f'Formatted Output: {formatted_output}')

# %% [markdown]
# We can query the device, which combines processing input, writing, reading, and
# processing output. The default behavior is to return a list of outputs, but we can also
# specify `multi_out=False` to return a single output.

# %%
device.query('sample_data',channel=1,code='X')

# %%
device.query('sample_data',channel=1,code='X', multi_out=False)

# %% [markdown]
# We can change the verbosity of the device to suppress or enable detailed printing 
# out to console. The logs will still be recorded in the log files, if logging is enabled.

# %%
device.verbose = False

# %% [markdown]
# We can start a data stream from the device, which continuously polls the device and stores
# the data in a buffer. We can show or hide the stream output in real-time, 
# and stop the stream when needed.

# %%
input_data = device.processInput(data='sample_data', channel=1, code='X')
start_time = datetime.now()
device.startStream(input_data)
time.sleep(0.1)
device.showStream(True)
time.sleep(0.1)
device.showStream(False)
time.sleep(0.1)
device.stopStream()
end_time = datetime.now()

# %% [markdown]
# After stopping the stream, we can inspect the buffer to see the collected data,
# using the `BaseDevice.buffer` attribute.

# %%
print(f'Start: {start_time}, End: {end_time}')
print(f'First data: {device.buffer[0][1]} {device.buffer[0][0]}')
print(f'Last data: {device.buffer[-1][1]} {device.buffer[-1][0]}')
print(f'End: {end_time}')
print(f'{len(device.buffer)=}')
device.buffer

# %% [markdown]
# We can clear the buffer when needed.

# %%
device.clear()
print(f'{len(device.buffer)=}')

# %% [markdown]
# ## Websocket Device
# Here, we demonstrate the use of a `WebsocketDevice`, which connects to a WebSocket server.
# We use the public echo WebSocket server at `echo.websocket.org` for testing.

# %%
from controllably.core.device import WebsocketDevice

wsd = WebsocketDevice(
    'echo.websocket.org', None, timeout=2,
    write_format='{data}\n', read_format='{data}\n', verbose=True
)
# ws = WebsocketDevice(
#     '192.109.209.46', port=81, 
#     timeout=1, init_timeout=0, verbose=True, 
#     write_format='{data}', read_format='{data}'
# )

# %%
wsd.readAll()

# %%
wsd.query('@')

# %%
wsd.query('#0', False)

# %%
wsd.query('#100', False)

# %%
wsd.write('@\n')

# %% [markdown]
# ## Serial Device and Socket Device
# Finally, we can also use the `SerialDevice` class to connect to serial devices,
# and `SocketDevice` class to connect to TCP/IP or UDP devices.
# These classes have similar interfaces and functionalities as the `BaseDevice` class demonstrated above.

# %%
from controllably.core.device import SerialDevice, SocketDevice

# %%
