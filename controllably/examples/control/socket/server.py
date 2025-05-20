# -*- coding: utf-8 -*-
from ....core.connection import get_host
from .utils import create_socket_hub
import time

PORT = 12345
HOST = get_host()

def start_server():
    """
    Start the socket hub server.
    """
    hub, hub_pack = create_socket_hub(HOST, PORT, 'HUB', relay=True)
    print(f"Socket hub server started at {HOST}:{PORT}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping hub...")
    return

# Start the server if not yet running
if __name__ == "__main__":
    start_server()
