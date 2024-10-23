from pathlib import Path
import sys
REPO = 'control-lab-le'
ROOT = str(Path().absolute()).split(REPO)[0]
sys.path.append(f'{ROOT}{REPO}')

from controllably import Helper
Helper.get_ports()

try:
    library = Helper.read_yaml(f'{ROOT}{REPO}\\library\\catalogue.yaml')
    """File reference for layout and config files"""
except FileNotFoundError:
    print('Catalogue file not found')
    library = dict()
try:
    Helper.update_root_directory(library, REPO)
except AttributeError:
    print('Error with handling catalogue file')