import pytest
import socket
import logging
import uuid

from ..context import controllably
from controllably.core.connection import get_addresses, get_host, get_node, get_ports, match_current_ip_address

registry = {
    'machine_id': {
        "123456789": {
            'port': {'__tool__': 'COM3'}, 
            'cam_index': {'__cam__': 'CAM1'}
        }
    }
}


@pytest.mark.parametrize("registry, node, expected", [
    (None, "000000000", None),
    (registry, "123456789", registry['machine_id']["123456789"]),
    (registry, "987654321", None),
])
def test_get_addresses(registry, node, expected, monkeypatch):
    monkeypatch.setattr('controllably.core.connection.get_node', lambda: node)
    addresses = get_addresses(registry)
    if expected is None:
        assert addresses is None
    else:
        assert addresses == expected

def test_get_host():
    host = get_host()
    assert isinstance(host, str)
    assert host == socket.gethostbyname(socket.gethostname())

def test_get_node():
    node = get_node()
    assert isinstance(node, str)
    assert node == str(uuid.getnode())

@pytest.mark.parametrize("available, expected, log", [
    (True, ['COM3', 'COM4'], "COM3: [USB VID:PID=1234:5678] USB Serial Port"),
    (False, [], "No ports detected"),
])
def test_get_ports(available, expected, log, caplog, monkeypatch):
    def mock_comports():
        if not available:
            return []
        return [
            ('COM3', 'USB Serial Port', 'USB VID:PID=1234:5678'),
            ('COM4', 'USB Serial Port', 'USB VID:PID=1234:5678')
        ]
    monkeypatch.setattr('serial.tools.list_ports.comports', mock_comports)
    with caplog.at_level(logging.INFO):
        ports = get_ports()
        assert ports == expected
        assert log in caplog.text

@pytest.mark.parametrize("hostname, expected", [
    ('192.168.1.1', True),
    ('127.0.0.2', True),
    ('192.168.2.2', False)
])
def test_match_current_ip_address(hostname, expected, monkeypatch):
    def mock_gethostbyname_ex(hostname):
        return (hostname, [], ['192.168.1.2', '127.0.0.1'])
    monkeypatch.setattr('socket.gethostbyname_ex', mock_gethostbyname_ex)
    assert match_current_ip_address(hostname) == expected
