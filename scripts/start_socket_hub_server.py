from controllably.core.connection import get_host
from control_utils import create_socket_hub

if __name__ == "__main__":
    hub, hub_pack = create_socket_hub(get_host(), 12345, 'HUB', relay=True)
    