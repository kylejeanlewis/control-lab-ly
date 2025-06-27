# -*- coding: utf-8 -*-
"""
This module provides a socket hub server for managing connections in a distributed system.

Attributes:
    PORT (int): The port number for the socket hub server.
    HOST (str): The host address for the socket hub server.
    
## Functions:
    `start_server`: Starts the socket hub server.
    
<i>Documentation last updated: 2025-06-11</i>
"""
from ....core.connection import get_host
from .utils import create_socket_hub
import time

PORT = 12345
HOST = get_host()

def start_server():
    """Start the socket hub server."""
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
