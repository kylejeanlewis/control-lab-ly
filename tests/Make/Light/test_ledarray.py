# %%
import pytest
import time
from controllably.Make.Light import Multi_LED

PORT = 'COM45'
configs = {
    'channels': [0,1,2,3],
    'details': {
        'port': PORT,
        'baudrate': 9600,
        'timeout': 1,
        'verbose': True,
        'simulation': False
}}

# %%
@pytest.fixture
def led_array():
    """Fixture to create an instance of LEDArray."""
    mled = Multi_LED(**configs)
    mled.device.verbose = True
    time.sleep(2)
    mled.connect()
    return mled

# %%
def test_set_power(led_array):
    ...
    
    
# %%
if __name__ == "__main__":
    mled = Multi_LED(**configs)
    mled.device.verbose = True
    time.sleep(2)
    mled.connect()
    
# %%
