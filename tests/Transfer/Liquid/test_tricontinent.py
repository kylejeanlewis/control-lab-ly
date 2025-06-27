import pytest
from controllably.Transfer.Liquid.Pump.TriContinent import TriContinent
from controllably.core.connection import get_ports

PORT = 'COM11'

pytestmark = pytest.mark.skipif((PORT not in get_ports()), reason="Requires serial connection to device")

@pytest.fixture(scope='session')
def pump():
    pmp = TriContinent(**{
        'port': PORT,
        'capacity': 1000,
        'output_right': True,
        'verbose': True
    })
    pmp.home()
    return pmp

def test_initialize(pump):
    pump.home()
    assert pump.init_status == True
    assert pump.device.output_right == True

def test_aspirate(pump):
    assert pump.volume == 0
    pump.aspirate(100)
    assert pump.volume == 100
    pump.aspirate(900)
    assert pump.volume == 1000
    pump.home()

def test_dispense(pump):
    assert pump.volume == 0
    pump.aspirate(100)
    assert pump.volume == 100
    pump.dispense(200)
    assert pump.volume == 800
    pump.home()

def test_reverse(pump):
    pump.reverse()
    assert pump.output_right == True
    assert pump.device.output_right == False
    pump.aspirate(500)
    assert pump.volume == 500
    pump.device.setValvePosition('I')
    pump.device.moveTo(0)
    assert pump.volume == 0

    pump.home()
    assert pump.output_right == True
    assert pump.device.output_right == True
    pump.aspirate(1000)
    assert pump.volume == 1000
    pump.dispense(1000)
    assert pump.volume == 0
    pump.home()
