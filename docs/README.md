# Control.lab.ly
Lab Equipment Automation Package

## Description
User-friendly package that enables flexible automation an reconfigurable setups for high-throughput experimentation and machine learning.

## Dependencies
- Dash (>=2.7.1)
- Impedance (>=1.4.1)
- Imutils (>=0.5.4)
- Matplotlib (>=3.3.4)
- Nest-asyncio (>=1.5.1)
- Numpy (>=1.19.5)
- Opencv-python (>=4.5.4.58)
- Pandas (>=1.2.4)
- Plotly (>=5.3.1)
- PyModbusTCP (>=0.2.0)
- Pyserial (>=3.5)
- PySimpleGUI (>=4.60.4)
- PyVISA (>=1.12.0)
- PyYAML (>=6.0)
- Scipy (>=1.6.2)

## Device support
- Make
  - Multi-channel spin-coater \[Arduino\]
- Measure
  - (Keithley) 2450 Source Measure Unit (SMU) Instrument
  - (PiezoRobotics) Dynamic Mechanical Analyser (DMA)
  - Precision mass balance \[Arduino\]
- Move
  - (Creality) Ender-3
  - (Dobot) M1 Pro
  - (Dobot) MG400
  - Primitiv \[Arduino\]
- Transfer
  - (Sartorius) rLINE® dispensing modules
  - Peristaltic pump and syringe system \[Arduino\]
- View
  - (FLIR) AX8 thermal imaging camera - full functionality in development 
  - Web cameras \[General\]

## Installation
```shell
$ pip install control-lab-ly
```

## Usage
### Import package
```python
import controllably as lab
```

### Import desired class
```python
from controllably.Move.Cartesian import Ender
mover = Ender(...)
mover.safeMoveTo((x,y,z))
```

More details for each class / module / package can be explored by using the `help` function.

```python
help(controllably.Move)
help(Ender)
help(mover)
```

Alternatively, you can use the native `pydoc` documentation generator.

```shell
$ python -m pydoc controllably.Move
$ python -m pydoc controllably.Move.Cartesian.Ender
```

>Tip: when using Interactive Python (IPython) (e.g. Jupyter notebooks), add a exclamation mark (`!`) in front of the shell command
```python
>>> !python -m pydoc controllably
```

### Create new project
Create a `/configs` folder in the base folder of your project repository to store all configuration related files from which the package will read from.

This only has to be done once when you first set up the project folder.

```python
lab.create_configs()
```

A different address may be used by different machines for the same device. To manage the different addresses used by different machines, you first need your machine's unique identifier.

```python
# Get your machine's ID
print(lab.Helper.get_node())
```

A template of `registry.yaml` has also been added to the folder to hold the machine-specific addresses of your connected devices (i.e. COM ports).\
Populate the YAML file in the format shown below.

```yaml
### registry.yaml ###
'0123456789ABCDE':              # insert your machine's ID here (from the above step)
    cam_index:                  # camera index of the connected imaging devices
      __cam_01__: 1             # keep the leading and trailing double underscores
      __cam_02__: 0
    port:                       # addresses of serial COM ports
      __device_01__: COM3       # keep the leading and trailing double underscores
      __device_02__: COM16
```

To find the COM port address(es) of the device(s) that is/are currently connected to your machine, use

```python
lab.Helper.get_ports()
```

### Create new setup
Create a new folder for the configuration files of your new setup. 

```python
lab.create_setup(setup_name = "Setup01")
# replace "Setup01" with the desired name for your setup
```

If you had skipped the previous step of creating a project, calling `lab.create_setup` will also generate the required file structure. However, be sure to populate your machine ID and device addresses in the `registry.yaml` file.

This creates a `/Setup01` folder that holds the configuration files for the setup, which includes `config.yaml` and `layout.json`.

#### `config.yaml`
Configuration and calibration values for your devices is stored in `config.yaml`.\
Each configuration starts with the `name` of your device, then its `module`, `class`, and `settings`.

