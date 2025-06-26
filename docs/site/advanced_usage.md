# Advanced Usage
Setup initialization can be greatly simplified with Control-lab-ly.

To access files / folders in the project repository as you would with an installed package, use the `init()` function to add the project directory into PATH.

```python
from controllably import init
init('project_root')

from tools import ToolSetup01
setup = ToolSetup01.setup()
setup.MoverDevice.loadDeckFromFile(ToolSetup01.LAYOUT_FILE)
```

Here, the setup is initialized and returned with just `ToolSetup01.setup()`, and the layout is loaded with the `loadDeckFromFile` method.


## Folder structure
To make full use of Control-lab-ly's features, a typical project file structure will need the `library` and `tools` folders.
```ascii
project_root/
|
├── library/
|   ├── deck/
|   |   ├── layout_board_30x30.json
|   |   └── layout_board_60x30.json
|   ├── labware/
|   |   ├── generic_96_tiprack.json
|   |   ├── generic_8_wellplate.json
|   |   └── generic_1_bin.json
|   ├── plugins/
|   |   ├── tool_part_1.py
|   |   ├── tool_part_2.py
|   |   └── mock_module.py
|   └── __init__.py
|
├── tools/
|   ├── ToolSetup01/
|   |   ├── __init__.py
|   |   ├── config.yaml
|   |   └── layout.json
|   ├── ToolSetup02/
|   |   ├── __init__.py
|   |   ├── config.yaml
|   |   └── layout.json
|   ├── __init__.py
|   └── registry.yaml
|
├── scripts/
|   ├── experiment_script_1.py
|   ├── experiment_2.ipynb
|   └── ...
└── ...
```

Use `start_project_here(target_dir)` to generate the above file structure,
```python
from controllably import start_project_here
controllably.start_project_here(".")
```

or the CLI to create the required directories.
```shell
$ python -m controllably .
```


## 1. Features
For more advanced uses, Control-lab-ly provides a host of tools to streamline the development of lab equipment automation. This includes setting up configuration files and writing plugins.

