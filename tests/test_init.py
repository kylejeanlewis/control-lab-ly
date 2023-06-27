from pathlib import Path
import sys
REPO = 'control-lab-le'
ROOT = str(Path().absolute()).split(REPO)[0]
sys.path.append(f'{ROOT}{REPO}')

from controllably import Helper
Helper.get_ports()