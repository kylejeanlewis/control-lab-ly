# Change Log

## Version 2.1.0
Fix bugs and updated with new features, including convenience functions for working with SiLA. First released 29 Sep 2025.
### Added
- [core.device] added `AnyDevice` and `WebsocketDevice`
- [core.factory] added functionality to `load_parts()` to reference parts defined in separate YAML file using `config_file` and `config_name` fields
- [core.notification] added parameter to define the decoder function; defaults to `base64.b64decode()`
- [core.position] added `convert_to_position()` into `Position.fromArray()`
- [examples.sila] added functions to create new SiLA packges, resolve annotation types, and modify implementation code for the generated package
- added new tests, tutorial files and code
### Changed
- [Transfer.Liquid.Pipette.Sartorius] update how the model name is parsed
- [core.connection] update `get_addresses()` to cover both MAC address and non Mac address references
- [core.control] update the priority counter of `TwoTierQueue`
- [core.factory] update `get_setup()` to disconnect devices upon setup failure
- [core.safety] updated module to support dynamic changing of safety levels
- [examples.gui.tkinter.gui] bug fix
- updated tests, documentation, and type hints
### Removed
- removed unused and outdated script files in `scripts/`


## Version 2.0.0
Major overhaul and package rebuilt from the ground. First released 27 Jun 2025.
### Added
- added `tests/` written with pytest
- added test execution with tox
- added documentation building with Mkdocs
- added documentation hosting with ReadTheDocs
- added proper logging facility with Python `logging` module
- [core] new core modules and features added
  - [control] added `TwoTierQueue` for queuing both priority and normal jobs; new `Controller` to relay data over a communication gap (either application-wise or network-wise) to enable remote calls; new `Proxy` to mimic object behavior that is on the other end of a Controller-Controller bridge 
  - [datalogger] functions to trigger data streaming and recording, conversion of data sequence to Pandas dataframe, and live plotting of data
  - [device] base classes for tools of different connection modes (e.g. serial, socket)
  - [file_handler] added function to zip files, and add repository to sys.path
  - [interpreter] added interpreters to serialize data for transfer over network (i.e. `JSONInterpreter`)
  - [log_filters] added logging filters to selectively toggle the verbosity of individual objects
  - [notification] added notifiers to send large data/files (i.e. `EmailNotifier`)
  - [position] added `Position` class, consisting of a `numpy.ndarray` for 3D coordinates and a `scipy.spatial.transform.Rotation` for 3D rotation for better description of positioning in 3D space; added `Slot` that defines the available space on `Deck` for `Labware` to be placed on; `BoundingVolume` and `BoundingBox` to describe an envelope of space to avoid or stay within
- [Make.Heat] added new `HeaterMixin` to augment objects with temperature control related methods
- [Make.Mixture] added new class for magnetic stirrer `TwoMag`
- [Measure.Electrical.BioLogic] added `BioLogic` via `easy-biologic` library
- [Move] added a generic `GCode` that can use different variants of G-code (i.e. GRBL, Marlin)
- [Transfer.Liquid.Pipette.Sartorius] added separate API module/class for direct implementation from manual
- [View] added placeholder image as bytestring in .py file
- [View] added `Camera.processImage()` method to allow user to define custom image processing callbacks, including detection algorithms
- [external] added sub-package to contain required libraries written by external parties that are not installable through PyPI; credits documented in `docs/ATTRIBUTIONS.md`
- [examples.control] added example implementations for `Controller` communication layers using FastAPI and sockets
- [examples.gui] GUI example implementation in tkinter with only implementations for translation, liquid transfer, and vision
- [example.sila] added XML generator for SiLA2 configuration files; refer to SiLA2 documentation for full usage of SiLA; Control-lab-ly simplifies the implementation definition step in using SiLA
### Changed
- consolidated packaging to single `pyproject.toml` file
- move all `requirements_*.txt` files to `dev/`
- change minimum Python version to 3.10 from 3.8
- changed to `core` from `misc` sub-package to better reflect how these modules in `core` underpin the functionalities of Control-lab-ly
- [core] clearer separation of scope in `core` modules
  - [compound] new complex tool definitions described below, containing `Compound`, `Combined`, `Ensemble`, and `Multichannel`
  - [connection] functions relating to getting the IP, port, and machine addresses
  - [factory] functions to procedurally parse config files, retrieve object classes, initialize objects, and returning tool setups in preferred form (e.g. dict, namedtuple, NameSpace, dataclass)
  - [file_handler] functions relating to file and folder creation, path resolution, and reading files
  - [logging] makes use of Python native `logging` module to log messages from package
  - [position] classes that define location (e.g. `Well`, `Labware`, `Deck`)
  - [safety] unchanged
- [core.compound] updated paradigm of how complex tools are defined, with `Compound` for multiple connections, dissimilar parts; `Ensemble` for multiple connections, similar parts; `Combined` for single connection, dissimilar parts (or use mixins); `Multichannel` for single connection, similar parts
  - example implementation (using`Compound` and mixins) can be found in `Compound` sub-package, and (using `Ensemble` and `Multichannel`) in `Transfer.Liquid.Pump.TriContinent.tricontinent`
