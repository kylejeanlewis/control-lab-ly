from pathlib import Path
import sys
REPO = 'control-lab-le'
ROOT = str(Path().absolute()).split(REPO)[0]
sys.path.append(f'{ROOT}{REPO}')

# from controllably.core import connection, file_handler
# connection.get_ports()

# library = file_handler.read_config_file(f'{ROOT}{REPO}\\library\\catalogue.yaml')
# """File reference for layout and config files"""
# Helper.update_root_directory(library, REPO)