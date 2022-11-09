# %% -*- coding: utf-8 -*-
"""
Adapted from @jaycecheng spinutils

Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import time

# Third party imports
import serial # pip install pyserial

# Local application imports
from . import LiquidHandler
print(f"Import: OK <{__name__}>")

CALIB_ASPIRATE = 27
CALIB_DISPENSE = 23.5
DEFAULT_SPEED = 3000
PRIMING_TIME = 2
WETTING_CYCLES = 1

class Pump(object):
    def __init__(self, port, verbose=False):
        self.mcu = None
        self.flags = {
            'busy': False
        }
        
        self.verbose = verbose
        self._port = None
        self._baudrate = None
        self._timeout = None
        
        self._connect(port)
        pass
    
    def _connect(self, port):
        self._port = port
        self._baudrate = 9600
        self._timeout = 1
        mcu = None
        try:
            mcu = serial.Serial(port, 9600, timeout=1)
            time.sleep(2)   # Wait for grbl to initialize
            mcu.flushInput()
            print(f"Connection opened to {port}")
        except Exception as e:
            if self.verbose:
                print(f"Could not connect to {port}")
                print(e)
        self.mcu = mcu
        return
    
    def _run_pump(self, speed):
        """
        Relay instructions to pump.
        - mcu: serial connection to pump
        - speed: speed of pump of rotation
        """
        try:
            self.mcu.write(bytes("{}\n".format(speed), 'utf-8'))
        except AttributeError:
            pass
        
    def _run_solenoid(self, state):
        """
        Relay instructions to valve.
        - mcu: serial connection to pump
        - state: valve channel
            - -1 to -8   : open specific valve
            - 1 to 8     : close specific valve
            - 9          : close all valves
        """
        try:
            self.mcu.write(bytes("{}\n".format(state), 'utf-8'))
        except AttributeError:
            pass
        
    def dispense(self, pump_speed, prime_time, drop_time, channel):
        """
        Dispense (aspirate) liquid from (into) syringe.
        - mcu: serial connection to pump
        - pump_speed: speed of pump of rotation
            - <0    : aspirate
            - >0    : dispense
        - prime_time: time to prime the peristaltic pump
        - drop_time: time to achieve desired volume
        - channel: valve channel
        """
        run_time = prime_time + drop_time
        interval = 0.1
        
        starttime = time.time()
        self._run_solenoid(-channel) # open channel
        self._run_pump(pump_speed)
        
        while(True):
            time.sleep(0.001)
            if (interval <= time.time() - starttime):
                # self.printer(run_time - interval)
                interval += 0.1
            if (run_time <= time.time() - starttime):
                # self.printer(time.time() - starttime)
                break
        
        starttime = time.time()
        interval = 0.1
        self._run_solenoid(-channel)
        self._run_pump(-abs(pump_speed))

        while(True):
            time.sleep(0.001)
            if (interval <= time.time() - starttime):
                # self.printer(prime_time - interval)
                interval += 0.1
            if (prime_time <= time.time() - starttime):
                # self.printer(time.time() - starttime)
                self._run_pump(10)
                self._run_solenoid(channel) # close channel
                break
        return
    
    def isConnected(self):
        if self.mcu == None:
            print(f"{self.__class__} ({self._port}) not connected.")
            return False
        return True
        

class Syringe(object):
    def __init__(self, capacity, channel, offset=(0,0,0), priming_time=PRIMING_TIME):
        self.capacity = capacity
        self.channel = channel
        self.offset = tuple(offset)
        
        self.prev_action = ''
        self.reagent = ''
        self.volume = 0
        
        self._priming_time = priming_time
        pass
    
    def update(self, field, value):
        attrs = ['prev_action', 'reagent', 'volume']
        if field not in attrs:
            print(f"Select a field from: {', '.join(attrs)}")
        else:
            setattr(self, field, value)
        return


class SyringeAssembly(LiquidHandler):
    """
    'SyringeAssembly' class contain methods to control the pump and the valve unit.
    """
    def __init__(self, port, capacities=[], channels=[], offsets=[], **kwargs):
        self._checkInputs(capacities=capacities, channels=channels, offsets=offsets)
        self.pump = Pump(port)
        properties = list(zip(capacities, channels, offsets))
        self.channels = {chn: Syringe(cap, chn, off) for cap,chn,off in properties}
        return
    
    def _checkInputs(self, **kwargs):
        keys = list(kwargs.keys())
        if any(len(kwargs[key]) != len(kwargs[keys[0]]) for key in keys):
            raise Exception(f"Ensure the lengths of these inputs are the same: {', '.join(keys)}")
        return
    
    def _getValues(self, channels, field):
        if len(channels) == 0:
            channels = list(self.channels.keys())
        return [(key, getattr(self.channels[key], field)) for key in channels]

    def aspirate(self, channel, reagent, vol, speed=DEFAULT_SPEED, wait=1, pause=False):
        '''
        Adjust the valve and aspirate reagent
        - vol: volume
        - speed: speed of pump rotation

        Returns: None
        '''
        self.pump.flags['busy'] = True
        syringe = self.channels[channel]
        vol = min(vol, syringe.capacity - syringe.volume)

        if vol != 0:
            t_aspirate = vol / speed * CALIB_ASPIRATE
            if syringe.prev_action == '':
                t_aspirate *= 1.3
            elif syringe.prev_action == 'aspirate':
                t_aspirate *= 1
            elif syringe.prev_action == 'dispense':
                t_aspirate *= 1.6
            print(t_aspirate)
            
            t_prime = 50 / speed * CALIB_ASPIRATE
            pump_speed = -abs(speed)
            # log_now(f'Syringe {self.order}: aspirate {vol}uL {self.reagent}...', save=log)
            self.pump.dispense(pump_speed, t_prime, t_aspirate, channel)
            
            syringe.prev_action = 'aspirate'
            syringe.reagent = reagent
            syringe.volume += vol
        
        time.sleep(wait)
        # log_now(f'Syringe {self.order}: done', save=log)
        if pause:
            input("Press 'Enter to proceed.")
        self.pump.flags['busy'] = False
        return

    def calibrate(self, *args, **kwargs):
        return super().calibrate(*args, **kwargs)

    def cycle(self, channel, vol, speed=DEFAULT_SPEED, wait=1):
        self.aspirate(channel, vol, speed=speed, wait=wait)
        self.dispense(channel, vol, speed=speed, wait=wait, force_dispense=True)
        return

    def dispense(self, channel, vol, speed=DEFAULT_SPEED, wait=1, pause=False, force_dispense=False):
        '''
        Adjust the valve and dispense reagent
        - vol: volume
        - speed: speed of pump rotation
        - force_dispense: continue with dispense even if insufficient volume in syringe

        Returns: None
        '''
        self.pump.flags['busy'] = True
        syringe = self.channels[channel]
        if force_dispense:
            vol = min(vol, syringe.volume)
        elif vol > syringe.volume:
            # log_now(f'Syringe {self.order}: Current volume too low for required dispense', save=log)
            pass
        
        if force_dispense or vol < syringe.volume:
            t_dispense = vol / speed * CALIB_DISPENSE
            if syringe.prev_action == '':
                t_dispense *= 1
            elif syringe.prev_action == 'aspirate':
                t_dispense *= 1.55
            elif syringe.prev_action == 'dispense':
                t_dispense *= 1
            print(t_dispense)
            
            t_prime = 50 / speed * CALIB_DISPENSE
            pump_speed = abs(speed)
            # log_now(f'Syringe {self.order}: dispense {vol}uL {self.reagent}...', save=log)
            self.pump.dispense(pump_speed, t_prime, t_dispense, channel)
            
            syringe.prev_action = 'dispense'
            syringe.volume -= vol
            if syringe.volume <= 0:
                syringe.reagent = ''
                syringe.volume = 0
        
        time.sleep(wait)
        # log_now(f'Syringe {self.order}: done', save=log)
        if pause:
            input("Press 'Enter to proceed.")
        self.pump.flags['busy'] = False
        return

    def empty(self, channel, wait=1, pause=False):
        '''
        Adjust the valve and empty syringe

        Returns: None
        '''
        syringe = self.channels[channel]
        self.dispense(channel, syringe.capacity, wait=wait, pause=pause, force_dispense=True)
        return
    
    def emptyAll(self, channels=[], wait=1, pause=False):
        if len(channels) == 0:
            channels = list(self.channels.keys())
        for channel in channels:
            self.empty(channel, wait, pause)
        return

    def fill(self, channel, reagent, prewet=True, wait=1, pause=False):
        '''
        Adjust the valve and fill syringe with reagent
        - reagent: reagent to be filled in syringe
        - vol: volume

        Returns: None
        '''
        syringe = self.channels[channel]
        vol = syringe.capacity - syringe.volume

        if prewet:
            # log_now(f'Syringe {self.order}: pre-wet syringe...')
            for c in range(WETTING_CYCLES):
                if c == 0:
                    self.cycle(channel, vol=vol*1.1, wait=2)
                else:
                    self.cycle(channel, vol=200)
            # log_now(f'Syringe {self.order}: done')

        self.aspirate(channel, reagent, vol, wait=wait, pause=pause)
        return
    
    def fillAll(self, channels=[], reagents=[], prewet=True, wait=1, pause=False):
        if len(channels) == 0:
            channels = list(self.channels.keys())
        self._checkInputs(channels=channels, reagents=reagents)
        for channel,reagent in zip(channels, reagents):
            self.fill(channel, reagent, prewet, wait, pause)
        return
    
    def getReagents(self, channels=[]):
        return self._getValues(channels, 'reagent')
    
    def getVolumes(self, channels=[]):
        return self._getValues(channels, 'volume')

    def isBusy(self):
        return self.pump.flags['busy']
    
    def isConnected(self):
        return self.pump.isConnected()

    def prime(self, channel):
        syringe = self.channels[channel]
        self.pump.flags['busy'] = True
        self.pump.dispense(-300, syringe._priming_time, 0, channel)
        self.pump.flags['busy'] = False
        return
    
    def primeAll(self, channels=[]):
        if len(channels) == 0:
            channels = list(self.channels.keys())
        for channel in channels:
            self.prime(channel)
        return
    
    def rinse(self, channel, rinse_cycles=3):
        # log_now(f'Syringe {self.order}: rinsing syringe...')
        for _ in range(rinse_cycles):
            self.cycle(channel, vol=2000)
        # log_now(f'Syringe {self.order}: done')
        return
    
    def rinseAll(self, channels=[], rinse_cycles=3):
        if len(channels) == 0:
            channels = list(self.channels.keys())
        for channel in channels:
            self.rinse(channel, rinse_cycles)
        return
    
    def update(self, channel, field, value):
        return self.channels[channel].update(field, value)