- [core.device] all equipment API that does read/write actions inherits from these device classes that provide methods for parsing, connecting, read/write actions, streaming; takes in user-defined templates for read/write parsing
- [Make.Light] uses `threading.Timer` for timing actions (via `core.device.TimedDeviceMixin`), instead of running a separate thread to count time
- [Measure.Electrical.Keithley] updated code to leverage `PyMeasure` library
- [Move] support for GRBL and Marlin separated into their respective APIs, and brought up to top level of `Move`, as G-code can also be used for jointed robots
- [Move.Jointed.Dobot] moved dobot API into `external` sub-module (see above in the 'Added' section)
- [Transfer.Liquid] reorganized tools based on type (i.e. Pump, Pipette), then brands
- [Transfer.Substrate] generalized `GripperMixin` that can be used with any translation robot, instead of just Dobot attachments
### Removed
- removed `GUI` as a top-level sub-package; downgraded to an example implementation using tkinter (see above in 'Added' section)
- removed reference guide GUI window in favor of a proper documentation site (i.e. GitHub Pages, ReadTheDocs)
- [core.factory] removed registration of imported modules to keep track of modules
- [Measure] simplify inheritance structure by removing `Programmable` class
- [Measure.Electrical] removed Keithley programs that were based on old implementation (before PyMeasure)
- [Measure.Mechanical] removed PiezoRobotics from tool list due to inactive development and use
- [Transfer.Liquid] removed implementations for "syringe" and peristaltic pump due lack of use
- [Transfer.Powder] removed due to lack of use
- [Transfer.Substrate.Dobot] removed Dobot specific implementations; prefer mixins instead (see above in 'Changed' section)
- [View] removed detection methods in `Camera` due to out of scope
- [View.Classifiers] removed due to out of scope


## Version 1.3.2
Feature enhancements, bug fixes and patches. First released 24 Apr 2024.
### Added
- add new `delay` parameter in `Keithley.programs.IV_Scan`
### Changed
- fix critical bug in setting sense/source limits for `KeithleyDevice`
- fix bugs in `KeithleyDevice`, `Peltier`, `ForceSensor`


## Version 1.3.1
Feature enhancements, bug fixes and patches. First released 11 Apr 2024.
### Added
- implementation of `TriContinent.pullback()`
- new `Well` properties and option in return list of wells by rows instead of columns
### Changed
- fix bugs in `Peltier` (`setTemperature()` and `getTemperature()`)
- fix bugs in `Ender` (`setTemperature()` and `getTemperature()`)
- fix bug in `Keithley.setFunction()`
- generalise `IV_Scan` to take either currents or voltages


## Version 1.3.0
Feature enhancements, bug fixes and patches. First released 19 Feb 2024.
### Added
- added check for poor physical connection with `PiezoRoboticsDevice`
- Keithley
  - added new subclasses of `KeithleyDevice`: `DAQ6510` and `SMU2450`
  - added way to read and save model name of `KeithleyDevice`
  - added new Keithley program for DAQ to scan multiple channels
  - new methods `clearErrors()`, `setDisplay()`, `setFunction()`
### Changed
- changed the way travel times are calculated for `Mover` tools, so that they reflect the actual physical travel times more accurately
- changed ability to delay initialisation of TriContinent pumps until it is in a more convenient location
- fixed few bugs with `SentronProbe` tool
### Removed
- removed old archived files


## Version 1.2.0
Feature enhancements, bug fixes and patches. First released 22 Aug 2023.
### Added
- `ForceClampSetup` class
- `LoadCell` class
- `Balance` class (subclass of `LoadCell`)
### Changed
- update `LEDArray` to delay timing loop by 0.1s
- fix bug with initialising `PiezoRoboticsDevice`
- update `getTemperature()` across multiple classes to standardise output
- `Mover` class
  - speed-related attributes and properties
  - add method to calculate travel time based on target speed, acceleration and deceleration
  - modify how speeds and max speeds interact with `move()` and `safeMoveTo()`
- `Cartesian` class
  - `setSpeed()` and `setSpeedFraction()`
  - get max speed settings from device upon connecting
  - change calculation of movement wait times using device speed and acceleration
- `Primitiv` class
  - change the class name to `Grbl` and `Primitiv` as a subclass name to retain compatibility
  - overload `moveTo()` and `_query()` methods to use jogging mode
  - modify the sequence of commands to halt movement
  - implement `getAcceleration()`, `getCoordinates()`, `getMaxSpeed()`
  - clear errors and setting feed rate upon establishing connection
- `Ender` class
  - change the class name to `Marlin` and `Ender` as a subclass name to retain compatibility
  - added method to immediately stop movement
  - implement `getAcceleration()`, `getCoordinates()`, `getMaxSpeed()`
  - separate methods for `setSpeed()` (absolute speed in mm/s) and `setSpeedFraction()` (proportional speed to max speed)
- `Dobot` class
  - added `stop()` method
- Flir `AX8` class
  - added `invertPalette()` method
  - added data parsing methods `_decode_from_modbus()` and `_encode_to_modbus()`
- `KeithleyDevice()` class
  - added `ip_address` property
  - added options for `_read()` method
  - added `readline()` method
  - implement `disconnect()` method
- fix bug with Keithley programs using `device.run()` instead of `device.start()`
### Removed
- `Thermal` class
- removed dependency on `imutils` package


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
