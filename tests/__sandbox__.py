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
bb = BoundingBox(p, dim, buffer)

# %%
point = (1,2,3)
point in bb

# %%
point = (-10,2,3)
point in bb

# %%
from pathlib import Path
import test_init
from controllably.core.position import Labware, Deck

labware_file = Path(r'C:\Users\chang\Downloads\corning_24_wellplate_3400ul.json')
labware = Labware.fromFile(labware_file)
labware.show()

deck_file = Path(r'C:\Users\chang\GitHub\control-lab-le\deck_sample.json')
deck = Deck.fromFile(deck_file)
deck.show()
deck

# %%
for n,bb in deck.exclusion_zone.items():
    print(n)
    print(bb.bounds)

# %%
import gc
import inspect

import test_init
from controllably.core.compound import Ensemble
from controllably.core.connection import SerialDevice
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
