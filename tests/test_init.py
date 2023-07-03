from pathlib import Path
import sys
REPO = 'control-lab-le'
ROOT = str(Path().absolute()).split(REPO)[0]
sys.path.append(f'{ROOT}{REPO}')

from controllably import Helper
Helper.get_ports()

library = Helper.read_yaml(r'C:\Users\leongcj\Desktop\Astar_git\control-lab-le\library\catalogue.yaml')
"""File reference for layout and config files"""

def update_root_directory(d: dict):
    """
    Updates relative filepaths in library with root directory

    Args:
        d (dict): library of relative filepaths
    """
    for k,v in list(d.items()):
        if isinstance(v, dict):
            update_root_directory(v)
        elif type(v) == str:
            d[k] = v.replace(REPO, ROOT.replace('\\','/')+REPO)

update_root_directory(library)