1. [Dynamic object initialization](#11-dynamic-object-initialization)
2. [Reconfigurable complex tools](#12-reconfigurable-complex-tools)
3. [Modular positioning system](#13-modular-positioning-system)
4. [Application and network interoperability](#14-application-and-network-interoperability)


### 1.1 Dynamic object initialization
Control-lab-ly allows users to store all their tool configuration data in a YAML file, providing a single source of truth for all projects using the same set up. The `config.yaml` file stores the configuration for all the tools in the set up, which can be parsed by Control-lab-ly to initialize the tools using `get_setup()`.
```yaml title="config.yaml"
MyDevice:                                   # user-defined name
  module: controllably.Move.Cartesian       # "from" ...
  class: Gantry                             # "import" ...
  settings:
    port: COM1                              # serial port address
    setting_A: [300,0,200]
    setting_B: [[0,1,0],[-1,0,0]]
```

!!! tip

    A different serial port address or camera index may be used by different machines for the same device. See [**Section 2.1**](#21-managing-hardware-addresses) to find out how to manage the different addresses used by different machines.


### 1.2 Reconfigurable complex tools
Compound devices are similarly configured in the `config.yaml` file. The configuration details of the component tools are nested in `details`.
```yaml title="config.yaml"
MyCompoundDevice:                           # user-defined name
  module: controllably.Compound.LiquidMover
  class: LiquidMover
  settings:                                 # settings for compound device
    speed_factor_lateral: null
    speed_factor_up: 0.2
    speed_factor_down: 0.2
    speed_factor_pick_tip: 0.01
    tip_approach_distance: 20
    details:                                # nest component configuration in "details"
      mover:                                # component name (defined in LiquidMover)
        module: controllably.Move.Cartesian
        class: Gantry
        settings:
          port: COM1 
      liquid:                               # component name (defined in LiquidMover)
        module: controllably.Transfer.Liquid.Pipette.Sartorius
        class: Sartorius
        settings:
          port: COM22
```

Lastly, you can define shortcuts (or aliases) at the end of `config.yaml` to easily access the nested components of compound devices.
```yaml title="config.yaml"
SHORTCUTS:
  LiquidDevice: 'MyCompoundDevice.liquid'
  MoverDevice: 'MyCompoundDevice.mover'
```


### 1.3 Modular positioning system
Control-lab-ly allows users to easily combine multiple modules and switch between local and global coordinates. The `layout.json` file stores the layout configuration of your physical workspace (`Deck`).

!!! note

    Optional: if your setup does not involve moving objects around in a pre-defined workspace,  a layout configuration may not be required

```json title="layout.json"
{
    "metadata": {
        "displayName": "Example Layout (main)",
        "displayCategory": "deck",
        "displayVolumeUnits": "µL",
        "displayLengthUnits": "mm",
        "tags": []
    },
    "dimensions": [600,300,0],
    "cornerOffset": [0,0,0],
    "orientation": [0,0,0],
    "slots": {
        "1": {
            "name": "slotOne",
            "dimensions": [127.76,85.48,0],
            "cornerOffset": [160.5,6.5,0],
            "orientation": [0,0,0]
        },
        "2": {
            "name": "slotTwo",
            "dimensions": [127.76,85.48,0],
            "cornerOffset": [310.5,6.5,0],
            "orientation": [0,0,0],
            "labware_file": "project_root/library/labware/labware_wellplate.json"
        },
        "3": {
            "name": "slotThree",
            "dimensions": [127.76,85.48,0],
            "cornerOffset": [460.5,6.5,0],
            "orientation": [0,0,0]
        }
    },
    "zones":{
        "A":{ 
            "dimensions": [600,300,0],
            "cornerOffset": [600,600,0],
            "orientation": [-90,0,0],
            "deck_file": "project_root/library/deck/layout_sub.json",
            "entry_waypoints": [
                [653.2, 224.6, 232]
            ]
        }
    }
}
```

The size and position of the `Deck` is defined by the `dimensions`, and combination of `cornerOffset` and `orientation` respectively.

- `dimensions` is the (x,y,z) dimensions with respect to the deck's own coordinate system. 
- `cornerOffset` is the (x,y,z) coordinates of the bottom-left corner of the deck with respect to world coordinates (typically the origin). 
- `orientation` is the (rz,ry,rx) rotation of the deck about the bottom-left corner with respect to world coordinates (typically the identity rotation or zero rotation).

Within the deck, `slots` and `zones` can be defined.

- `slots` are spaces where Labware can be placed. These Labware can be individual tools or vessel holders. Indexing of slots increments numerically, typically starting from 1. 
- `zones` are regions of nested layouts. As such, a `Deck` of a smaller modular setup layout can be incorporated as part of a larger layout. Indexing of zones increments alphabetically, typically starting with 'A'.

Here, the `dimensions`, `cornerOffset`, and `orientation` definitions apply similarly, except the latter two takes reference from the parent's origin and orientation. The filename definition in `labware_file` and `deck_file` can either be absolute filepaths, or relative to the project repository. 

!!! note

    This package uses the same Labware files as those provided by [Opentrons](https://opentrons.com/), which can be found [here](https://labware.opentrons.com/), and custom Labware files can be created [here](https://labware.opentrons.com/create/). Additional fields can be added to the these Labware files to enable features such as plate stacking and collision avoidance.

    - `parameters.isStackable` is a boolean value defining if another Labware can be stacked above.
    - `slotAbove` defines a new slot above the Labware, with similar subfields `slotAbove.name`, `slotAbove.dimensions`, `slotAbove.cornerOffset`, and `slotAbove.orientation`.
    - `exclusionBuffer` is the offset from the lower and upper bounds of the Labware bounding box. (i.e. `[ [left, front, bottom], [right, back, top] ]`)

!!! warning

    Avoidance checks only apply to destination coordinates. **Does not** guarantee collision avoidance along intermediate path coordinates when using point-to-point move actions such as `move`, `moveBy` or `moveTo`. Use `safeMoveTo` instead.

For zones, `entry_waypoints` lists a sequence of coordinates that defines a safe path a translation tool can take to transit into that particular zone.


### 1.4 Application and network interoperability
To allow control of the setups over the network, or with other applications, Control-lab-ly provides a way to access the attributes and methods over a communication layer. A `Controller` encodes and decodes requests and responses using an `Interpreter`, serializing the data to be sent.
```python
from controllably.core.control import Controller
from controllably.core.interpreter import JSONInterpreter

# 'model' controllers receives requests, triggers execution in registered objects, 
# and transmits the resultant data
worker = Controller(role='model', interpreter=JSONInterpreter())
worker.setAddress('WORKER')

# 'view' controllers transmits requests and receives the resultant data
user = Controller(role='view', interpreter=JSONInterpreter())
user.setAddress('USER')
```

Each controller subscribes to one or more callbacks that will be called when the controller transmits. In this example, when `user` tries to transmit a request to target controller (`'WORKER'`), it will call `worker.receiveRequest`. Likewise, when `worker` tries to transmit data back to the request originator (`'USER'`), it will call `user.receiveData`.
```python
# request flow: USER -> WORKER
user.subscribe(callback=worker.receiveRequest, callback_type='request', address='WORKER')
# data flow: USER -> WORKER
worker.subscribe(callback=user.receiveData, callback_type='data', address='USER')
```

A hub-and-spoke network can also be achieved using a new 'relay' controller.
```python
# 'relay' controllers bridges communication between `model` and `view` controllers
hub = Controller(role='relay', interpreter=JSONInterpreter())
hub.setAddress('HUB')

# request flow: USER -> HUB -> WORKER
user.subscribe(callback=hub.relayRequest, callback_type='request', address='HUB', relay=True)
hub.subscribe(callback=worker.receiveRequest, callback_type='request', address='WORKER')

# data flow: WORKER -> HUB -> USER
worker.subscribe(callback=hub.relayData, callback_type='data', address='HUB', relay=True)
hub.subscribe(callback=user.receiveData, callback_type='data', address='USER')
```

These callbacks should be replaced with user implementation of communication layers, (e.g. socket communication or FastAPI).


## 2. Additional features
### 2.1 Managing hardware addresses
Hardware addresses may vary from machine to machine, especially for serial ports and cameras. To keep track of all the different port addresses, the machine ID and its corresponding port addresses are stored in `registry.yaml`

In the `tools` folder, a template of `registry.yaml` has been added to manage the machine-specific addresses of your connected devices (e.g. serial port and camera index). First, use the `get_node` and `get_ports` functions to identify your machine's ID and the serial port addresses of your tools.
```python
from controllably.core.connection import get_node, get_ports
get_node()           # Get the unique identifier of your machine
get_ports()          # Get a list of serial port addresses of your connect devices
```

Next, populate the `registry.yaml` file with the relevant information.
```yaml title="registry.yaml"
'012345678901234':              # insert your machine's unique identifier
    cam_index:                  # camera index of the connected imaging devices
      __cam_01__: 1             # NOTE: retain leading and trailing double underscores
    port:                       # addresses of serial ports
      __MyDevice__: COM1        # NOTE: retain leading and trailing double underscores
```

Lastly, change the value for the serial port address in the `config.yaml` file(s) to match the registry.
```yaml title="config.yaml"
MyDevice:                                   # user-defined name
  module: controllably.Move.Cartesian       # "from" ...
  class: Gantry                             # "import" ...
  settings:
    port: __MyDevice__                      # serial port address
    setting_A: [300,0,200]
    setting_B: [[0,1,0],[-1,0,0]]
```

### 2.2 Linting and coding assists
To help with development, linters such as Pylance provide suggestions while coding, based on the types of the objects. To make use of this feature, furnish the `__init__.py` file with the corresponding tool names and classes from the `config.yaml` file.
```python title="__init__.py"
from dataclasses import dataclass
...

# ========== Optional (for typing) ========== #
from controllably.Compound.LiquidMover import LiquidMover
from controllably.Transfer.Liquid.Pipette.Sartorius import Sartorius
from controllably.Move.Cartesian import Gantry

@dataclass
class Platform:
    MyCompoundDevice: LiquidMover
    LiquidDevice: Sartorius
    MoverDevice: Gantry
# ========================================== #

...
```
---
> More additional features to be documented...

---
