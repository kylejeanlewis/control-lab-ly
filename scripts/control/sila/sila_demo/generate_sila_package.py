import importlib
from pathlib import Path

from controllably.examples.sila.factory import create_setup_sila_package
ROOT = Path(r'~\lab-dance')
SETUP_NAME = 'claw_machine'

# Initialize the setup
setup = importlib.import_module(f'tools.{SETUP_NAME}').setup()
# Equivalent to:
# >>> from tools import claw_machine
# >>> setup = claw_machine.setup()

create_setup_sila_package (
    setup = setup,
    setup_name = SETUP_NAME,
    dst_folder = ROOT/'sila',
    library = ROOT/'library'/'sila'
)
# The above function performs several actions:
# 1) Creates XML templates from objects in the setup
#    a) copies XML templates from library if available
# 2) Generate a SiLA2 package from the setup
# 3) Modify the implementation files and server code
#    a) copies implementations from library if available
# 4) Install the new SiLA2 package for setup