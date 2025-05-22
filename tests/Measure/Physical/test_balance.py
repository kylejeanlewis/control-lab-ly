# %%
import pytest
import time
from controllably.Measure.Physical import Balance
from controllably.core.connection import get_ports

PORT = 'COM32'
configs = {
    'port': PORT,
    'correction_parameters': (1.0, 0.0),
    'calibration_factor': 1.0,
    'force_tolerance': 0.01,
    'stabilize_timeout': 1
}

pytestmark = pytest.mark.skipif((PORT not in get_ports()), reason="Requires serial connection to device")

@pytest.fixture(scope='session')
def balance():
    bal = Balance(**configs)
    return bal

def test_get_attributes(balance):
    balance.reset()
    attributes = balance.getAttributes()
    expected_attributes = {k:v for k,v in configs.items() if k not in ['port']}
    expected_attributes['baseline'] = 0
    assert attributes == expected_attributes, f"Expected {expected_attributes}, but got {attributes}"

def test_zero(balance):
    balance.reset()
    assert balance.baseline == 0, "Baseline should be set to 0 after resetting"
    balance.zero()
    assert balance.baseline != 0, "Baseline should be set to current reading after zeroing"

def test_record(balance):
    balance.reset()
    assert len(balance.records) == 0, "Records should be empty after resetting"
    assert not balance.record_event.is_set(), "Recording should be False after record(False)"
    balance.record(True)
    assert balance.record_event.is_set(), "Recording should be True after record(True)"
    time.sleep(2)
    balance.record(False)
    assert not balance.record_event.is_set(), "Recording should be False after record(False)"
    assert len(balance.records) > 0, "Records should not be empty after recording"

# %%
if __name__ == "__main__":
    bal = Balance(**configs)

# %%
