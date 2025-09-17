# %% [markdown]
# # Connection utility functions
# 
# The `controllably.core.connection` module provides utility functions to manage and retrieve connection information for devices. 
# This includes functions to get available ports, host information, node identifiers, and to match IP addresses.

# %%
from controllably.core.connection import (
    get_addresses, get_host, get_node, get_ports, match_current_ip_address
)

# %% [markdown]
# A list if available communication ports connected to the system can be retrieved using the `get_ports()` function.

# %%
get_ports()

# %% [markdown]
# The `get_host()` function retrieves the hostname of the current machine.

# %%
host = get_host()
host

# %% [markdown]
# The `match_current_ip_address()` function checks if the provided hostname or IP address matches the current machine's IP address.

# %%
match_current_ip_address(host)

# %%
match_current_ip_address('127.0.0.1')

# %% [markdown]
# The `get_node()` function retrieves a unique identifier for the current machine, typically the MAC address.

# %%
mac_address = get_node()
mac_address

# %%
node = get_node(mac_address=False)
node

# %% [markdown]
# The `get_addresses()` function retrieves connection addresses from a provided registry dictionary, 
# using the current machine's identifier (MAC address or node name) to look up relevant entries.

# %%
registry = {
    'machine_id':{
        mac_address: {
            'port': {'__device__': 'COM3'},
            'cam_index': {'__cam__': 0}
        },
        node: {
            'port': {'__device__': 'COM6'},
            'cam_index': {'__cam__': 0}
        }
    }
}

# %%
get_addresses(registry)

# %%
get_addresses(registry, False)

# %%
