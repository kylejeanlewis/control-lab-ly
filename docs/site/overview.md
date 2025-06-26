# Control-lab-ly
Lab Equipment Automation Package

## Description
User-friendly package that simplifies the definition and control of reconfigurable setups for high-throughput experimentation and machine learning.

## Installation
[Control-lab-ly](https://pypi.org/project/control-lab-ly/) can be found on PyPI and can be easily installed with `pip install`.
```shell
$ python -m pip install control-lab-ly[all]
```

## Quickstart
Import the desired class from the library and initialize to use.
```python
from controllably.Move.Cartesian import Gantry
mover = Gantry(...)
mover.connect()
mover.safeMoveTo((x,y,z))
```

Explore the details for each object using the `help()` function, or the `?` operator within the IPython / Jupyter Notebook environment.
```python
help(Gantry)
```

## Device support
- Make
    - (QInstruments) BioShake Orbital Shaker
    - (Arduino-based devices)
        - Multi-channel LED array
        - Multi-channel spin-coater
        - Peltier device
- Measure
    - (BioLogic) via `easy-biologic` (optional)
    - (Keithley) via `PyMeasure` (optional)
    - (Sentron) SI series pH meters
    - (Arduino-based device) 
        - Precision mass balance
        - Load cell
- Move
    - (Creality) Ender-3
    - (Dobot) with `external/../dobot_api`
        - M1 Pro
        - MG400
    - (Arduino-based device) gantry robot running on GRBL
- Transfer
    - (Sartorius) rLINE® dispensing modules
    - (TriContinent) C Series syringe pumps
- View
    - (FLIR) AX8 thermal imaging camera via `pyModbusTCP` (optional)
    - (General) Web cameras with `cv2`