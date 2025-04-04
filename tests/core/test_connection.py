import pytest
import socket
import logging
import uuid
from controllably.core.connection import get_addresses, get_host, get_node, get_ports, match_current_ip_address

def test_get_addresses_listed_machine(monkeypatch):
    registry = {
        'machine_id': {
            123456789: {
                'port': {'__tool__': 'COM3'}, 
                'cam_index': {'__cam__': 'CAM1'}
            }
        }
    }
    monkeypatch.setattr('controllably.core.connection.get_node', lambda: 123456789)
    assert get_addresses(registry) == {'port': {'__tool__': 'COM3'}, 'cam_index': {'__cam__': 'CAM1'}}
    
def test_get_addresses_unlisted_machine():
    registry = {
        'machine_id': {
            123456789: {
                'port': {'__tool__': 'COM3'}, 
                'cam_index': {'__cam__': 'CAM1'}
            }
        }
    }
    assert get_addresses(registry) is None

def test_get_host():
    host = get_host()
    assert isinstance(host, str)
    assert host == socket.gethostbyname(socket.gethostname())

def test_get_node():
    node = get_node()
    assert isinstance(node, str)
    assert node == str(uuid.getnode())

def test_get_ports(monkeypatch, caplog):
    def mock_comports():
        return [
            ('COM3', 'USB Serial Port', 'USB VID:PID=1234:5678'),
            ('COM4', 'USB Serial Port', 'USB VID:PID=1234:5678')
        ]
    monkeypatch.setattr('serial.tools.list_ports.comports', mock_comports)
    with caplog.at_level(logging.INFO):
        ports = get_ports()
        assert ports == ['COM3', 'COM4']
        assert "COM3: [USB VID:PID=1234:5678] USB Serial Port" in caplog.text

def test_get_ports_no_port(monkeypatch, caplog):
    monkeypatch.setattr('serial.tools.list_ports.comports', lambda: [])
    with caplog.at_level(logging.WARNING):
        ports = get_ports()
        assert ports == []
        assert "No ports detected" in caplog.text

def test_match_current_ip_address(monkeypatch):
    def mock_gethostbyname_ex(hostname):
        return (hostname, [], ['192.168.1.2', '127.0.0.1'])
    monkeypatch.setattr('socket.gethostbyname_ex', mock_gethostbyname_ex)
    assert match_current_ip_address('192.168.1.3') == True
    assert match_current_ip_address('127.0.0.2') == True
    assert match_current_ip_address('192.168.2.2') == False
