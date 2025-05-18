# %%
import test_init
from controllably.core.implementations.control import create_socket_worker
from controllably.core.connection import get_host

from controllably.core.control import TwoTierQueue
from controllably.Move.Cartesian import Gantry
from controllably.Transfer.Liquid.Pipette.Sartorius.sartorius import Sartorius
from controllably.Transfer.Liquid.Pipette.Sartorius.sartorius_api.sartorius_api import SartoriusDevice
from controllably.Transfer.Liquid.Pump.TriContinent.tricontinent import TriContinent

import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

HUB = False
PORT = 12345
HOST = get_host()

# %%
worker, worker_pack = create_socket_worker(HOST, PORT, 'WORKER', relay=HUB)

# %%
q = TwoTierQueue()
worker.register(q, 'QUEUE')
q.put_nowait('hello world')

# %%
mover = Gantry('COM0',[[100,100,100],[-100,-100,-100]], simulation=True)
worker.register(mover, 'MOVER')
worker.object_methods

# %%
pipette_device = SartoriusDevice('COM0', simulation=True, verbose=True)
pipette_device.connect()
pipette_device.getInfo(model='BRL1000')
pipette = Sartorius('COM0', simulation=True, device=pipette_device, verbose=True)
pipette.attach(90)
worker.register(pipette, 'PIPETTE')
pipette.aspirate(400)

# %%
pump = TriContinent('COM11', 1000, output_right=False, simulation=False, verbose=True)
pump.connect()
worker.register(pump, 'PUMP')

# %%
