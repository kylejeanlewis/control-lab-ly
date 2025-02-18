# %%
import threading

import test_init
from controllably.core.connection import get_host
from controllably.core.control import Controller, start_server, start_client
from controllably.core.interpreter import JSONInterpreter

from controllably.core.control import TwoTierQueue
from controllably.Move.Cartesian import Gantry

from controllably.Transfer.Liquid.Sartorius.sartorius import Sartorius
from controllably.Transfer.Liquid.Sartorius.sartorius_api.sartorius_api import SartoriusDevice
from controllably.Transfer.Liquid.Pumps.TriContinent.tricontinent import TriContinent
from controllably.Transfer.Liquid.Pumps.TriContinent.tricontinent_api.tricontinent_api import TriContinentDevice

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# %%
host = get_host()
port = 12345
worker = Controller('model', JSONInterpreter())
terminate = threading.Event()
args = [host, port, worker]
kwargs = dict(terminate=terminate)
worker.start()

# %% Client-server version
worker_thread = threading.Thread(target=start_server, args=args, kwargs=kwargs, daemon=True)
worker_thread.start()

# %% Hub-spoke version
args.append(True)
worker_thread = threading.Thread(target=start_client, args=args, kwargs=kwargs, daemon=True)
worker_thread.start()

# %%
q = TwoTierQueue()
worker.register(q)
q.put_nowait('12345')

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
pump_device = TriContinentDevice('COM0', simulation=True, verbose=True)
pump_device.connect()
pump_device.getInfo()
pump = TriContinent('COM0', 5000, simulation=True, device=pump_device, verbose=True)
worker.register(pump, 'PUMP')
pump.dispense(400) 

# %%
