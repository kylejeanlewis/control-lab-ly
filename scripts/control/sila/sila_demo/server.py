import atexit
from pathlib import Path
import subprocess
import sys

from controllably.core.connection import get_host
from controllably.core.file_handler import create_folder

SETUP_NAME = 'claw_machine'
HOST = get_host()
PORT = 50052

folder_name = create_folder('logs')
process = subprocess.Popen([
    sys.executable, '-m', f'{SETUP_NAME}_sila',
    '--ip-address', HOST,
    '--port', str(PORT),
    # '--insecure',
    '--ca-export-file', str(Path(__file__).parent/'ca.pem'),
], stdout=open(f'{folder_name}/stdout.log', 'a'), stderr=open(f'{folder_name}/stderr.log', 'a'))

atexit.register(process.wait)  # Ensure we wait for the process to terminate
atexit.register(process.terminate)  # Ensure the process is terminated on exit