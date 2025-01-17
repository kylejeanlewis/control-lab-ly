# %%
import test_init
from controllably.core.device import SerialDevice
from controllably.core.connection import get_ports
from controllably.Make.Heat.peltier import Peltier

get_ports()
# ser = SerialDevice(port='COM32', baudrate=115200, timeout=1, verbose=True, simulation=False)
pelt = Peltier(port='COM32')

# %%
import test_init
from controllably.Make.Light.led import LED

led = LED(port='COM1', baudrate=9600, timeout=1, verbose=True, simulation=True)

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

import test_init
from controllably.core.device import SerialDevice, DataLoggerUtils
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
        df = DataLoggerUtils.getDataframe(data_store=data_store, fields=fields)
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

import test_init
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
from random import random
import threading
import time
from typing import NamedTuple
from unittest import mock

import pandas as pd

import test_init
from controllably.core.device import SerialDevice

def readline():
    time.sleep(0.01)
    return f"{10*random():.3f};{10*random():.3f};{10*random():.3f}\n".encode()

MockSerial = mock.Mock()
MockSerial.port = 'COM1'
MockSerial.baudrate = 9600
MockSerial.timeout = 1
MockSerial.is_open = True
MockSerial.readline = readline
MockSerial.write = mock.Mock()

# %%
device = SerialDevice(
    port='COM4', baudrate=9600, timeout=1,
    data_type=NamedTuple("Data", [("d1", str),("d2", int),("d3", float)]),
    read_format="{d1};{d2};{d3}\n",
)
device.connection = MockSerial

device.clear()
device.showStream(False)
device.startStream()
time.sleep(1)
device.showStream(True)
time.sleep(5)
device.stopStream()

data,timestamps = list([x for x in zip(*device.buffer)])
df = pd.DataFrame(data,index=timestamps)
df

# %%
import test_init
from controllably import start_logging
start_logging(r'logs\session_20241115_1451.log')
from controllably.core.factory import load_setup_from_files

setup = load_setup_from_files(r'C:\Users\chang\GitHub\control-lab-le\library\configs\open_pipette.yaml')
overkill = setup.overkill
mover = overkill.mover
liquid = overkill.liquid

# setup = load_setup_from_files(r'C:\Users\chang\GitHub\control-lab-le\library\configs\ender.yaml')
ender = setup.ender
primitiv = setup.primitiv

# %%
import test_init
from controllably.Make.Light import LEDArray

leds = LEDArray(port='COM1', baudrate=9600, timeout=1, verbose=True, simulation=True)

# %%
import test_init
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
import test_init
from controllably.Move.grbl_api.grbl_api import GRBL

grbl = GRBL('COM22', baudrate=115200, timeout=1, simulation=True, verbose=True)
grbl.connect()
grbl.read(True)

# %%
import test_init
from controllably.Move.Cartesian import Marlin, Grbl

mover = Marlin('COM21')
# mover = Grbl('COM22')

# %%
import test_init
# from controllably.Make.ThinFilm import Multi_Spinner, Spinner
from controllably.Make.ThinFilm.spinner import Spinner, Multi_Spinner
details = [
    dict(port='COM17', verbose=True),
    dict(port='COM18', verbose=True),
    dict(port='COM19', verbose=True),
    dict(port='COM20', verbose=True),
]
spinners = Multi_Spinner.create(channels=[1,2,3,4], details=details, verbose=True)
spinners.connect()

# %%
spinners.spin(1000,5,blocking=True)

# %%
import inspect
import pprint
import sys

import test_init
from controllably.core.factory import get_imported_modules

mod = get_imported_modules('library')
pprint.pprint(mod)

# %%
import importlib.resources
import os
from pathlib import Path

path_string = 'control-lab-le/tests/files/corning_24_wellplate_3400ul.json'
p = Path('control-lab-le/tests/files/corning_24_wellplate_3400ul.json')

parent = [os.path.sep] + os.getcwd().split(os.path.sep)[1:]
path = os.path.normpath(path_string).split(os.path.sep)
full_path = os.path.abspath(os.path.join(*parent[:parent.index(path[0])], *path))
full_path

# %%
from typing import Sequence

def zip_kwargs_to_dict(primary_key:str, kwargs:dict) -> dict:
    """
    Checks and zips multiple keyword arguments of lists into dictionary
    
    Args:
        primary_keyword (str): primary keyword to be used as key
    
    Kwargs:
        key, list[...]: {keyword, list of values} pairs

    Raises:
        Exception: Ensure the lengths of inputs are the same

    Returns:
        dict: dictionary of (primary keyword, kwargs)
    """
    length = len(kwargs[primary_key])
    for key, value in kwargs.items():
        if isinstance(value, Sequence):
            continue
        if isinstance(value, set):
            kwargs[key] = list(value)
            continue
        kwargs[key] = [value]*length
    keys = list(kwargs.keys())
    assert all(len(kwargs[key]) == length for key in keys), f"Ensure the lengths of these inputs are the same: {', '.join(keys)}"
    primary_values = kwargs.pop(primary_key)
    other_values = [v for v in zip(*kwargs.values())]
    sub_dicts = [dict(zip(keys[1:], values)) for values in other_values]
    new_dict = dict(zip(primary_values, sub_dicts))
    return new_dict

