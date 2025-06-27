import pytest
import logging
from controllably.Transfer.Liquid.Pump.TriContinent import Multi_TriContinent
from controllably.core.connection import get_ports

PORT = 'COM11'

pytestmark = pytest.mark.skipif((PORT not in get_ports()), reason="Requires serial connection to device")

@pytest.fixture(scope='session')
def pumps():
    pmps = Multi_TriContinent(**{
        'channels': (1,2),
        'details': [
            {
            'port': 'COM11',
            'capacity': 1000,
            'output_right': True,
            'channel': 1,
            'verbose': True
            },
            {
            'port': 'COM11',
            'capacity': 1000,
            'output_right': True,
            'channel': 2,
            'verbose': True
            }
        ]
    })
    pmps.home()
    return pmps

def test_multi_initialize(pumps):
    pumps.home()
    assert all([pumps.channels[c].init_status for c in (1,2)])
    assert all([pumps.channels[c].output_right for c in (1,2)])

def test_multi_aspirate(pumps):
    assert all([pumps.channels[c].volume == 0 for c in (1,2)])
    pumps.aspirate(100)
    assert all([pumps.channels[c].volume == 100 for c in (1,2)])
    pumps.aspirate(900)
    assert all([pumps.channels[c].volume == 1000 for c in (1,2)])
    pumps.home()

def test_multi_dispense(pumps):
    assert all([pumps.channels[c].volume == 0 for c in (1,2)])
    pumps.aspirate(100)
    assert all([pumps.channels[c].volume == 100 for c in (1,2)])
    pumps.dispense(200)
    assert all([pumps.channels[c].volume == 800 for c in (1,2)])
    pumps.home()

def test_reverse(pumps):
    pumps.reverse()
    assert all([pumps.channels[c].output_right for c in (1,2)])
    assert pumps.device.output_right == False
    pumps.aspirate(500)
    assert all([pumps.channels[c].volume == 500 for c in (1,2)])
    for c in (1,2):
        pumps.setActiveChannel(c)
        pumps.channels[c].setChannel()
        pumps.device.setValvePosition('I')
        pumps.device.moveTo(0)
    assert all([pumps.channels[c].volume == 0 for c in (1,2)])

    pumps.home()
    assert all([pumps.channels[c].output_right for c in (1,2)])
    assert pumps.device.output_right == True
    pumps.aspirate(1000)
    assert all([pumps.channels[c].volume == 1000 for c in (1,2)])
    pumps.dispense(1000)
    assert all([pumps.channels[c].volume == 0 for c in (1,2)])
    pumps.home()
