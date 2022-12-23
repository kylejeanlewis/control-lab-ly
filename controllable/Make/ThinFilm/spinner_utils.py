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
print(f"Import: OK <{__name__}>")

class Spinner(object):
    """
    Spinner class contains methods to control the spin coater unit

    Args:
        port (str): com port address
        order (int, optional): channel order. Defaults to 0.
        position (tuple, optional): x,y,z position of spinner. Defaults to (0,0,0).
        verbose (bool, optional): whether to print outputs. Defaults to False.
    """
    def __init__(self, port:str, order=0, position=(0,0,0), verbose=False, **kwargs):
        self.mcu = None
        self.order = order
        self.position = tuple(position)
        self.speed = 0
        self.verbose = verbose
        
        self._flags = {
            'busy': False
        }
        self._port = None
        self._baudrate = None
        self._timeout = None
        
        self._connect(port)
        return
    
    def _connect(self, port:str):
        """
        Connect to serial port

        Args:
            port (str): com port address
        """
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
    
    def _run_speed(self, speed:int):
        """
        Relay spin speed to spinner

        Args:
            speed (int): spin speed
        """
        try:
            self.mcu.write(bytes("{}\n".format(speed), 'utf-8'))
        except AttributeError:
            pass
        print("Spin speed: {}".format(speed))
        return
    
    def _run_spin_step(self, speed:int, run_time:int):
        """
        Perform timed spin step

        Args:
            speed (int): spin speed
            run_time (int): spin time
        """
        starttime = time.time()
        
        interval = 1
        self._run_speed(speed)
        
        while(True):
            time.sleep(0.1)
            if (interval <= time.time() - starttime):
                # self.printer(run_time - interval)
                interval += 1
            if (run_time <= time.time() - starttime):
                # self.printer(time.time() - starttime)
                self._run_speed(0)
                break

    def execute(self, soak_time=0, spin_speed=2000, spin_time=1):
        """
        Executes the soak and spin steps

        Args:
            soak_time (int, optional): soak time. Defaults to 0.
            spin_speed (int, optional): spin speed. Defaults to 2000.
            spin_time (int, optional): spin time. Defaults to 1.
        """
        self._flags['busy'] = True
        self.soak(soak_time)
        self.spin(spin_speed, spin_time)
        self._flags['busy'] = False
        # self._flags['complete'] = True
        return
    
    def isConnected(self):
        """
        Checks whether the spinner is connected

        Returns:
            bool: whether the spinner is connected
        """
        if self.mcu == None:
            print(f"{self.__class__} ({self._port}) not connected.")
            return False
        return True

    def soak(self, seconds:int):
        """
        Executes the soak step

        Args:
            seconds (int): soak time
        """
        self.speed = 0
        if seconds:
            # log_now(f'Spinner {self.order}: start soak')
            time.sleep(seconds)
            # log_now(f'Spinner {self.order}: end soak')
        return

    def spin(self, speed:int, seconds:int):
        """
        Executes the spin step

        Args:
            speed (int): spin speed
            seconds (int): spin time
        """
        self.speed = speed
        # log_now(f'Spinner {self.order}: start spin ({speed}rpm)')
        self._run_spin_step(speed, seconds)
        # log_now(f'Spinner {self.order}: end spin')
        self.speed = 0
        return


class SpinnerAssembly(object):
    """
    Spinner assembly with multiple spinners

    Args:
        ports (list, optional): list of com port strings. Defaults to [].
        channels (list, optional): list of int channel indices. Defaults to [].
        positions (list, optional): list of tuples of x,y,z spinner positions. Defaults to [].
    """
    def __init__(self, ports=[], channels=[], positions=[]):
        self._checkInputs(ports=ports, channels=channels, positions=positions)
        properties = list(zip(ports, channels, positions))
        self.channels = {chn: Spinner(port, chn, pos) for port,chn,pos in properties}
        return
    
    def _checkInputs(self, **kwargs):
        """
        Checks whether the input lists are the same length

        Raises:
            Exception: Inputs need to be the same length
        """
        keys = list(kwargs.keys())
        if any(len(kwargs[key]) != len(kwargs[keys[0]]) for key in keys):
            raise Exception(f"Ensure the lengths of these inputs are the same: {', '.join(keys)}")
        return
        
    def execute(self, channel:int, soak_time:int, spin_speed:int, spin_time:int):
        """
        Executes the soak and spin steps

        Args:
            channel (int): channel index
            soak_time (int, optional): soak time. Defaults to 0.
            spin_speed (int, optional): spin speed. Defaults to 2000.
            spin_time (int, optional): spin time. Defaults to 1.
        """
        return self.channels[channel].execute(soak_time, spin_speed, spin_time)
    
    def isBusy(self):
        """
        Check whether any of the spinners are still busy

        Returns:
            bool: whether any of the spinners are busy
        """
        return any([spinner._flags['busy'] for spinner in self.channels.values()])
    
    def isConnected(self):
        """
        Check whether all spinners are connected

        Returns:
            bool: whether all spinners are connected
        """
        return all([spinner.isConnected() for spinner in self.channels.values()])
    
    def soak(self, channel:int, seconds:int):
        """
        Executes the soak step

        Args:
            channel (int): channel index
            seconds (int): soak time
        """
        return self.channels[channel].soak(seconds)
    
    def spin(self, channel:int, speed:int, seconds:int):
        """
        Executes the spin step

        Args:
            channel (int): channel index
            speed (int): spin speed
            seconds (int): spin time
        """
        return self.channels[channel].spin(speed, seconds)
