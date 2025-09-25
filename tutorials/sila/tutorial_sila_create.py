# %%
import importlib
from pathlib import Path

from controllably.examples.sila.factory import create_setup_sila_package

ROOT = Path(__file__).parent.parent.parent.parent
SETUP_NAME = 'overkill'

# %%
setup = importlib.import_module(f'tools.{SETUP_NAME}').setup()

# %%
create_setup_sila_package (
    setup = setup,
    setup_name = SETUP_NAME,
    dst_folder = ROOT/'sila',
    library = ROOT/'library'/'sila'
)