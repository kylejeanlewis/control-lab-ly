# %% -*- coding: utf-8 -*-
"""This module holds the references for GRBL firmware."""
# Standard library imports
from collections import namedtuple
from enum import Enum

Message = namedtuple('Message', ['message','description'])
"""Message is a named tuple for a pair of message and its description"""

class Alarm(Enum):
    ac01 = Message('Hard Limit', 'Hard limit has been triggered. Machine position is likely lost due to sudden halt. Re-homing is highly recommended.')
    ac02 = Message('Soft Limit', 'Soft limit alarm. G-code motion target exceeds machine travel. Machine position retained. Alarm may be safely unlocked.')
    ac03 = Message('Abort during cycle', 'Reset while in motion. Machine position is likely lost due to sudden halt. Re-homing is highly recommended. May be due to issuing g-code commands that exceed the limit of the machine.')
    ac04 = Message('Probe fail', 'Probe fail. Probe is not in the expected initial state before starting probe cycle when G38.2 and G38.3 is not triggered and G38.4 and G38.5 is triggered.')
    ac05 = Message('Probe fail', 'Probe fail. Probe did not contact the workpiece within the programmed travel for G38.2 and G38.4.')
    ac06 = Message('Homing fail', 'Homing fail. The active homing cycle was reset.')
    ac07 = Message('Homing fail', 'Homing fail. Safety door was opened during homing cycle.')
    ac08 = Message('Homing fail', 'Homing fail. Pull off travel failed to clear limit switch. Try increasing pull-off setting or check wiring.')
    ac09 = Message('Homing fail', 'Homing fail. Could not find limit switch within search distances. Try increasing max travel, decreasing pull-off distance, or check wiring.')

class Error(Enum):
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
    er30 = Message('Invalid gcode ID:30', 'G53 only allowed with G0 and G1 motion modes.')
    er31 = Message('Invalid gcode ID:31', 'Axis words found in block when no command or current modal state uses them.')
    er32 = Message('Invalid gcode ID:32', 'G2 and G3 arcs require at least one in-plane axis word.')
    er33 = Message('Invalid gcode ID:33', 'Motion command target is invalid.')
    er34 = Message('Invalid gcode ID:34', 'Arc radius value is invalid.')
    er35 = Message('Invalid gcode ID:35', 'G2 and G3 arcs require at least one in-plane offset word.')
    er36 = Message('Invalid gcode ID:36', 'Unused value words found in block.')
    er37 = Message('Invalid gcode ID:37', 'G43.1 dynamic tool length offset is not assigned to configured tool length axis.')
    er38 = Message('Invalid gcode ID:38', 'Tool number greater than max supported value.')

class Setting(Enum):
    sc0     = Message('Step Pulse Length (us)', 'Length of the step pulse delivered to the stepper motors.')
    sc1     = Message('Step Idle Delay (ms)', 'Time delay in milliseconds that GRBL will power the stepper motors after a motion command is complete.')
    sc2     = Message('Step Pulse Configuration', 'Step signal sent to the stepper motor drivers. Configuration codes are the decimal representation of the binary values of whether to reverse Z,Y,X axes (e.g. reverse Y and X: DEC(011) = 3)')
    sc3     = Message('Axis Direction', 'Change axis motion direction without changing wiring. See Setting Code 2.')
    sc4     = Message('Step Enable Invert', 'Controls the signal sent to the enable pin of stepper drivers')
    sc5     = Message('Limit Pins Invert', '')
    sc6     = Message('Probe Pin Invert', '')
    sc10    = Message('Status Report', 'Real time data sent to the user.')
    sc11    = Message('Junction Deviation (mm)', 'Proxy for cornering speed.')
    sc12    = Message('Arc Tolerance', 'Defines how smooth the curves will be.')
    sc13    = Message('Feedback Units', 'Set position feedback units: 0 for mm, 1 for inches')
    sc20    = Message('Soft Limits', 'Requires "Homing" to be enabled.')
    sc21    = Message('Hard Limits', 'Requires limit switches to be installed.')
    sc22    = Message('Homing Cycle', 'Requires limit switches to be installed.')
    sc23    = Message('Homing Cycle Direction', 'Allows change of direction of homing cycle.')
    sc24    = Message('Homing Feed (mm/min)', 'Feed rate used in the "Homing" cycle once the limit switches are located.')
    sc25    = Message('Homing Seek (mm/min)', 'Feed rate used in the "Homing" cycle to locate the limit switches.')
    sc26    = Message('Homing Debounce (ms)', 'Length of the software delay in milliseconds that minimizes switch noise.')
    sc27    = Message('Homing Pull-off (mm)', 'How far to move away from the limit switches after finding the "Home" position.')
    sc30    = Message('Maximum spindle speed (rpm)', '')
    sc31    = Message('Minimum spindle speed (rpm)', '')
    sc32    = Message('Laser-mode enable (bool)', '')
    sc100   = Message('X (steps/mm)', 'Tells GRBL how many steps are required to move 1mm in X-axis.')
    sc101   = Message('Y (steps/mm)', 'Tells GRBL how many steps are required to move 1mm in Y-axis.')
    sc102   = Message('Z (steps/mm)', 'Tells GRBL how many steps are required to move 1mm in Z-axis.')
    sc110   = Message('X - Max Rate (mm/min)', 'Maximum speed for X-axis.')
    sc111   = Message('Y - Max Rate (mm/min)', 'Maximum speed for Y-axis.')
    sc112   = Message('Z - Max Rate (mm/min)', 'Maximum speed for Z-axis.')
    sc120   = Message('X - Max Acceleration (mm/s^2)', 'Maximum acceleration for X-axis.')
    sc121   = Message('Y - Max Acceleration (mm/s^2)', 'Maximum acceleration for Y-axis.')
    sc122   = Message('Z - Max Acceleration (mm/s^2)', 'Maximum acceleration for Z-axis.')
    sc130   = Message('X - Max Travel (mm)', 'Used when soft limits are enabled to tell GRBL the maximum travel for X-axis.')
    sc131   = Message('Y - Max Travel (mm)', 'Used when soft limits are enabled to tell GRBL the maximum travel for Y-axis.')
    sc132   = Message('Z - Max Travel (mm)', 'Used when soft limits are enabled to tell GRBL the maximum travel for Z-axis.')

class Status(Enum):
    Alarm   = "Homing enabled but homing cycle not run or error has been detected such as limit switch activated. Home or unlock to resume."
    Idle    = "Waiting for any command."
    Jog     = "Performing jog motion, no new commands until complete, except Jog commands."
    Home    = "Performing a homing cycle, won't accept new commands until complete."
    Check   = "Check mode is enabled; all commands accepted but will only be parsed, not executed." 
    Run     = "Running GCode commands, all commands accepted, will go to Idle when commands are complete."
    Hold    = "Pause is in operation, resume to continue."
    Sleep   = "Sleep command has been received and executed, sometimes used at the end of a job. Reset or power cycle to continue."
    Door    = "Door related state. Check Door state and Door state initiated."
