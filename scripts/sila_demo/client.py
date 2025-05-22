# %%
from control_lab_lisa import Server

# %%
from sila2.client import SilaClient

client = SilaClient("127.0.0.1", 50052, insecure=True)

# %%
client.Gantry.Position.get()

# %%
client.Gantry.Home()
