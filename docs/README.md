# Control.lab.ly
Lab Equipment Automation Package

![Tests](https://github.com/kylejeanlewis/control-lab-le/actions/workflows/tests.yml/badge.svg)

## Description
User-friendly package that enables flexible automation an reconfigurable setups for high-throughput experimentation and machine learning.

## Package Structure
1. core
2. external
3. Make
4. Measure
5. Move
6. Transfer
7. View

## Device support
- Make
  - (QInstruments) BioShake Orbital Shaker
  - (Arduino-based devices)
    - Multi-channel LED array
    - Multi-channel spin-coater
    - Peltier device
- Measure
  - (Sentron) SI series pH meters
  - (Arduino-based device) 
    - Precision mass balance
    - Load cell
- Move
  - (Creality) Ender-3
  - (Dobot) 
    - M1 Pro
    - MG400
  - (Arduino-based device) gantry robot running on GRBL
- Transfer
  - (Dobot) Gripper attachments
  - (Sartorius) rLINE® dispensing modules
  - (TriContinent) C Series syringe pumps
  - (Arduino-based device) Peristaltic pump and syringe system
- View
  - (FLIR) AX8 thermal imaging camera
  - (General) Web cameras

## Installation
Control.lab.ly can be found on PyPI and can be easily installed with `pip install`.
```shell
$ pip install control-lab-ly
```

## Basic Usage
Simple start-up guide for basic usage of the package.

### Import desired class
```python
from controllably.Move.Cartesian import Gantry
mover = Gantry(...)
mover.safeMoveTo((x,y,z))
```

### View documentation
Details for each class / module / package can be explored by using the `help` function.
```python
help(Gantry)
```

For basic usage, this is all you need to know. Check the documentation for more details on each class and function.

---
>Content below is still work in progress

---

## Advanced Usage
For more advanced uses, Control.lab.ly provides a host of tools to streamline the development of lab equipment automation. This includes setting up configuration files and adding plugin drivers.

### Import package
```python
import controllably as lab
```

Optionally, you can set the safety policy for the session. This feature allows the user to prevent collisions before each movement is made. The safety policy has to be assigned before importing any of the `Mover` objects.
```python
lab.set_safety('high')  # Notifies; Pauses for input before every move action
lab.set_safety('low')   # Notifies; Waits for countdown before every move action
lab.set_safety(None)    # Carries out movement actions without delay

# Import control-lab-ly classes only after setting the safety policy
```

### Contents
1. [Setups](#1-creating-a-new-setup)
2. [Decks](#2-managing-a-deck)
3. [Addresses](#3-managing-project-addresses)
4. [Plugins](#4-using-plugins)


### 1. Creating a new setup
Create a `/configs/MySetup` folder that holds the configuration files for the setup, which includes `config.yaml` and `layout.json`.
```python
lab.create_setup(setup_name = "MySetup")
```

#### 1.1 `config.yaml`
This file stores the configuration and calibration values for your devices.
```yaml
MyDevice:                                       # device name
  module: controllably.Move.Cartesian                     # top-level category
  class: Gantry                        # device class
  settings:
    port: COM1                                  # serial port address
    setting_A: {'tuple': [300,0,200]}           # use keys to define the type of iterable
    setting_B: {'array': [[0,1,0],[-1,0,0]]}    # only tuple and np.array supported
```
> Each device configuration starts with the device name, then the following parameters:\
> `module`: module/sub-package dotnotation\
> `class`: object class\
> `settings`: various initialisation settings\

Compound devices are similarly configured. 
```yaml
MyCompoundDevice:                         # compound device name
  module: controllably.Compound.LiquidMover
  class: LiquidMover
  settings:                               # settings for your compound device
    setting_C: True
    details:                     # nest component configuration settings here
      liquid:                      # component device name
        module: controllably.Transfer.Liquid.Pipette.Sartorius
        class: Sartorius
        settings:                         # settings for your component device
          port: COM22
          setting_D: 2                    
      mover:                     # component device name
        module: controllably.Mover.Jointed.Dobot
        class: M1Pro
        settings:                         # settings for your compound device
          ip_address: '192.0.0.1'
```
> The configuration values for the component devices are nested under the `component_config` setting of the compound device.

Lastly, you can define shortcuts (or nicknames) to quickly access the components of compound devices.
```yaml
SHORTCUTS:
  First: 'MyCompoundDevice.liquid'
  Second: 'MyCompoundDevice.mover'
```
> A different serial port address or camera index may be used by different machines for the same device.\
*See* [**Section 3**](#3-creating-a-new-project) *to find out how to manage the different addresses used by different machines.*


#### 1.2 `layout.json`
This file stores the layout configuration of your physical workspace, also known as a `Deck`.\
*See* [**Section 2**](#2-managing-a-deck) *on how to load this information into the setup.*

*Optional: if your setup does not involve moving objects around in a pre-defined workspace,  a layout configuration may not be required*
> This package uses the same Labware files as those provided by [Opentrons](https://opentrons.com/), which can be found [here](https://labware.opentrons.com/), and custom Labware files can be created [here](https://labware.opentrons.com/create/). Labware files are JSON files that specifies the external and internal dimensions of a Labware block / object.


```json
{
    "metadata": {
        "displayName": "Example Layout (sub)",
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
            "labware_file": "control-lab-le/tests/core/examples/labware_wellplate.json"
        },
        "3": {
            "name": "slotThree",
            "dimensions": [127.76,85.48,0],
            "cornerOffset": [460.5,6.5,0],
            "orientation": [0,0,0]
        }
    },
    "zones":{}
}
```
> In `cornerOffset`, the bottom-left coordinates of each slot on the deck are defined. Slots are positions where Labware blocks may be placed.

> In `slots`, the `name` of the Labware and the `labware_file` path to the JSON file containing Labware details are defined. The filepath starts with the name of the repository's base folder.\
>\
> The `exclusion_height` is the height (in mm) above the dimensions of the Labware block to steer clear from when performing movement actions. Values less than 0 means the Labware is not avoided.\
>\
> *(Note: Labware avoidance only applies to final coordinates (i.e. destination). Does not guarantee collision avoidance when using point-to-point move actions. Use* `safeMoveTo()` *instead.)*

#### 1.3 Load setup
The initialisation of the setup occurs when importing `setup` from `configs.MySetup`. With `setup`, you can access all the devices that you have defined in [**Section 1.1**](#11-configyaml).

```python
### main.py ###
# Add repository folder to sys.path
from pathlib import Path
import sys
REPO = 'MyREPO'
ROOT = str(Path().absolute()).split(REPO)[0]
sys.path.append(f'{ROOT}{REPO}')

# Import the initialised setup
from configs.MySetup import setup
setup.MyDevice
setup.First
```


### 2. Managing a deck
*Optional: if your setup does not involve moving items around in a pre-defined workspace,  a* `Deck` *may not be required*

#### 2.1 Loading a deck
To load a `Deck` from the layout file, use the `loadDeck()` function of a `Mover` object (or its subclasses).
```python
from configs.MySetup import setup, LAYOUT_FILE
setup.Mover.loadDeckFromFile(LAYOUT_FILE)
``` 
> `LAYOUT_FILE` contains the details that has been defined in `layout.json` (see [**Section 1.2**](#12-layoutjson))

#### 2.2 Loading a Labware
To load a `Labware` onto the deck, use the `loadLabware()` method of the `Deck` object.
```python
setup.Mover.deck.loadLabware(...)
``` 
> This package uses the same Labware files as those provided by [Opentrons](https://opentrons.com/), which can be found [here](https://labware.opentrons.com/), and custom Labware files can be created [here](https://labware.opentrons.com/create/). Labware files are JSON files that specifies the external and internal dimensions of a Labware block / object.


### 3. Managing project addresses
A `/configs` folder will have been created in the base folder of your project repository to store all configuration related files from which the package will read from, in [**Section 1**](#1-creating-a-new-setup). A template of `registry.yaml` has also been added to the `/configs` folder to manage the machine-specific addresses of your connected devices (e.g. serial port and camera index).
```yaml
### registry.yaml ###
'012345678901234':              # insert your machine's 15-digit ID here
    cam_index:                  # camera index of the connected imaging devices
      __cam_01__: 1             # keep the leading and trailing double underscores
      __cam_02__: 0
    port:                       # addresses of serial ports
      __MyDevice__: COM1        # keep the leading and trailing double underscores
      __MyFirstDevice__: COM22
```

> Use the `Helper.get_node()` function to get the 15-digit unique identifier of your machine\
> Use the `Helper.get_port()` function to get the serial port addresses of your connect devices

```python
lab.Helper.get_node()           # Get your machine's ID (15-digit)
lab.Helper.get_ports()          # Get the port addresses of connected devices
```

Afterwards, change the value for the serial port address in the `config.yaml` file to match the registry.
```yaml
### config.yaml ###
MyDevice:
  module: controllably.Move.Cartesian
  class: Gantry
  settings:
    port: __MyDevice__          # serial port address
```

### 4. Using plugins
*Optional: if drivers for your hardware components are already included, plugins may not be required*

User-defined plugins can be easily written and integrated into Control.lab.ly. All available classes and functions can be found in `lab.modules`.
```python
lab.guide_me()                              # Use guide to view imported objects
lab.modules.at.Make.Something.Good.MyClass  # Access the class 
```

#### 4.1 Registering a Class or Function
You can import the class and register the object using the `Factory.register()` function.
```python
from my_module import MyClass
lab.Factory.register(MyClass, "Make.Something.Good")
```

#### 4.2 Registering a Python module
Alternatively, you can automatically register all Classes and Functions in a Python module just by importing it.
> 1. Declare a `__where__` global variable to indicate where to register the module
> 2. At the end of the .py file, import and call  the `include_this_module()` function
```python
### my_module.py ###
__where__ = "Make.Something.Good"               # Where to register this module to

def MyClass:                                    # Main body of code goes here
  ...

def my_function:
  ...

from controllably import include_this_module    # Registers only the Classes and Functions
include_this_module()                           # defined above in this .py file
```

The Classes and Functions in the module will be registered when you import the module.
```python
### main.py ###
from my_module import MyClass, my_function
```
---

## Dependencies
- numpy (>=1.19.5)
- opencv-python (>=4.5.4.58)
- pandas (>=1.2.4)
- pyModbusTCP (>=0.2.0)
- pyserial (>=3.5)
- PyVISA (>=1.12.0)
- PyVISA-py (>=0.7)
- PyYAML (>=6.0)

## Contributors
[@kylejeanlewis](https://github.com/kylejeanlewis)\
[@mat-fox](https://github.com/mat-fox)\
[@Quijanove](https://github.com/Quijanove)\
[@AniketChitre](https://github.com/AniketChitre)


## How to Contribute
[Issues](https://github.com/kylejeanlewis/control-lab-le/issues) and feature requests are welcome!

## License
This project is distributed under the [MIT License](https://github.com/kylejeanlewis/control-lab-le/blob/main/LICENSE).

---