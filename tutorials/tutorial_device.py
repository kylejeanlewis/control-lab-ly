# %%
from controllably.core.device import BaseDevice, SerialDevice, SocketDevice, WebsocketDevice

# %%
ws = WebsocketDevice('echo.websocket.org', None, timeout=2)
# ws = WebsocketDevice('192.109.209.46', port=81, timeout=1, init_timeout=0, verbose=True, write_format='{data}', read_format='{data}')

# %%
ws.readAll()

# %%
ws.query('@')

# %%
ws.query('#0', False)

# %%
ws.query('#100', False)

# %%
ws.write('@\n')
# %%
