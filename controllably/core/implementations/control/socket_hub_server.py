# -*- coding: utf-8 -*-
from ...connection import get_host
from .control_utils import create_socket_hub

PORT = 12345
HOST = get_host()

if __name__ == "__main__":
    hub, hub_pack = create_socket_hub(HOST, PORT, 'HUB', relay=True)
    