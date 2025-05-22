# %%
import pytest
import time
from controllably.Measure.Electrical.Keithley import Keithley
from controllably.Measure import Program
from controllably.core.connection import match_current_ip_address

HOST = '192.109.209.104'

configs = {
    'host': HOST,
    'keithley_class': 'Keithley2450',
    'verbose': True,
}

pytestmark = pytest.mark.skipif((not match_current_ip_address(HOST)), reason="Requires connection to local lab network")


# %%
@pytest.fixture(scope='session')
def keithley():
    kl = Keithley(**configs)
    return kl

def test_load_program(keithley):
    ...
    # keithley.loadProgram()
    # check technique doc printout
    
def test_measure(keithley):
    keithley.reset()
    # assert len(keithley.runs) == 0
    # assert keithley.program is None
    # keithley.loadProgram()
    # parameters = {'time': 3, 'channels': [0]}
    
    # df = keithley.measure(parameters=parameters)
    # assert len(keithley.runs) == 1
    # assert len(df) == 4
    # assert len(keithley.records_df) == 4
    
    # parameters = {'time': 2, 'channels': [0]}
    # df = keithley.measure(parameters=parameters)
    # assert len(keithley.runs) == 2
    # assert len(df) == 3
    # assert len(keithley.records_df) == 3
    
    # keithley.getData(1)
    # assert len(keithley.records_df) == 4
    

# %%
if __name__ == '__main__':
    kl = Keithley(**configs)
    
# %%
