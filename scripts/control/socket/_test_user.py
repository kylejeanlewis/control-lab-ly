# %%
import test_init
from controllably.examples.control.socket import create_socket_user
from controllably.core.connection import get_host

from controllably.core.control import Proxy, TwoTierQueue
from controllably.Move.Cartesian import Gantry
from controllably.Transfer.Liquid.Pipette.Sartorius.sartorius import Sartorius
from controllably.Transfer.Liquid.Pump.TriContinent.tricontinent import TriContinent
from controllably.examples.gui.tkinter import MovePanel, LiquidPanel

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

HUB = False
PORT = 12345
HOST = get_host()

# %%
user, user_pack = create_socket_user(HOST, PORT, 'USER', relay=HUB)

# %%
p = Proxy(TwoTierQueue(), 'QUEUE')
p.bindController(user)
p.get_nowait()

# %%
gantry = Gantry('COM0',[[100,100,100],[-100,-100,-100]], simulation=True)
mover = Proxy(gantry, 'MOVER')
mover.bindController(user)

# %%
mover.remote = True
position = mover.move('x',-10)
position

# %%
mover.remote = False
position = mover.move('x',10)
position

# %%
pipette = Proxy(Sartorius, 'PIPETTE')
pipette.bindController(user)

# %%
pump = Proxy(TriContinent, 'PUMP')
pump.bindController(user)

# %%
move_gui = MovePanel()
move_gui.show()
move_gui.bindObject(mover)
move_gui.show()

# %%
liquid_gui = LiquidPanel()
liquid_gui.show()
liquid_gui.bindObject(pipette)
liquid_gui.show()
liquid_gui.bindObject(pump)
liquid_gui.show()
