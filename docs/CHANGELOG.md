# Change Log

## Unreleased
*Items under development*

## 1.0.0.x
Major overhaul in package structure. Standardisation of methods and consolidation of common methods. First released 12 Apr 2023.
### Added
#### 1.0.0
- Usage of Abstract Base Classes (ABCs) to define a base class with abstract methods that needs to be implemented through sub-classing
- Usage of Protocols to provide an interface between different classes of objects
- Usage of Dataclasses to store complex data 
- Usage of decorators to modify methods
- Introduced different functions to parse the program docstring and find program parameters
### Changed
#### 1.0.0
- Standardised methods and consolidated common methods
- Added type hints
- Moved Dobot attachments from Mover to Transfer.Substrate
- Split GUI Panels into individual files
- Split Dobot arms into individual files
- Split functions/methods in `misc.py` into individual files.
- Changed `_flags` to a public attribute `flags`
- Update documentation
### Removed
#### 1.0.0
- Unnecessary commented-out blocks of code

## 0.0.4.x
Introduced control for Peltier device and TriContinent Series C syringe pumps. First released 10 Mar 2023.
### Added
#### 0.0.4
- Added control for `Peltier`
  - set and get temperatures
  - hold temperatures for desired duration
  - checks if target temperature has been reached by checking power level lower than a threshold or time passed over a predefined duration, once the temperature is within tolerance
  - ability to record temperatures and timestamps 
- Added control for `TriContinent` and `TriContinentEnsemble`
  - single actions such as `empty`, `fill`, `initialise`, move actions, set speeds and valves, and wait
  - compound actions such as `aspirate`, `dispense`, and `prime`
### Changed
#### 0.0.4
- Update documentation

## 0.0.3.x
Minor changes to movement robot safety and pipette control. Introduced control for LED array. First released 08 Mar 2023.
### Added
#### 0.0.3
- Added safety measures for movement actions
  - In `Deck`, added exclusion zones when reading the `layout.json` file and new method `is_excluded()` to check if target coordinate is within the exclusion zone
  - In `Mover`, update `isFeasible()` method to check if target coordinates violates the deck's exclusion zone
  - New function `set_safety()` defines safety modes when starting a new session to pause for input (in "high" safety setting) and to wait for safety countdown (in "low" safety setting)
- `Make.Light.LEDArray` for controlling LEDs in the photo-reactor, as well as timing the LED "on" durations
### Changed
#### 0.0.3.1
- Update documentation
#### 0.0.3
- `Sartorius`
  - made the blowout/home optional for the dispense method upon emptying the pipette
- Update documentation

## 0.0.2.x
Updates in setting up configuration files. First released 24 Feb 2023.
### Added
#### 0.0.2.2
- Added import of `CompoundSetup` class
#### 0.0.2
- `Deck.at()` method for directly referencing slots using either index numbers or names
- New `CompoundSetup` class for common methods of `Compound` devices
- New `load_deck()` function to load `Deck` after initialisation
### Changed
#### 0.0.2.1
- Changed template files for `lab.create_setup()`
#### 0.0.2
- Update documentation

## 0.0.1.x
First release of [Control.lab.ly](https://pypi.org/project/control-lab-ly/) distributed on 23 Feb 2023.
### Added
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
- misc
  - Helper class for most common actions
  - create_configs: make new directory for configuration files
  - create_setup: make new directory for specific setup-related files
  - load_setup: initialise setup on import during runtime

## 0.0.0.x
Pre-release packaging checks