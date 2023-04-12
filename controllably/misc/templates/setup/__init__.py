"""
This __init__.py file initialises and imports the setups defined in this sub-folder.

Other constants and variables:
    CONFIG_FILE (str)
    CONFIGS (str)
    HERE (str)
    LAYOUT_FILE (str)
    REGISTRY_FILE (str)
    setup (namedtuple)
"""
from pathlib import Path
from controllably import load_setup         # pip install control-lab-ly

HERE = str(Path(__file__).parent.absolute()).replace('\\', '/')
CONFIGS = str(Path(__file__).parent.parent.absolute()).replace('\\', '/')

CONFIG_FILE = f"{HERE}/config.yaml"
LAYOUT_FILE = f"{HERE}/layout.json"
REGISTRY_FILE = f"{CONFIGS}/registry.yaml"

setup = load_setup(config_file=CONFIG_FILE, registry_file=REGISTRY_FILE)
"""NOTE: importing SETUP gives the same instance wherever you import it"""