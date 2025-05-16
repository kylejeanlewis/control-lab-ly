import pytest
import time
from controllably.Make.Light import Multi_LED
from controllably.core.connection import get_ports

PORT = 'COM45'

pytestmark = pytest.mark.skipif((PORT not in get_ports()), reason="Requires serial connection to device")

configs = {
    'channels': [0,1,2,3],
    'details': {
        'port': PORT,
        'baudrate': 9600,
        'timeout': 1,
        'verbose': False,
        'simulation': False
}}

@pytest.fixture(scope="session")
def led_array():
    """Fixture to create an instance of LEDArray."""
    mled = Multi_LED(**configs)
    mled.device.verbose = True
    time.sleep(1)
    mled.connect()
    return mled


def test_set_power(led_array):
    led_array.setPower(0)
    led_array.setPower(100)
    time.sleep(1)
    assert all([(led_array.channels[led].target_power==100) for led in led_array.channels])
    for i in range(len(led_array.channels)):
        led_array.setPower(0, channel=i)
        time.sleep(1)
        assert led_array.channels[i].target_power == 0

def test_light(led_array):
    led_array.setPower(0)
    led_array.light(100, 10, blocking=False)
    time.sleep(2)
    assert all([(led_array.channels[led].target_power==100) for led in led_array.channels])
    time.sleep(10)
    assert all([(led_array.channels[led].target_power==0) for led in led_array.channels])

def test_stop(led_array):
    led_array.setPower(0)
    led_array.light(100, 10, blocking=False)
    time.sleep(2)
    assert all([(led_array.channels[led].target_power==100) for led in led_array.channels])
    led_array.stop(channel=1)
    target_powers = [led_array.channels[led].target_power for led in led_array.channels]
    assert target_powers == [100, 0, 100, 100]
    led_array.stop()
    assert all([(led_array.channels[led].target_power==0) for led in led_array.channels])
