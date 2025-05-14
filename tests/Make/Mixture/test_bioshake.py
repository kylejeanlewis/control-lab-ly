import pytest
import time
from controllably.Make.Mixture.QInstruments import BioShake
from controllably.core.connection import get_ports

PORT = 'COM33'

pytestmark = pytest.mark.skipif((PORT not in get_ports()), reason="Requires serial connection to device")

@pytest.fixture(scope="session")
def shaker():
    bs = BioShake(**{
        'port': PORT,
        'verbose': True,
    })
    return bs

def test_grip(shaker):
    shaker.grip(False)
    assert shaker.getElmState() == 3
    shaker.grip(True)
    assert shaker.getElmState() == 1
    shaker.grip(False)
    
def test_shake(shaker):
    shaker.shake(speed=1000, duration=5, blocking=True)
    time.sleep(5)
    assert shaker.atSpeed(0)

def test_shake_nonblocking(shaker):
    shaker.shake(speed=1000, blocking=False)
    assert not shaker.atSpeed(1000)
    time.sleep(10)
    assert shaker.atSpeed(1000, tolerance=0.05)
    shaker.toggleShake(on=False, home=True)
    assert not shaker.atSpeed(0)
    time.sleep(10)
    assert shaker.atSpeed(0)