kwargs = dict(
    name=['A','B','C'],
    value=[1,2,3],
    other=5
)

zip_kwargs_to_dict('name', kwargs)

# %%
import datetime

seconds = 1e6
delta = datetime.timedelta(seconds=seconds)

strings = str(delta).split(' ')
strings[-1] = "{}h {}min {}sec".format(*strings[-1].split(':'))
' '.join(strings)

# %%
print("{}h {}min {}sec".format(*str(delta).split(':')))

# %%

# %%
import test_init
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
import numpy as np
from scipy.spatial.transform import Rotation

import test_init
from controllably.core.position import get_transform

internal_points = np.array([(10,10,0), (80,10,0), (10,60,0), (80,60,0)])
external_points = np.array([(50,50,0), (50,120,0), (0,50,0), (0,120,0)])
transform = get_transform(internal_points, external_points)
transform

# %%
import logging

import test_init
from controllably.core.compound import Combined
from controllably.Make.Heat import Peltier
from controllably.Make.Mixture.QInstruments import BioShake

# logging.basicConfig(level=logging.DEBUG)

config = dict(
    port='COM1',
    baudrate=9600,
    timeout=1,
    verbose=True,
    simulation=True,
    details=dict(
        heater=dict(
            part_class=Peltier,
            port='COM2'
        ),
        heatr=dict(
            part_class=Peltier,
            port='COM3'
        )
    )
)

comb = Combined.fromConfig(config)


# %%
import test_init
from controllably.core.position import BoundingBox, Position

p = Position((1,2,3))
dim = (100,200,300)
buffer = ((-10,-20,-30),(40,50,60))
bb = BoundingBox(reference=p, dimensions=dim, buffer=buffer)

# %%
point = (1,2,3)
point in bb

# %%
point = (-10,2,3)
point in bb

# %%
import json
from pathlib import Path
from types import SimpleNamespace
import test_init
from controllably.core.position import Labware, Deck

labware_file = Path('control-lab-le/tests/files/labware/corning_24_wellplate_3400ul.json')
labware = Labware.fromFile(labware_file)
labware.show()

deck_file = Path('control-lab-le/tests/files/deck/deck_pescador.json')
deck = Deck.fromFile(deck_file)
deck.show()
deck

positions = deck.getAllPositions()
my_positions = json.loads(json.dumps(positions), object_hook=lambda item: SimpleNamespace(**item))

# %%
for n,bb in deck.exclusion_zone.items():
    print(n)
    print(bb.bounds)

# %%
import gc
import inspect

import test_init
from controllably.core.compound import Ensemble
from controllably.core.device import SerialDevice
from controllably.Make.Heat import Peltier

# %%
Multi_Peltier = Ensemble.factory(Peltier)
details = [
    dict(port='COM1',baudrate=115200,timeout=2, simulation=True),
    # dict(port='COM2',baudrate=9600,timeout=3, simulation=True),
]
multi = Multi_Peltier.create(channels=[0,1], details=details)
# multi.parts.chn_0.device.is_connected
# %%
multi.connect()
multi.parts.chn_0.device.is_connected
# %%
print(multi.parts.chn_0.device)
print(multi.parts.chn_1.device)

# %%
details = [
    dict(port='COM1',baudrate=115200,timeout=5, simulation=True),
    # dict(port='COM2',baudrate=115200,timeout=3, simulation=True),
]
multi2 = Multi_Peltier.create(channels=[0,1], details=details)
multi2.parts.chn_0.device.is_connected
# %%
print(multi2.parts.chn_0.device)
print(multi2.parts.chn_1.device)

# %%
inspect.signature(multi.setTemperature)

# %%
from controllably.Make import Maker
from controllably.Make.Mixture.QInstruments import BioShake
from controllably.Make.Heat import Peltier

maker = Peltier(verbose=True, port=None)

# %%
maker = BioShake(verbose=True, port=None)

# %%
maker = Maker(verbose=True, port=None, baudrate=9600, timeout=1)
maker.connection_details
# %%
maker.connect()
maker.is_connected
maker.device.write('M3')
maker.device.read()
maker.device.query('G0')
maker.disconnect()
# %%
maker.execute()
# %%
maker.connection_details
# %%
maker.verbose = False
# %%
