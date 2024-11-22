# -*- coding: utf-8 -*-
"""This module holds the references for QInstruments firmware."""
# Standard library imports
from enum import Enum

class ELMStateCode(Enum):
    es0     = "ELM is moving"
    es1     = "ELM is locked"
    es3     = "ELM is unlocked"
    es9     = "ELM error occurred"

class ELMStateString(Enum):
    ELMUndefined    = "ELM is moving"
    ELMLocked       = "ELM is locked"
    ELMUnlocked     = "ELM is unlocked"
    ELMError        = "ELM error occurred"

class ErrorCodes_BS(Enum):
    # Shaking
    e101    = "Error by the DC motor controller"
    e102    = "Error due speed failure, for example happens through mechanical locking"
    e103    = "Errors caused by an uninitialized shaker or incorrect initialization parameters after switch on"
    e104    = "Errors caused by unsuccessful initialization routine"
    e105    = "Errors caused by not achieving the home position at  stop command"
    e106    = "Errors caused by over speed"
    # Temperature
    e201    = "Error due failed answers from temperature sensors or incorrect internal settings of temperature sensors"
    e202    = "Error due temperature communication bus system"
    e203    = "Sensor with the requested ID is not found while working"
    e204    = "Errors caused by a faulty temperature measurement while working"
    e206    = "Error caused by checksum of the internal temperature sensor"
    e207    = "Error caused by checksum of the main temperature sensor"
    e208    = "Error caused by general checksum"
    e209    = "Error caused by unknown temperature method"
    e210    = "Error caused by over heating"
    # ELM
    e300    = "General error"
    e301    = "IC-Driver error"
    e303    = "Verification error by the unlock position"
    e304    = "Error caused by unsuccessful reach the lock position (timeout)"
    e305    = "Error caused by unsuccessful reach the unlock position (timeout)"
    e306    = "Error caused by unsuccessful reach the lock position (over current)"
    e307    = "Error caused by unsuccessful reach the unlock position (over current)"
    
class ErrorCodes_Q1_CP(Enum):
    e10002  = "Instruction sent with an invalid parameter"
    e10003  = "Instruction sent with an invalid parameter"
    e100__  = "Internal firmware sequence failure"
    e2____  = "Internal MCU periphery error"
    e310__  = "EEPROM data verification failed"
    # Temperature
    e320__  = "Communication with internal temperature sensors failed"
    e33010  = "Device internal temperature too hot"
    e33020  = "Emergency shutdown of the temperature fuse has triggered"
    e33030  = "Emergency temperature sensor validation has failed"
    e34010  = "FAN-1 or FAN-2 power supply invalid"
    e34110  = "FAN-1 or FAN-2 power supply invalid"
    e34020  = "FAN-1 or FAN-2 has stalled"
    e34120  = "FAN-1 or FAN-2 has stalled"
    e34030  = "FAN-1 or FAN-2 airway clogged"
    e34130  = "FAN-1 or FAN-2 airway clogged"
    e35010  = "TEC power supply invalid"
    e35020  = "TEC power supply short circuit detected"
    e35030  = "TEC power supply open circuit detected"
    e360__  = "Internal temperature controller failure"
    # Shaking
    e37030  = "Shaker has stalled"
    e37040  = "Shaker cannot move because the solenoid does not unlock"
    e37060  = "Unable to lock Shaker in the home position"
    e37070  = '"Shaker find home position" timeout occurred'
    e370__  = "Internal shake controller failure"
    e39030  = "Solenoid motion timeout occurred"
    e390__  = "Internal solenoid controller failure"
    # ELM
    e38030  = "ELM motion timeout occurred"
    e38090  = "ELM self-test has failed"
    e380__  = "Internal ELM controller failure"

class ShakeStateCode(Enum):
    ss0     = "Running"
    ss1     = "Detected a stop command"
    ss2     = "Braking mode"
    ss3     = "Stopped and is locked at home position"
    ss4     = "Manual mode for external control"
    ss5     = "Accelerates"
    ss6     = "Decelerates"
    ss7     = "Decelerates to stop"
    ss8     = "Decelerates to stop at home position"
    ss9     = "Stopped and is not locked"
    ss10    = "State is for service purpose only"
    ss90    = "ECO mode"
    ss99    = "Boot process running"

class ShakeStateString(Enum):
    RUN             = "Running"
    STOP            = "Stopped and is locked at home position"
    ESTOP           = "Emergency Stop"
    RAMPt           = "Accelerates"
    RAMP_           = "Decelerates"
    dec_stop        = "Decelerates to stop"
    dec_stop_home   = "Decelerates to stop at home position"
    stopped         = "Stopped and is not locked"
    aligned         = "State is for service purpose only"