```yaml
### config.yaml ###
Device01:                                         # name of simple device (user-defined)
  module: __module_name_01__                      # device module
  class: __submodule_1A__.__class_1A__            # device class
  settings:
    port: __device_01__                           # port addresses defined in registry.yaml
    __setting_A__: {'tuple': [300,0,200]}         # use keys to define the type of iterable
    __setting_B__: {'array': [[0,1,0],[-1,0,0]]}  # only tuple and np.array supported
```

`Compound` devices are similarly configured. The configuration values for its component devices are defined under the `component_config` setting. The structure of the configuration values for the component devices are similar to that shown above, except indented to fall under the indentation of the `component_config` setting.

```yaml
### config.yaml ###
Device02:                                     # name of 'Compound' device (user-defined)
  module: Compound                            
  class: __submodule_2A__.__class_2A__
  settings:
    __setting_C__: 1                          # other settings for your 'Compound' device
    component_config:                         # nest component configuration settings here
      Component01:                            # name of component
        module: __module_name_03__
        class: __submodule_3A__.__class_3A__
        settings:
          ip_address: '192.0.0.1'             # IP addresses do not vary between machines
      Component02: 
        module: __module_name_04__
        class: __submodule_4A__.__class_4A__
        settings:
          __setting_D__: 2                    # settings for your component device
```

Lastly, you can define shortcuts to quickly access components of `Compound` devices.
```yaml
### config.yaml ###
SHORTCUTS:
  robot_arm: myCompoundDevice.mover
  Nickname1: Device02.Component01
  Nickname2: Device02.Component02
```

#### `layout.json`
Layout configuration of your physical workspace (`Deck`) will be stored in `layout.json`. This package uses the same Labware files as those provided by [Opentrons](https://opentrons.com/), which can be found [here](https://labware.opentrons.com/), and custom Labware files can be created [here](https://labware.opentrons.com/create/). Labware files are JSON files that specifies the external and internal dimensions of a Labware block/module.

In `reference_points`, the bottom-left coordinates of each slot in the workspace are defined. Slots are positions where Labware blocks may be placed.

In `slots`, the name of each slot and the file reference for Lawbware block that occupies that slot are defined. The filepath starts with the repository's base folder name.

```json
{
  "reference_points":{
    "1": ["_x01_","_y01_","_z01_"],
    "2": ["_x02_","_y02_","_z02_"]
  },
  "slots":{
    "1": {
      "name": "Labware01",
      "filepath": "REPO/.../Labware01.json"
    },
    "2": {
      "name": "Labware02",
      "filepath": "REPO/.../Labware02.json"
    }
  }
}
```
This file is optional if your setup does not involve moving objects around in a pre-defined workspace, and hence a layout configuration may not be required.

### Load setup
The initialisation of the setup occurs during the import `SETUP` from within `configs/Setup01`.

```python
# Add repository folder to sys.path
from pathlib import Path
import sys
REPO = 'REPO'
ROOT = str(Path().absolute()).split(REPO)[0]
sys.path.append(f'{ROOT}{REPO}')

# Import the initialised setup
from configs.Setup01 import SETUP
this = SETUP
```

With `this`, you can access all the devices that you have defined in `configs.yaml`.
```python
this.myCompoundDevice
this.robot_arm
```

### Load deck
To load the `Deck` from the layout file, use the `lab.load_deck` function.
```python
from configs.Setup01 import LAYOUT_FILE
lab.load_deck(this.DeviceWithDeck, LAYOUT_FILE)
``` 

## Package Structure
1. Analyse
2. Compound
3. Control
4. Make
5. Measure
6. Move
7. Transfer
8. View

## Contributors
[@kylejeanlewis](https://github.com/kylejeanlewis)\
[@mat-fox](https://github.com/mat-fox)\
[@Quijanove](https://github.com/Quijanove)


## How to Contribute
[Issues](https://github.com/kylejeanlewis/control-lab-le/issues) and feature requests are welcome!

## License
This project is distributed under the [MIT License](https://github.com/kylejeanlewis/control-lab-le/blob/main/LICENSE).
