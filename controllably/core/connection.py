# -*- coding: utf-8 -*-
""" 
This module provides classes for handling connections to serial and socket devices.
    
## Classes:
    `SocketUtils`: Socket utility class for handling socket connections
    `Server`: Server class for handling socket connections
    `Client`: Client class for handling socket connections
    
## Functions:
    `get_addresses`: Get the appropriate addresses for current machine
    `get_host`: Get the host IP address for current machine
    `get_node`: Get the unique identifier for current machine
    `get_ports`: Get available serial ports connected to current machine
    `match_current_ip_address`: Match the current IP address of the machine
    
<i>Documentation last updated: 2024-11-12</i>
"""
# Standard library imports
from __future__ import annotations
import ipaddress
import logging
import socket
import uuid

# Third party imports
import serial                       # pip install pyserial

# Local application imports
from .archives._connection import *

_logger = logging.getLogger("controllably.core")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.addFilter(logging.Filter(__name__+'.'))
logger.addHandler(handler)

def get_addresses(registry:dict|None) -> dict|None:
    """
    Get the appropriate addresses for current machine

    Args:
        registry (dict|None): dictionary with serial port addresses and camera ids

    Returns:
        dict|None: dictionary of serial port addresses and camera ids for current machine, if available
    """
    node_id = get_node()
    addresses = registry.get('machine_id',{}).get(node_id,{}) if registry is not None else {}
    if len(addresses) == 0:
        logger.warning("Append machine id and camera ids/port addresses to registry file")
        logger.warning(f"Machine not yet registered. (Current machine id: {node_id})")
        return None
    return addresses

def get_host() -> str:
    """
    Get the host IP address for current machine

    Returns:
        str: machine host IP address
    """
    host = socket.gethostbyname(socket.gethostname())
    host_out = f"Current machine host: {host}"
    logger.info(host_out)
    return host

def get_node() -> str:
    """
    Get the unique identifier for current machine

    Returns:
        str: machine unique identifier
    """
    node_id = str(uuid.getnode())
    node_out = f"Current machine id: {node_id}"
    logger.info(node_out)
    return node_id

def get_ports() -> list[str]:
    """
    Get available serial ports connected to current machine

    Returns:
        list[str]: list of connected serial ports
    """
    ports = []
    for port, desc, hwid in sorted(serial.tools.list_ports.comports()):
        ports.append(str(port))
        port_desc = f"{port}: [{hwid}] {desc}"
        logger.info(port_desc)
    if len(ports) == 0:
        logger.warning("No ports detected!")
    return ports

def match_current_ip_address(ip_address:str) -> bool:
    """
    Match the current IP address of the machine

    Returns:
        bool: whether the IP address matches the current machine
    """
    hostname = socket.gethostname()
    local_ips = socket.gethostbyname_ex(hostname)[2]
    success = False
    for local_ip in local_ips:
        local_network = f"{'.'.join(local_ip.split('.')[:-1])}.0/24"
        if ipaddress.ip_address(ip_address) in ipaddress.ip_network(local_network):
            success = True
            break
    return success
