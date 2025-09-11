# %%
from controllably.core.connection import (
    get_addresses, get_host, get_node, get_ports, match_current_ip_address
)

# %%
get_ports()

# %%
host = get_host()
host

# %%
match_current_ip_address(host)

# %%
match_current_ip_address('127.0.0.1')

# %%
mac_address = get_node()
mac_address

# %%
node = get_node(mac_address=False)
node

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
