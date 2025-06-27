# %%
import pytest
from controllably.Measure.Chemical.Sentron import SI600
from controllably.core.connection import get_ports

PORT = 'COM36'

pytestmark = pytest.mark.skipif((PORT not in get_ports()), reason="Requires serial connection to device")

# %%
@pytest.fixture(scope='session')
def sentron():
    st = SI600(**{
        'port': PORT,
        'verbose': True
    })
