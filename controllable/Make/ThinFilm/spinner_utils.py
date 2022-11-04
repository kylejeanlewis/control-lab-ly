# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import time

# Local application imports
from .. import Maker
print(f"Import: OK <{__name__}>")

class Spinner(Maker):
    """
    'Spinner' class contains methods to control the spin coater unit.
    """
    def __init__(self, order, position, mcu):
        self.order = order
        self.position = position
        self.mcu = mcu
        self.speed = 0
        self.etc = time.time()
        self.flags = {
            'busy': False,
            'complete': False
        }
        return
    
    def _run_speed(self, speed):
        """
        Relay instructions to spincoater.
        - mcu: serial connection to spincoater
        - speed: spin speed
        """
        try:
            self.mcu.write(bytes("{}\n".format(speed), 'utf-8'))
        except AttributeError:
            pass
        print("Spin speed: {}".format(speed))
    
    def _run_spin_step(self, speed, run_time):
        """
        Perform timed spin step
        - mcu: serial connection to spincoater
        - speed: spin speed
        - run_time: spin time
        """
        starttime = time.time()
        
        interval = 1
        self._run_speed(speed)
        
        while(True):
            time.sleep(0.1)
            if (interval <= time.time() - starttime):
                self.printer(run_time - interval)
                interval += 1
            if (run_time <= time.time() - starttime):
                self.printer(time.time() - starttime)
                self._run_speed(0)
                break

    def execute(self, soak_time, spin_speed, spin_time):
        '''
        Executes the soak and spin steps
        - soak_time: soak time
        - spin_speed: spin speed
        - spin_time: spin time

        Returns: None
        '''
        self.flags['busy'] = True
        self.soak(soak_time)
        self.spin(spin_speed, spin_time)
        self.flags['busy'] = False
        # self.flags['complete'] = True
        return

    def soak(self, seconds):
        '''
        Executes the soak step
        - seconds: soak time

        Returns: None
        '''
        self.speed = 0
        if seconds:
            # log_now(f'Spinner {self.order}: start soak')
            time.sleep(seconds)
            # log_now(f'Spinner {self.order}: end soak')
        return

    def spin(self, speed, seconds):
        '''
        Executes the spin step
        - speed: spin speed
        - seconds: spin time

        Returns: None
        '''
        self.speed = speed
        # log_now(f'Spinner {self.order}: start spin ({speed}rpm)')
        self._run_spin_step(speed, seconds)
        # log_now(f'Spinner {self.order}: end spin')
        self.speed = 0
        return

