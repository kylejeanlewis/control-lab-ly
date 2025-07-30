# SiLA2 communications
Here, we document how to create SiLA servers, following the instructions 
documented on [SiLA2's documentation page](https://sila2.gitlab.io/sila_python/content/server/index.html)

## A. Install dependencies
Install the Python implementation of the SiLA2 standard and the cryptography library for secure communications.
```shell
$ python -m pip install sila[codegen] cryptography
```

## B. Install this repository as an editable package
```shell
$ python -m pip install -e . --config-settings editable_mode=strict
```

## C. Create SiLA package
```python
import importlib
from pathlib import Path

from controllably.examples.sila.factory import create_setup_sila_package
s
ROOT = Path('.')                # Root of repository
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
```
Refer to [details below](#details-on-package-creation) for further information.

## D. Start Server
```python
import atexit
import subprocess
import sys

process = subprocess.Popen([
    sys.executable, '-m', f'{SETUP_NAME}_sila',
    '--ip-address', '127.0.0.1',
    '--port', '50052',
    '--ca-export-file', str(ROOT/'ca.pem'),
    # '--insecure',
], stdout=open('stdout.log', 'a'), stderr=open('stderr.log', 'a'))

atexit.register(process.wait)  # Ensure we wait for the process to terminate
atexit.register(process.terminate)  # Ensure the process is terminated on exit
```

## E. Connect Client
```python
import importlib
from controllably.core.position import Position

# Import the Client class
Client = importlib.import_module(f'{SETUP_NAME}_sila').Client
# Equivalent to:
# >>> from claw_machine_sila import Client

client = Client(
    '127.0.0.1', 50052,
    root_certs = open(ROOT/'ca.pem', 'rb').read(),
    # insecure = True,
)
```

## Details on package creation
### C1) Creates XML templates from objects in the setup
```python
from pathlib import Path
from controllably.examples.sila.factory import create_xml

xml_paths: dict[tuple[str,str], Path] = {}
for name, value in setup.__dict__.items():
    xml_path = create_xml(value, output_directory/'xml')
    class_name: str = value.__class__.__name__
    xml_paths[(class_name,name)] = xml_path
```
Todo:
1) Remove any unnecessary commands and properties.
2) Verify the data types, replacing the "Any" fields as needed.
3) Fill in the "DESCRIPTION" fields in the XML file.

### C2) Generate a SiLA2 package from the setup
```python
import subprocess 
subprocess.run([
    'sila2-codegen', 
    'new-package',
    '--package-name', f'{SETUP_NAME}_sila',
    '--output-directory', str(ROOT/'sila'/SETUP_NAME),
    *[str(path) for path in xml_paths.values()]
], check=True, capture_output=True, text=True)
```

### C3) Modify the implementation files and server code
```python
from controllably.examples.sila.modifier import (
    modify_server_file, 
    modify_generated_file, 
    copy_from_existing
)

modify_server_file(
    ROOT/'sila'/SETUP_NAME/f'{SETUP_NAME}_sila'/'server.py', 
    setup_name=setup_name
)

for (class_name, object_name), impl_path in impl_paths.items():
    modify_generated_file(
        impl_path,
        class_name, 
        object_name, 
        setup_name=setup_name
    )
```
Todo:
1) Check the types of inputs and outputs.
2) Remove the NotImplementedError after verifying implementation.
<!-- ###    a) copies implementations from library if available -->

### C4) Install the new SiLA2 package for setup
```python
import subprocess
import sys
subprocess.run([
    sys.executable, '-m',
    'pip', 'install', '-e',
    str(output_directory),
    '--config-settings', 'editable_mode=strict'
], check=True, capture_output=True, text=True)
```

## Universal SiLA client
https://gitlab.com/SiLA2/universal-sila-client/sila_universal_client 
