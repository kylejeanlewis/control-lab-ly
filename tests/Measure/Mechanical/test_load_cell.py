# %%
import pytest
import time
from controllably.Measure.Mechanical import LoadCell
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
def load_cell():
    lc = LoadCell(**configs)
    return lc

def test_get_attributes(load_cell):
    load_cell.reset()
    attributes = load_cell.getAttributes()
    expected_attributes = {k:v for k,v in configs.items() if k not in ['port']}
    expected_attributes['baseline'] = 0
    assert attributes == expected_attributes, f"Expected {expected_attributes}, but got {attributes}"

def test_zero(load_cell):
    load_cell.reset()
    assert load_cell.baseline == 0, "Baseline should be set to 0 after resetting"
    load_cell.zero()
    assert load_cell.baseline != 0, "Baseline should be set to current reading after zeroing"

def test_record(load_cell):
    load_cell.reset()
    assert len(load_cell.records) == 0, "Records should be empty after resetting"
    assert not load_cell.record_event.is_set(), "Recording should be False after record(False)"
    load_cell.record(True)
    assert load_cell.record_event.is_set(), "Recording should be True after record(True)"
    time.sleep(2)
    load_cell.record(False)
    assert not load_cell.record_event.is_set(), "Recording should be False after record(False)"
    assert len(load_cell.records) > 0, "Records should not be empty after recording"

# %%
if __name__ == "__main__":
    lc = LoadCell(**configs)

# %%
