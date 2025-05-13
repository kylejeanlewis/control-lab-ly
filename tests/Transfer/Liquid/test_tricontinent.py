import pytest
import time
from controllably.Transfer.Liquid.Pump.TriContinent import TriContinent, Multi_TriContinent
from controllably.core.connection import get_ports

PORT = 'COM11'

pytestmark = pytest.mark.skipif((PORT not in get_ports()), reason="Requires serial connection to device")

@pytest.fixture(scope='session')
def pump():
    pmp = TriContinent(**{
        'port': PORT,
        'capacity': 1000,
        'output_right': False,
        'verbose': True
    })
    pmp.connect()
    return pmp

def test_initialize(pump):
    pump.device.initialize(False)
    assert pump.init_status == True
    assert pump.device.output_right == False

def test_aspirate(pump):
    assert pump.volume == 0
    pump.aspirate(100)
    assert pump.volume == 100
    pump.home()

def test_dispense(pump):
    pump.aspirate(100)
    assert pump.volume == 100
    pump.dispense(100)
    assert pump.volume == 0
    pump.home()


# @pytest.fixture(scope='session')
# def pumps():
#     pmps = Multi_TriContinent(**{
#         'channels': (1,2),
#         'details': {
#             'port': PORT,
#             'capacity': 1000,
#             'output_right': False,
#             'verbose': True
#         }
#     })
#     pmps.connect()
#     return pmps

# def test_multi_initialize(pumps):
#     for channel in (1,2):
#         pumps.setActiveChannel(channel)
#         # print(pumps.device.output_right)
#         # pumps.device.initialize()
#         # assert pumps.init_status == True
#         # assert pumps.device.output_right == False

# def test_multi_aspirate(pumps):
#     for channel in (1,2):
#         pumps.setActiveChannel(channel)
#         assert pumps.volume == 0
#         pumps.aspirate(100)
#         assert pumps.volume == 100
#         pumps.home()

# def test_multi_dispense(pumps):
#     for channel in (1,2):
#         pumps.setActiveChannel(channel)
#         pumps.aspirate(100)
#         assert pumps.volume == 100
#         pumps.dispense(100)
#         assert pumps.volume == 0
#         pumps.home()
