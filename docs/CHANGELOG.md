# Change Log

## Unreleased
*Items in development*

## 0.0.2.x
Updates in setting up configuration files. Released 24 Feb 2023.
### Added
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