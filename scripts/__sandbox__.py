# %%
from controllably import start_logging
start_logging()

# %%
from controllably.Make.Light import LED, Multi_LED

led = LED(port='COM1', baudrate=9600, timeout=1, verbose=True, simulation=True)
mled = Multi_LED(
    channels=[1,2,3,4],
    port='COM0', baudrate=9600, timeout=1, verbose=True, simulation=True
)
mled.device.verbose = True

# %%
from controllably.Transfer.Liquid.Pump.TriContinent import TriContinent, Multi_TriContinent, Parallel_TriContinent

pump = TriContinent(port='COM1', baudrate=9600, timeout=1, verbose=True, simulation=True)
pump.device.verbose = True
pump.connect()

mpump = Multi_TriContinent(
    channels=[1,2,3,4],
    details=dict(port='COM1', baudrate=9600, timeout=1),
    port='COM1', baudrate=9600, timeout=1, verbose=True, simulation=True
)
mpump.device.verbose = True

ppump = Parallel_TriContinent(
    channels=[1,2,3,4],
    details=[
        dict(port='COM1', baudrate=9600, timeout=1, verbose=True, simulation=True),
        dict(port='COM2', baudrate=9600, timeout=1, verbose=True, simulation=True),
        dict(port='COM3', baudrate=9600, timeout=1, verbose=True, simulation=True),
        dict(port='COM4', baudrate=9600, timeout=1, verbose=True, simulation=True)
    ]
)

# %%
from controllably.Measure.Mechanical.actuated_sensor import ActuatedSensor, Parallel_ActuatedSensor
from controllably.core.datalogger import monitor_plot

fin = ActuatedSensor(
    port='COM27',
    correction_parameters=(1.0453861330027523, -717.008056157306),
    calibration_factor=573.2622826433104
)
fin.connect()
fin.home()

# %%
fin.record(True,clear_cache=True)
event = monitor_plot(fin.records,y='value', stop_trigger=fin.record_event)

# %% 
fin.touch(1,-15)
fin.record(False)

# %%
import cv2
import matplotlib.pyplot as plt

from controllably.View.camera import Camera
from controllably.View.Thermal.Flir.ax8 import AX8

# %%
cam = Camera()
cam.connect()

_,frame = cam.getFrame()
plt.imshow(frame)

# %%
cam.show()

# %%
therm = AX8('192.168.1.110')
therm.connect()

_,frame = therm.getFrame()
plt.imshow(frame)

# %%
from controllably.core.connection import get_ports
from controllably.core import datalogger
from controllably.Measure.Chemical.Sentron.sentron import SI600

probe = SI600(port='COM36', baudrate=9600, verbose=True)
probe.connect()
probe.stream(True, False)
event = datalogger.monitor_plot(
    probe.buffer, 'temperature', x='timestamp', kind='scatter',
    stop_trigger=probe.device.stream_event,
    dataframe_maker=probe.getDataframe
)
time.sleep(10)  # Let it run for 10 seconds
probe.stream(False)
event.set()

# %%
from controllably.core.connection import get_ports
from controllably.Measure.Physical.balance import Balance
from controllably.core import datalogger

bal = Balance(port='COM21', baudrate=115200, timeout=1, verbose=True, simulation=True)
bal.connect()
bal.getMass()
bal.zero()
bal.stream(True, False)
datalogger.monitor_plot(
    bal.buffer, 'force', 
    stop_trigger=bal.device.stream_event,
    dataframe_maker=bal.getDataframe
)
time.sleep(10)
bal.stream(False)
event.set()

# %%
from datetime import datetime
from random import random
import time
from unittest import mock

from controllably.Measure.Chemical.Sentron.sentron import SI600

probe = SI600(port='COM1', baudrate=9600, verbose=True)

MockSerial = mock.Mock()
MockSerial.port = 'COM1'
MockSerial.baudrate = 9600
MockSerial.timeout = 1
MockSerial.is_open = True
MockSerial.write = mock.Mock()

SET_TEMPERATURE = 25
TEMPERATURE = SET_TEMPERATURE+random()*3
SET_PH = 7
PH = SET_PH+random()*3
def readline():
    global TEMPERATURE, SET_TEMPERATURE, SET_PH, PH
    step = 0.1
    delta = step*random() 
    if abs(SET_TEMPERATURE - TEMPERATURE) <= step:
        delta -= step/2
    TEMPERATURE = TEMPERATURE + delta if SET_TEMPERATURE>TEMPERATURE else TEMPERATURE - delta
    
    if abs(SET_PH - PH) <= step:
        delta -= step/2
    PH = PH + delta if SET_PH>PH else PH - delta
    time.sleep(0.05)
    yyyymmdd, hhmmss = datetime.now().strftime("%Y-%m-%d %H:%M:%S").split(' ')
    return f"{yyyymmdd} {hhmmss} {PH:06.3f} {TEMPERATURE:04.1f}\n".encode()
MockSerial.readline = readline
probe.device.connection = MockSerial


# %%
from datetime import datetime
from random import random
import threading
import time
from typing import NamedTuple, Iterable
from unittest import mock

import matplotlib.pyplot as plt
from IPython.display import display, clear_output
import pandas as pd

from controllably.core import datalogger
from controllably.core.device import SerialDevice
from controllably.Make.Heat import Peltier

# %%
heater = Peltier(port='COM1', baudrate=9600, timeout=1, verbose=True)

