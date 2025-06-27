# %%
import pytest
import time
from controllably.Measure.Mechanical import ActuatedSensor
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
def actuated_sensor():
    acs = ActuatedSensor(**configs)
    return acs

def test_get_attributes(actuated_sensor):
    actuated_sensor.reset()
    attributes = actuated_sensor.getAttributes()
    expected_attributes = {k:v for k,v in configs.items() if k not in ['port']}
    expected_attributes['baseline'] = 0
    assert attributes == expected_attributes, f"Expected {expected_attributes}, but got {attributes}"

def test_zero(actuated_sensor):
    actuated_sensor.reset()
    assert actuated_sensor.baseline == 0, "Baseline should be set to 0 after resetting"
    actuated_sensor.zero()
    assert actuated_sensor.baseline != 0, "Baseline should be set to current reading after zeroing"

def test_record(actuated_sensor):
    actuated_sensor.reset()
    assert len(actuated_sensor.records) == 0, "Records should be empty after resetting"
    assert not actuated_sensor.record_event.is_set(), "Recording should be False after record(False)"
    actuated_sensor.record(True)
    assert actuated_sensor.record_event.is_set(), "Recording should be True after record(True)"
    time.sleep(2)
    actuated_sensor.record(False)
    assert not actuated_sensor.record_event.is_set(), "Recording should be False after record(False)"
    assert len(actuated_sensor.records) > 0, "Records should not be empty after recording"

# %%
if __name__ == "__main__":
    acs = ActuatedSensor(**configs)

# %%
