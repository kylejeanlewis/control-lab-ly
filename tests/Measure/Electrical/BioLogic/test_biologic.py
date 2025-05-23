# %%
import pytest
import platform
import time

is_windows = platform.system() == 'Windows'
if platform.system() != 'Windows':
    pytest.skip("Windows platform required for easy-biologic", allow_module_level=True)
else:
    from easy_biologic import base_programs as bp
    from controllably.Measure.Electrical.BioLogic import BioLogic
    from controllably.core.connection import match_current_ip_address

HOST = '192.109.209.128'

configs = {
    'host': HOST,
    'verbose': True,
}
pytestmark = pytest.mark.skipif((not match_current_ip_address(HOST)), reason="Requires connection to local lab network and running on Windows")

# %%
@pytest.fixture(scope='session')
def biologic():
    bl = BioLogic(**configs)
    return bl

def test_load_program(biologic):
    biologic.loadProgram(bp.OCV)
    # check technique doc printout
    
def test_measure(biologic):
    biologic.reset()
    assert len(biologic.runs) == 0
    assert biologic.program is None
    biologic.loadProgram(bp.OCV)
    parameters = {'time': 3, 'channels': [0]}
    
    df = biologic.measure(parameters=parameters)
    assert len(biologic.runs) == 1
    assert len(df) == 4
    assert len(biologic.records_df) == 4
    
    parameters = {'time': 2, 'channels': [0]}
    df = biologic.measure(parameters=parameters)
    assert len(biologic.runs) == 2
    assert len(df) == 3
    assert len(biologic.records_df) == 3
    
    biologic.getData(1)
    assert len(biologic.records_df) == 4
    

# %%
if __name__ == '__main__':
    bl = BioLogic(**configs)
    bl.loadProgram(bp.OCV)
    parameters = {'time': 3, 'channels': [0]}
    df = bl.measure(parameters=parameters)
    print(df)
    
# %%
