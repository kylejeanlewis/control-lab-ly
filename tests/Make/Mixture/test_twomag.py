import pytest
from controllably.Make.Mixture.TwoMag import TwoMagStirrer
from controllably.core.connection import get_ports

PORT = 'COM40'

pytestmark = pytest.mark.skipif((PORT not in get_ports()), reason="Requires serial connection to device")

@pytest.fixture(scope="session")
def stirrer():
    stir = TwoMagStirrer(**{
        'port': PORT
    })
    return stir

def test_stirrer(stirrer):
    assert stirrer.is_connected
    stirrer.disconnect()
    assert not stirrer.is_connected
    stirrer.connect()
    model, status = stirrer.getStatus()
    assert model == stirrer.device.version
    assert status == 'OFF'
    
def test_set_power(stirrer):
    stirrer.setPower(50)
    assert stirrer.power == 50
    assert stirrer.getPower() == 50
    stirrer.setPower(70)
    assert stirrer.power == 75
    assert stirrer.getPower() == 75
    stirrer.setDefault()
    
def test_set_speed(stirrer):
    stirrer.setSpeed(500)
    assert stirrer.speed == 500
    assert stirrer.getSpeed() == 500
    stirrer.setDefault()

def test_start_stop(stirrer):
    ret = stirrer.start()
    assert ret
    assert stirrer.getStatus()[1] == 'REM' # Remote mode
    ret = stirrer.stop()
    assert ret
    assert stirrer.getStatus()[1] == 'OFF' # Off mode
    stirrer.setDefault()
