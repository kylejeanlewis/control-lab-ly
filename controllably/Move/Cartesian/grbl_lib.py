# %% -*- coding: utf-8 -*-
"""
This module holds the references for pipette tools from Sartorius.

Classes:

Other types:

"""
# Standard library imports
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
print(f"Import: OK <{__name__}>")

Message = namedtuple('Message', ['message','description'])
"""Message is a named tuple for a pair of message and its description"""

class AlarmCode(Enum):
    ac01 = Message('Hard Limit', 'Hard limit has been triggered. Machine position is likely lost due to sudden halt. Re-homing is highly recommended.')
    ac02 = Message('Soft Limit', 'Soft limit alarm. G-code motion target exceeds machine travel. Machine position retained. Alarm may be safely unlocked.')
    ac03 = Message('Abort during cycle', 'Reset while in motion. Machine position is likely lost due to sudden halt. Re-homing is highly recommended. May be due to issuing g-code commands that exceed the limit of the machine.')
    ac04 = Message('Probe fail', 'Probe fail. Probe is not in the expected initial state before starting probe cycle when G38.2 and G38.3 is not triggered and G38.4 and G38.5 is triggered.')
    ac05 = Message('Probe fail', 'Probe fail. Probe did not contact the workpiece within the programmed travel for G38.2 and G38.4.')
    ac06 = Message('Homing fail', 'Homing fail. The active homing cycle was reset.')
    ac07 = Message('Homing fail', 'Homing fail. Safety door was opened during homing cycle.')
    ac08 = Message('Homing fail', 'Homing fail. Pull off travel failed to clear limit switch. Try increasing pull-off setting or check wiring.')
    ac09 = Message('Homing fail', 'Homing fail. Could not find limit switch within search distances. Try increasing max travel, decreasing pull-off distance, or check wiring.')

class ErrorCode(Enum):
    er01 = Message('Expected command letter', 'G-code words consist of a letter and a value. Letter was not found.')
    er02 = Message('Bad number format', 'Missing the expected G-code word value or numeric value format is not valid.')
    er03 = Message('Invalid statement', 'Grbl "$" system command was not recognized or supported.')
    er04 = Message('Value < 0', 'Negative value received for an expected positive value.')
    er05 = Message('Setting disabled', 'Homing cycle failure. Homing is not enabled via settings.')
    er06 = Message('Value < 3 μsec', 'Minimum step pulse time must be greater than 3μsec.')
    er07 = Message('EEPROM read fail. Using defaults', 'An EEPROM read failed. Auto-restoring affected EEPROM to default values.')
    er08 = Message('Not idle', 'Grbl "$" command cannot be used unless Grbl is IDLE. Ensures smooth operation during a job.')
    er09 = Message('G-code lock', 'G-code commands are locked out during alarm or jog state.')
    er10 = Message('Homing not enabled', 'Soft limits cannot be enabled without homing also enabled.')
    er11 = Message('Line overflow', 'Max characters per line exceeded. Received command line was not executed.')
    er12 = Message('Step rate > 30kHz', 'Grbl "$" setting value cause the step rate to exceed the maximum supported.')
    er13 = Message('Check Door', 'Safety door detected as opened and door state initiated.')
    er14 = Message('Line length exceeded', 'Build info or startup line exceeded EEPROM line length limit. Line not stored.')
    er15 = Message('Travel exceeded', 'Jog target exceeds machine travel. Jog command has been ignored.')
    er16 = Message('Invalid jog command', 'Jog command has no "=" or contains prohibited g-code.')
    er17 = Message('Setting disabled', 'Laser mode requires PWM output.')
    er20 = Message('Unsupported command', 'Unsupported or invalid g-code command found in block.')
    er21 = Message('Modal group violation', 'More than one g-code command from same modal group found in block.')
    er22 = Message('Undefined feed rate', 'Feed rate has not yet been set or is undefined.')
    er23 = Message('Invalid gcode ID:23', 'G-code command in block requires an integer value.')
    er24 = Message('Invalid gcode ID:24', 'More than one g-code command that requires axis words found in block.')
    er25 = Message('Invalid gcode ID:25', 'Repeated g-code word found in block.')
    er26 = Message('Invalid gcode ID:26', 'No axis words found in block for g-code command or current modal state which requires them.')
    er27 = Message('Invalid gcode ID:27', 'Line number value is invalid.')
    er28 = Message('Invalid gcode ID:28', 'G-code command is missing a required value word.')
    er29 = Message('Invalid gcode ID:29', 'G59.x work coordinate systems are not supported.')
    er30 = Message('Invalid gcode ID:30', '	G53 only allowed with G0 and G1 motion modes.')
    er31 = Message('Invalid gcode ID:31', 'Axis words found in block when no command or current modal state uses them.')
    er32 = Message('Invalid gcode ID:32', 'G2 and G3 arcs require at least one in-plane axis word.')
    er33 = Message('Invalid gcode ID:33', 'Motion command target is invalid.')
    er34 = Message('Invalid gcode ID:34', 'Arc radius value is invalid.')
    er35 = Message('Invalid gcode ID:35', 'G2 and G3 arcs require at least one in-plane offset word.')
    er36 = Message('Invalid gcode ID:36', 'Unused value words found in block.')
    er37 = Message('Invalid gcode ID:37', 'G43.1 dynamic tool length offset is not assigned to configured tool length axis.')
    er38 = Message('Invalid gcode ID:38', 'Tool number greater than max supported value.')

class StatusCode(Enum):
    Alarm   = "Homing enabled but homing cycle not run or error has been detected such as limit switch activated. Home or unlock to resume."
    Idle    = "Waiting for any command."
    Jog     = "Performing jog motion, no new commands until complete, except Jog commands."
    Homing  = "Performing a homing cycle, won't accept new commands until complete."
    Check   = "Check mode is enabled; all commands accepted but will only be parsed, not executed." 
    Cycle   = "Running GCode commands, all commands accepted, will go to Idle when commands are complete."
    Hold    = "Pause is in operation, resume to continue."
    Sleep   = "Sleep command has been received and executed, sometimes used at the end of a job. Reset or power cycle to continue."

