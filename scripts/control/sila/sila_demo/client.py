# %%
from pathlib import Path
from controllably.core.connection import get_host
from controllably.core.position import Position
from sila2.client import SilaClient

SETUP_NAME = 'claw_machine'
HOST = get_host()
PORT = 50052

client = SilaClient(
    HOST, PORT,
    # insecure = True,
    root_certs = open(Path(__file__).parent/'ca.pem', 'rb').read(),
)

# %%
client.Gantry.Position.get()

# %%
client.Gantry.Home()

# %%
client.Sartorius.IsTipOn.get()

# %%
client.Sartorius.Home()

# %%
