"""
This __init__.py file initializes and imports the setups defined in this sub-folder.

Attributes:
    setup (Platform|namedtuple|dict)
    CONFIG_FILE (str)
    LAYOUT_FILE (str)
    REGISTRY_FILE (str)
"""
from dataclasses import dataclass
from pathlib import Path
from controllably.core.factory import load_setup_from_files         # pip install control-lab-ly
__all__ = ['CONFIG_FILE', 'LAYOUT_FILE', 'REGISTRY_FILE', 'setup']

HERE = Path(__file__).parent.absolute()
CONFIGS = Path(__file__).parent.parent.absolute()
CONFIG_FILE = HERE/"config.yaml"
LAYOUT_FILE = HERE/"layout.json"
REGISTRY_FILE = CONFIGS/"registry.yaml"

setup = load_setup_from_files(CONFIG_FILE, REGISTRY_FILE, create_tuple=True)
"""NOTE: importing SETUP gives the same instance wherever you import it"""

# ========== Optional (for typing) ========== #
# from ... import _tool_class

@dataclass
class Platform:
    ...
    # Add fields and types here
    # _tool_name: _tool_class

if len(Platform.__annotations__) > 0:
    setup = Platform(**setup._asdict())