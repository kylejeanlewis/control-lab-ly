from pathlib import Path
import sys
REPO = 'my-repo'
ROOT = str(Path().absolute()).split(REPO)[0]
sys.path.append(f'{ROOT}{REPO}')

from controllably import Helper
Helper.get_ports()

registry = Helper.read_yaml(f'{ROOT}{REPO}\\tools\\registry.yaml')
"""Registry of device addresses"""
addresses = registry['machine_id'][Helper.get_node()]
"""Device addresses for this machine"""

# Import plugins
from library.plugins.my_plugin import MyClass

# Define utility functions
...