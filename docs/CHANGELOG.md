# Change Log

## Unreleased
*Items under development*
### 1.2.0
- Integration for mass balance from Sartorius

## Version 1.1.3
Bug fixes and patches. First released __ Jul 2023.
### Changed
- update `LEDArray` to delay timing loop by 0.1s
-fix bug with initialising `PiezoRoboticsDevice`


## Versions 1.1.2 & 1.1.1
Bug fixes and patches. First released 12 Jul 2023.
### Added
- import `Device` classes in init files to view documentation
- added library for GRBL status and error codes
- add `update_root_direcctory()` function to Helper
### Changed
- fix bug with adding new rows into Dataframes
- use `reset_input_buffer()` instead of `flushInput()` for `pyserial.Serial` objects
- print the actual string sent to Serial devices
- update methods in `Deck`, `Labware`, and `Well` to camelCase
- update `Deck.isExcluded()` to apply strict inequalities when determining out-of-range coordinates
- update `LiquidMover` to insert a portion of tip into rack before ejecting
- update `Spinner`
  - fix bug with sending commands
  - added `_query()` method
  - pass verbosity to individual spinners
- verbosity of `Measure` objects pass through to devices
- update `PiezoRoboticsDevice`
  - initialize upon connection
  - raise errors when encountering them
- update `Mover`
  - modify`setFlag()` to print kwargs instead of raising error if assigned values are not boolean
  - use `safe_height` (if defined) instead of z-coordinate of home in `safeMoveTo()`
  - added `getSettings()` method
- update `Gantry` class
  - read multiple flines in `_query()`
  - check that commands end with newline before sending to device
  - fix bug with changing speeds
- update `Ender`
  - added `getTemperature()`, `holdTemperature()`, `isAtTemperature()` methods
  - modified `setTemperature()` to use Marlin code to wait for temperature
- update `Primitiv` class
  - add `getStatus()` and `stop()` methods
  - add `_get_settings()` method
- fix bug in `M1Pro.setHandedness()`
- update `Sartorius` class
  - `tip_inset_mm` now an instance attribute with initialisation parameters
  - set `tip_on` flag to False when performing `eject()`


## Version 1.1.0
Bug fixes and feature enhancements. First released 15 Jun 2023.
### Added
- `ForceSensor` - DIY force sensor (#55)
- `BioShake` - orbital shaker from QInstruments (#56)
- `SentronProbe` - pH meter probe from Sentron (#75)
- `Maker`
  - added `execute()` abstract method and implemented in subclasses
- GUI
  - `Guide` - documentation guide
  - `MakerPanel` - daptive GUI controls for `Maker` objects (#87)
### Changed
- `M1Pro`
  - fix issue with changing handedness (#86)
- `Peltier`
  - rename `getTemperatures()` to `getTemperature()`
  - rename `isReady()` to `isAtTemperature()`
  - rename `set_point` to `set_temperature`
- `Ender`
  - rename `set_point` to `set_temperature`
- `TriContinent`
  - rename `step_limit` to `limits`
- Refactor and reorganize `GUI` code
- Refactor code in `helper` and `factory`
- Updated documentation
### Removed
- `Analyse` sub-package removed
- `Control.Schedule` sub-package removed
- Unnecessary commented-out blocks of code


## Version 1.0.1
Bug fixes and minor feature enhancements. First released 08 May 2023.
### Added
- `LiquidMover`
  - Added `LiquidMover.touchTip()` method to touch the pipette tip against the walls of the vessel to remove excess liquid on the outside of the tip (#62)
  - Added option to indicate the position of the first available pipette tip in `LiquidMover` (#61)
- Added adaptive GUI controls for `Liquid` objects (#70)
- Added option to indicate which digital IO channel to use with Dobot attachments (#53)
### Changed
- `MassBalance`
  - Updated to the use `pd.concat()` instead of `pd.DataFrame.append()`, which is going ot be deprecated (#63)
  - Fixed endless loop for when `MassBalance` tries to `zero()` while recording data (#60)
- Changed the `Image` class and methods into functions within a module (#54)
- Fixed the tool offset of pipette when pipette tip is attached, and accounts for the length of pipette that enters the pipette tip (#64)
- Changed to using more precise time interval measurements by moving from `time.time()` to `time.perf_counter()` (#68)
- Fixed discrepancy in aspirate and dispense speed for `Sartorius` (#73) and let speed return to a global default value (#72)
- Updated documentation


## Version 1.0.0
Major overhaul in package structure. Standardisation of methods and consolidation of common methods. First released 12 Apr 2023.
### Added
- Usage of Abstract Base Classes (ABCs) to define a base class with abstract methods that needs to be implemented through sub-classing (#31)
- Usage of Protocols to provide an interface between different classes of objects (#30)
- Usage of Dataclasses to store complex data 
- Usage of decorators to modify methods
- Introduced different functions to parse the program docstring and find program parameters
### Changed
- Standardised methods and consolidated common methods
- Added type hints (#28)
- Moved Dobot attachments from Mover to Transfer.Substrate
- Split GUI Panels into individual files
- Split Dobot arms into individual files
- Split functions/methods in `misc.py` into individual files.
- Changed `_flags` to a public attribute `flags`
- Update documentation (#27, #28, #29)
### Removed
- Unnecessary commented-out blocks of code


## Version 0.0.x
(0.0.4.x) Introduced control for Peltier device and TriContinent Series C syringe pumps. First released 10 Mar 2023.\
(0.0.3.x) Minor changes to movement robot safety and pipette control. Introduced control for LED array. First released 08 Mar 2023.\
(0.0.2.x) Updates in setting up configuration files. First released 24 Feb 2023.\
(0.0.1.x) First release of [Control.lab.ly](https://pypi.org/project/control-lab-ly/) distributed on 23 Feb 2023.\
(0.0.0.x) Pre-release packaging checks
### Added
#### 0.0.4
- Added control for `Peltier` (#23)
  - set and get temperatures
  - hold temperatures for desired duration
  - checks if target temperature has been reached by checking power level lower than a threshold or time passed over a predefined duration, once the temperature is within tolerance
  - ability to record temperatures and timestamps 
- Added control for `TriContinent` and `TriContinentEnsemble` (#25)
  - single actions such as `empty`, `fill`, `initialise`, move actions, set speeds and valves, and wait
  - compound actions such as `aspirate`, `dispense`, and `prime`
#### 0.0.3
- Added safety measures for movement actions (#24)
  - In `Deck`, added exclusion zones when reading the `layout.json` file and new method `is_excluded()` to check if target coordinate is within the exclusion zone
  - In `Mover`, update `isFeasible()` method to check if target coordinates violates the deck's exclusion zone
  - New function `set_safety()` defines safety modes when starting a new session to pause for input (in "high" safety setting) and to wait for safety countdown (in "low" safety setting)
- `Make.Light.LEDArray` for controlling LEDs in the photo-reactor, as well as timing the LED "on" durations (#35)
#### 0.0.2.2
- Added import of `CompoundSetup` class
#### 0.0.2
- `Deck.at()` method for directly referencing slots using either index numbers or names
- New `CompoundSetup` class for common methods of `Compound` devices
- New `load_deck()` function to load `Deck` after initialisation
#### 0.0.1
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

### Changed
#### 0.0.4
- Update documentation
#### 0.0.3.1
- Update documentation
#### 0.0.3
- `Sartorius`
  - made the blowout/home optional for the dispense method upon emptying the pipette
- Update documentation
#### 0.0.2.1
- Changed template files for `lab.create_setup()`
#### 0.0.2
- Update documentation
