"""
This __init__.py file initializes and imports the setups defined in this sub-folder.

Attributes:
    CONFIG_FILE (str)
    LAYOUT_FILE (str)
    REGISTRY_FILE (str)
    
## Functions:
    setup: Load setup from files and return as NamedTuple or Platform
"""
from dataclasses import dataclass
from pathlib import Path
from controllably import get_setup         # pip install control-lab-ly
__all__ = ['CONFIG_FILE', 'LAYOUT_FILE', 'REGISTRY_FILE', 'setup']
__setup__ = None

HERE = Path(__file__).parent.absolute()
CONFIGS = Path(__file__).parent.parent.absolute()
CONFIG_FILE = HERE/"config.yaml"
LAYOUT_FILE = HERE/"layout.json"
REGISTRY_FILE = CONFIGS/"registry.yaml"

# ========== Optional (for typing) ========== #
# from ... import _tool_class

@dataclass
class Platform:
    ...
    # Add fields and types here
    # _tool_name: _tool_class
    
# ========================================== #

def setup(silent_fail:bool = False) -> tuple|Platform:
    global __setup__
    if __setup__ is not None:
        print(f"Setup already loaded from {CONFIG_FILE}")
        return __setup__
    __setup__ = get_setup(CONFIG_FILE, REGISTRY_FILE, Platform, silent_fail=silent_fail)
    return __setup__