MockSerial = mock.Mock()
MockSerial.port = 'COM1'
MockSerial.baudrate = 9600
MockSerial.timeout = 1
MockSerial.is_open = True
MockSerial.write = mock.Mock()

SET_TEMPERATURE = 25
TEMPERATURE = SET_TEMPERATURE+random()*3
def readline():
    global TEMPERATURE, SET_TEMPERATURE
    step = 0.1
    delta = step*random() 
    if abs(SET_TEMPERATURE - TEMPERATURE) <= step:
        delta -= step/2
    TEMPERATURE = TEMPERATURE + delta if SET_TEMPERATURE>TEMPERATURE else TEMPERATURE - delta
    power = max(0, (SET_TEMPERATURE - TEMPERATURE)*20)
    cold = 25 + step*random() - step/2
    time.sleep(0.05)
    return f"{SET_TEMPERATURE:.3f};{TEMPERATURE:.3f};{cold:.3f};{power:.3f}\n".encode()
MockSerial.readline = readline
heater.device.connection = MockSerial

# %%
heater.stream(True, True)
timer_start = threading.Timer(5, heater.record, args=(True,))
timer_start.start()

timer_stop = threading.Timer(15, heater.record, args=(False,))
timer_stop.start()

# %%
heater.clearCache()
# heater.stream(True,False)
heater.record(True, True, clear_cache=True)
this_deque = heater.records if heater.record_event.is_set() else heater.buffer
SET_TEMPERATURE = 25

# %% Blocking
heater.setTemperature(SET_TEMPERATURE, blocking=True)
heater.stream(False)

# %% Non-blocking
t,e = heater.setTemperature(SET_TEMPERATURE, blocking=False)

# %%
def monitor_plot(data_store: Iterable[tuple[NamedTuple,datetime]], fields: Iterable[str], stop_trigger: threading.Event|None = None,):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    timestamp = None
    stop_trigger = stop_trigger if isinstance(stop_trigger, threading.Event) else threading.Event()
    count = 0
    while not stop_trigger.is_set() and count<10:
        time.sleep(0.1)
        df = datalogger.get_dataframe(data_store=data_store, fields=fields)
        if df.empty:
            continue
        if df['timestamp'].iloc[-1] != timestamp:
            count = 0
            timestamp = df['timestamp'].iloc[-1]
            ax.cla()
            ax.plot(df['timestamp'], df['temperature'], label='Temperature')
            ax.legend(loc='upper left')
            plt.tight_layout()
            display(fig)
            clear_output(wait=True)
        else:
            count += 1
    display(fig)
    return stop_trigger

# %% Blocking
monitor_plot(this_deque, heater.device.data_type._fields, e)
heater.stream(False)
print(f'At Temperature: {heater.getTemperature()}°C')

# %% Non-blocking
event = threading.Event()
thread = threading.Thread(target=monitor_plot, args=(this_deque, heater.device.data_type._fields, event))
thread.start()

# %%
from collections import deque
import socket
import threading
import time
from typing import NamedTuple

import pandas as pd

from controllably.core.device import SocketDevice

# %%
device = SocketDevice(
    host=socket.gethostbyname(socket.gethostname()), port=12345, timeout=1,
    data_type=NamedTuple("Data", [("d1", str),("d2", int),("d3", float)]),
    read_format="{d1};{d2};{d3}\n", verbose=True
)

device.connect()
device.write('Hello\nWorld!\n')
device.clear()

# %%
device.query('1;2;3\n4;5;6\n7;8;9')

# %%
my_buffer = deque()
device.clear()
barrier = threading.Barrier(2, timeout=1)
device.startStream(' ', buffer=my_buffer, show=False)
time.sleep(2)
device.showStream(True)
time.sleep(2)
device.stopStream()

data,timestamps = list([x for x in zip(*my_buffer)])
df = pd.DataFrame(data, index=timestamps).reset_index(names='timestamp')
df

# %%
from controllably.Move.Cartesian import Gantry
# mover = Gantry('COM3', limits=((-100,-100,-100),(0,0,0)),safe_height=0, verbose=True)
mover = Gantry('COM4', device_type_name='Marlin', safe_height=30, limits=((0,0,0),(220,220,250)), verbose=True, simulation=True)

# %%
# mover.moveTo((-10,-20,-50))
mover.moveTo((10,20,50))

# %%
mover.safeMoveTo((-100,-10,-30))
mover.safeMoveTo((100,10,30))

# %%
mover.moveBy((50,-10,-10))

# %%
mover.move('x', -10,jog=True)
# %%
mover.home()

# %%
from controllably.Make.ThinFilm.spinner import Spinner, Multi_Spinner
details = [
    dict(port='COM17', verbose=True),
    dict(port='COM18', verbose=True),
    dict(port='COM19', verbose=True),
    dict(port='COM20', verbose=True),
]
spinners = Multi_Spinner.create(channels=[1,2,3,4], details=details, verbose=True)
spinners.connect()
spinners.spin(1000,5,blocking=True)

# %%
from controllably.core import safety

safety.set_level(safety.SUPERVISED)

@safety.guard()
def move(position:tuple[int,int,int], stop:bool = False) -> None:
    print(f"Moving{position}")
    if stop:
        print("STOP")
    return

move((1,1,1), stop=True)
move((1,1,1))

# %%
