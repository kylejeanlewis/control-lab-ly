# Standard library imports
from __future__ import annotations
from collections import deque
from copy import deepcopy
from datetime import datetime
import logging
from pathlib import Path
import threading
import time
from types import SimpleNamespace
from typing import Iterable, NamedTuple, Any, Callable

# Third party imports
import pandas as pd

# Local application imports
from ...core import factory, datalogger
from ...core.compound import Ensemble
from ...core.device import StreamingDevice
from .. import Program, ProgramDetails

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)

COLUMNS = ('Time', 'Displacement', 'Value', 'Factor', 'Baseline', 'Force')
"""Headers for output data from force sensor"""
G = 9.81
"""Acceleration due to Earth's gravity"""

MAX_LEN = 100
MAX_SPEED = 0.375 # mm/s (22.5mm/min)
READ_FORMAT = "{target},{speed},{displacement},{end_stop},{value}\r\n"
OUT_FORMAT = '{data}\r\n'
Data = NamedTuple('Data', [('data',str)])
MoveForceData = NamedTuple('MoveForceData', [('target', float),('speed', float),('displacement', float),('value', int),('end_stop', bool)])

class ForceActuator:
    """ 
    ForceSensor provides methods to read out values from a force sensor

    ### Constructor
    Args:
        `port` (str): COM port address
        `limits` (Sequence[float], optional): lower and upper limits of actuation. Defaults to (-30,0).
        `home_displacement` (float, optional): starting displacement of home position. Defaults to -1.0.
        `threshold` (float, optional): force threshold to stop movement. Defaults to 800 * G.
        `calibration_factor` (float, optional): calibration factor of device readout to newtons. Defaults to 1.0.
        `precalibration` (Sequence[float], optional): pre-calibration correction against a calibrated load cell. Defaults to (1.0, 0.0).
        `touch_force_threshold` (float, optional): force threshold to detect touching of sample. Defaults to 2 * G.

    ### Attributes and properties:
        `baseline` (float): baseline readout at which zero newtons is set
        `calibration_factor` (float): calibration factor of device readout to newtons
        `displacement` (float): machine displacement
        `end_stop` (bool): whether the end stop is triggered
        `home_displacement` (float): starting displacement of home position
        `precision` (int): number of decimal places to print force value
        `threshold` (float): force threshold to stop movement
        `force` (float): force experienced
        `limits` (np.ndarray): lower and upper limits of movement
    
    ### Methods:
        `clearCache`: clear most recent data and configurations
        `disconnect`: disconnect from device
        `getForce`: get the force response
        `home`: home the actuator
        `isFeasible`: checks and returns whether the target displacement is feasible
        `measure`: measure the stress-strain response of sample
        `move`: move the actuator by desired distance. Alias of `moveBy()` method
        `moveBy`: move the actuator by desired distance
        `moveTo`: move the actuator to desired displacement
        `reset`: reset the device
        `setThreshold`: set the force threshold for the machine
        `shutdown`: shutdown procedure for tool
        `tare`: alias for zero()
        `stream`: start or stop feedback loop
        `record`: start or stop data recording
        `touch`: touch the sample
        `waitThreshold`: wait for force sensor to reach the force threshold
        `zero`: set the current reading as baseline (i.e. zero force)
    """

    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(
        busy=False, verbose=False, connected=False,
        get_feedback=False, pause_feedback=False, read=True,
        record=False, threshold=False
    )
    def __init__(self,
        port: str,
        limits: Iterable[float] = (-30.0, 0),
        force_threshold: float = 10000,
        stabilize_timeout: float = 1, 
        force_tolerance: float = 0.01, 
        *, 
        home_displacement: float = -1.0,
        max_speed: float = MAX_SPEED,
        steps_per_second: int = 6400,
        calibration_factor: float = 1.0,
        correction_parameters: tuple[float] = (1.0,0.0),
        touch_force_threshold: float = 2 * G,
        touch_timeout: int = 300,
        from_top: bool = True,      # whether compression direction is towards negative displacement
        baudrate: int = 115200,
        verbose: bool = False, 
        **kwargs
    ):
        """ 
        Initialize the actuated sensor
        
        Args:
            port (str): Serial port
            limits (Iterable[float]): Lower and upper limits for the actuator
            force_threshold (float): Force threshold
            stabilize_timeout (float): Time to wait for the device to stabilize
            force_tolerance (float): Tolerance for
            home_displacement (float): Home position
            max_speed (float): Maximum speed
            steps_per_second (int): Steps per second
            calibration_factor (float): Calibration factor
            correction_parameters (tuple[float]): Polynomial correction parameters
            baudrate (int): Baudrate for serial communication
            verbose (bool): Print verbose output
        """
        defaults = dict(
            init_timeout=3, 
            data_type=MoveForceData, 
            read_format=READ_FORMAT, 
        )
        defaults.update(kwargs)
        kwargs = defaults
        kwargs['port'] = port
        kwargs['baudrate'] = baudrate
        self.device: StreamingDevice = kwargs.get('device', factory.create_from_config(kwargs))
        self.flags: SimpleNamespace = deepcopy(self._default_flags)
        
        self._logger = logger.getChild(f"{self.__class__.__name__}.{id(self)}")
        self.verbose = verbose
        
        # Category specific attributes
        # Data logging attributes
        self.buffer: deque[tuple[NamedTuple, datetime]] = deque(maxlen=MAX_LEN)
        self.records: deque[tuple[NamedTuple, datetime]] = deque()
        self.record_event = threading.Event()
        
        # Measurer property
        self.buffer_df = pd.DataFrame(columns=COLUMNS)
        
        # Measurer specific attributes
        self.program: Program|Any|None = None
        self.runs = dict()
        self.n_runs = 0
        self._threads = dict()
        
        # LoadCell specific attributes        
        self.force_tolerance = force_tolerance
        self.stabilize_timeout = stabilize_timeout
        self._stabilize_start_time = None
        
        self.baseline = 0
        self.calibration_factor = calibration_factor
        self.correction_parameters = correction_parameters
        
        # ActuatedSensor specific attributes
        self.displacement = 0
        self.force_threshold = force_threshold
        self.home_displacement = home_displacement
        self.limits = (min(limits), max(limits))
        self.max_speed = max_speed
        self._steps_per_second = steps_per_second
        
        # ForceActuator specific attributes
        self.end_stop = False
        self.precision = 3
        self._force = 0
        self.touch_force_threshold = touch_force_threshold
        self.touch_timeout = touch_timeout
        self.from_top = from_top
        
        if kwargs.get('final', True):
            self.connect()
        return
    
    def __del__(self):
        self.shutdown()
        return
    
    @property
    def connection_details(self) -> dict:
        """Connection details for the device"""
        return self.device.connection_details
    
    @property
    def is_busy(self) -> bool:
        """Whether the device is busy"""
        return self.flags.busy
    
    @property
    def is_connected(self) -> bool:
        """Whether the device is connected"""
        return self.device.is_connected
    
    @property
    def verbose(self) -> bool:
        """Verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        level = logging.DEBUG if value else logging.INFO
        CustomLevelFilter().setModuleLevel(self._logger.name, level)
        return
    
    @property
    def records_df(self) -> pd.DataFrame:
        """DataFrame of records"""
        return self.buffer_df.copy()
    
    # ForceActuator implementation
    @property
    def force(self) -> float:
        return round(self._force, self.precision)
    
    def connect(self):
        """Establish connection with device"""
        # Measurer specific
        self.device.connect()
        
        #LoadCell specific
        if not self.is_connected:
            return
        self.device.clearDeviceBuffer()
        start_time = time.perf_counter()
        while True:
            time.sleep(0.1)
            out = self.device.query(None,multi_out=False)
            if out is not None:
                time.sleep(1)
                self.device.clearDeviceBuffer()
                break
            if (time.perf_counter()-start_time) > 5:
                break
        
        # ActuatedSensor specific
        # self.stream(True)
        self.home()
        # self.stream(False)
        self.zero()
        self.stream(True)
        return
    
    def disconnect(self):
        """Disconnect from device"""
        self.device.disconnect()
        return
    
    def reset(self):
        """Reset the device"""
        # Measurer specific
        self.clearCache()
        self.program = None
        
        # LoadCell specific
        self.baseline = 0
        
        # ForceActuator specific
        self.resetFlags()
        return
    
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = deepcopy(self._default_flags)
        self.record_event.clear()
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.stream(on=False)
        self.reset()
        self.disconnect()
        return
    
    # Measurer specific properties and methods
    # Measurer implementation
    def measure(self, *args, parameters: dict|None = None, blocking:bool = True, **kwargs) -> pd.DataFrame|None:
        """
        Run the measurement program
        
        Args:
        *args: positional arguments
            parameters (dict, optional): dictionary of kwargs. Defaults to None.
            blocking (bool, optional): whether to block until completion. Defaults to True.
            **kwargs: keyword arguments
            
        Returns:
            pd.DataFrame|None: dataframe of data collected
        """
        assert issubclass(self.program, Program), "No Program loaded"
        new_run = self.program(
            instrument = self, 
            parameters = parameters,
            verbose = self.verbose
        )
        kwargs.update(new_run.parameters)
        
        self.n_runs += 1
        self._logger.info(f"Run ID: {self.n_runs}")
        self.runs[self.n_runs] = new_run
        if not blocking:
            thread = threading.Thread(target=new_run.run, args=args, kwargs=kwargs)
            thread.start()
            self._threads['measure'] = thread
            self.flags.busy = True
            return
        new_run.run(*args, **kwargs)
        self.flags.busy = False
        return new_run.data_df
    
    # Measurer implementation
    def loadProgram(self, program: Program, docstring_parser: Callable[[Any,bool],ProgramDetails]|None = None):
        """
        Load a program to the Measurer
        
        Args:
            program (Program): program to load
        """
        assert issubclass(program, Program), "Ensure program type is a subclass of Program"
        self.program = program
        if docstring_parser is None and hasattr(program, 'parseDocstring'):
            docstring_parser = program.parseDocstring
        if docstring_parser is not None:
            self.measure.__func__.__doc__ = docstring_parser(program, verbose=self.verbose)
        return
        
    def clearCache(self):
        """Clear most recent data and configurations"""
        # ForceActuator specific
        self.flags.pause_feedback = True
        time.sleep(0.1)
        # self.buffer_df = pd.DataFrame(columns=COLUMNS)
        self.buffer_df.drop(index=self.buffer_df.index, inplace=True, errors='ignore')
        self.buffer.clear()
        self.records.clear()
        self.flags.pause_feedback = False
        return
 
    # Measurer implementation
    def getDataframe(self, data_store: Iterable[tuple[NamedTuple, datetime]]) -> pd.DataFrame:
        """
        Get dataframe of data collected
        
        Args:
            data_store (Iterable[tuple[NamedTuple, datetime]]): data store
            
        Returns:
            pd.DataFrame: dataframe of data collected
        """
        return datalogger.get_dataframe(data_store=data_store, fields=self.device.data_type._fields)
    
    # Measurer implementation
    def saveData(self, filepath:str|Path):
        """
        Save data to file
        
        Args:
            filepath (str|Path): path to save file
        """
        if not len(self.records_df):
            raise ValueError("No records to save. Ensure you have recorded data before saving.")
        self.records_df.to_csv(filepath)
        return
    
    # LoadCell implementation
    def getAttributes(self) -> dict:
        """
        Get attributes
        
        Returns:
            dict: Attributes
        """
        relevant = ['correction_parameters', 'baseline', 'calibration_factor', 'force_tolerance', 'stabilize_timeout']
        return {key: getattr(self, key) for key in relevant}
    
    # ForceActuator implementation
    def getData(self, *args, **kwargs) -> MoveForceData|None:
        """
        Get data from device
        
        Returns:
            MoveForceData: Data from device
        """
        response = self.device.read()
        now = datetime.now()
        try:
            data,_ = self.device.processOutput(response, timestamp=now)
            if data is None:
                return None
            data: MoveForceData = data
            displacement = data.displacement
            end_stop = data.end_stop
            value = data.value
        except ValueError:
            return None
        else:
            self._force = self._calculate_force(self._correct_value(value))
            self.displacement = displacement
            self.end_stop = end_stop
            over_threshold = (abs(self.force) > abs(self.force_threshold))
            self.flags.threshold = bool(over_threshold)
            if self.verbose:
                print(f"{displacement:.2f} mm | {self.force:.5E} mN | {value:.2f}")
            if self.record_event.is_set():
                self.records.append((data, now))
                values = [
                    now,
                    displacement, 
                    value, 
                    self.calibration_factor, 
                    self.baseline, 
                    self._force
                ]
                row = {k:v for k,v in zip(COLUMNS, values)}
                new_row_df = pd.DataFrame(row, index=[0])
                dfs = [_df for _df in [self.buffer_df, new_row_df] if len(_df)]
                self.buffer_df = pd.concat(dfs, ignore_index=True)
            else:
                self.buffer.append((data, now))
        return data
    
    # LoadCell implementation
    def atForce(self, 
        force: float, 
        current_force: float|None = None,
        *, 
        tolerance: float|None = None,
        stabilize_timeout: float = 0
    ) -> bool:
        """
        Check if the device is at the target force
        
        Args:
            force (float): Target force
            current_force (float|None): Current force
            tolerance (float): Tolerance for force
            stabilize_timeout (float): Time to wait for the device to stabilize
            
        Returns:
            bool: True if the device is at the target force
        """
        current_force = current_force or self.getForce()
        if current_force is None:
            return False
        
        tolerance = tolerance or self.force_tolerance
        stabilize_timeout = stabilize_timeout or self.stabilize_timeout
        if abs(current_force - force) > tolerance:
            self._stabilize_start_time = None
            return False
        self._stabilize_start_time = self._stabilize_start_time or time.perf_counter()
        if ((time.perf_counter()-self._stabilize_start_time) < stabilize_timeout):
            return False
        return True
    
    # ForceActuator implementation
    def getForce(self) -> float|None:
        """
        Get the force response and displacement of actuator
        
        Returns:
            str: device response
        """
        self.getData()
        return self.force
    
    # LoadCell implementation
    def getValue(self) -> float|None:
        """
        Get the value readout from device
        
        Returns:
            float|None: Value readout
        """
        data = self.getData()
        if data is None:
            return None
        return self._correct_value(data.value)
    
    # ActuatedSensor specific properties and methods
    def atDisplacement(self, displacement: float, current_displacement: float|None = None) -> bool:
        """
        Check if the device is at the target displacement
        
        Args:
            displacement (float): Target displacement
            current_displacement (float|None): Current displacement. Defaults to None.
            
        Returns:
            bool: True if the device is at the target displacement
        """
        current_displacement = current_displacement or self.getDisplacement()
        if current_displacement is None:
            return False
        return current_displacement == displacement
    
    # ForceActuator implementation
    def getDisplacement(self) -> float|None:
        """
        Get displacement
        
        Returns:
            float: Displacement in mm
        """
        self.getData()
        return self.displacement
    
    # ForceActuator implementation
    def home(self) -> bool:
        """
        Home the actuator
        
        Returns:
            bool: whether homing is a success
        """
        if not self.flags.get_feedback:
            self.stream(True)
        try:
            success = self.device.write('H 0')
            if not success:
                return False
        except Exception:
            pass
        else:
            time.sleep(1)
            while self.displacement != self.home_displacement:
                time.sleep(0.1)
            while self.displacement != self.home_displacement:
                time.sleep(0.1)
            self.stream(False)
            self.device.disconnect()
            time.sleep(2)
            self.device.connect()
            time.sleep(2)
            self.stream(True)
            self.device.write('H 0')
            time.sleep(1)
            while self.displacement != self.home_displacement:
                time.sleep(0.1)
        self.displacement = self.home_displacement
        return True

    # ActuatedSensor implementation
    def move(self, by: float, speed: float|None = None) -> bool:
        """
        Move the actuator to the target displacement and apply the target force
        
        Args:
            by (float): distance in mm
            speed (float, optional): movement speed. Defaults to 0.375.
            
        Returns:
            bool: whether movement is successful
        """
        speed = speed or self.max_speed
        return self.moveBy(by, speed=speed)
    
    # ActuatedSensor implementation
    def moveBy(self, by: float, speed: float|None = None) -> bool:
        """
        Move the actuator by desired distance

        Args:
            by (float): distance in mm
            speed (float, optional): movement speed. Defaults to 0.375.

        Returns:
            bool: whether movement is successful
        """
        speed = speed or self.max_speed
        new_displacement = self.displacement + by
        return self.moveTo(new_displacement, speed)
    
    # ForceActuator implementation
    def moveTo(self, to: float, speed: float|None = None) -> bool:
        """
        Move the actuator to desired displacement

        Args:
            to (float): displacement in mm
            speed (float, optional): movement speed. Defaults to 0.375.

        Returns:
            bool: whether movement is successful
        """
        assert self.limits[0] <= to <= self.limits[1], f"Target displacement out of range: {to}"
        speed = speed or self.max_speed
        to = round(to,2)
        rpm = int(speed * self._steps_per_second)
        if not self.flags.get_feedback:
            self.stream(True)
        try:
            self.device.write(f'G {to} {rpm}')
        except Exception:
            pass
        else:
            displacement = self.waitThreshold(to)
            self._logger.info(displacement)
            self.device.write(f'G {displacement} {rpm}')
        self.displacement = displacement
        return displacement == to

    # ForceActuator implementation
    def touch(self, 
        force_threshold: float = 0.1, 
        displacement_threshold: float|None = None, 
        speed: float|None = None, 
        from_top: bool = True,
        record: bool = False,
        timeout:int=None,
    ) -> bool:
        """
        Apply the target force
        
        Args:
            force_threshold (float): target force. Defaults to 0.1.
            displacement_threshold (float): target displacement. Defaults to None.
            speed (float): movement speed. Defaults to None.
            from_top (bool): whether compression direction is towards negative displacement. Defaults to True.
            record (bool): whether to record data. Defaults to False.
            
        Returns:
            bool: whether movement is successful (i.e. force threshold is not reached)
        """
        if timeout is not None:
            default_timeout = self.touch_timeout
            self.touch_timeout = timeout
        speed = speed or self.max_speed
        
        self._logger.info('Touching...')
        # if not self.flags.get_feedback:
        #     self.stream(True)
        if abs(round(self.force)) > self.touch_force_threshold:
            # self.stream(False)
            self.zero()
            # self.stream(True)
        
        _threshold = self.force_threshold
        # touch_timeout = self.touch_timeout
        self.force_threshold = self.touch_force_threshold if force_threshold is None else force_threshold
        # self.touch_timeout = 3600
        
        if record:
            self.stream(False)
            self.record(True)
        try:
            # touch sample
            self.moveTo(displacement_threshold, speed=speed)
            time.sleep(2)
        except Exception as e:
            self._logger.exception(e)
        else:
            ...
        finally:
            self.force_threshold = _threshold
            if timeout is not None:
                self.touch_timeout = default_timeout
            # self.touch_timeout = touch_timeout
            time.sleep(2)
        self._logger.info('In contact')
        if record:
            self.record(False)
            self.stream(True)
        self.flags.threshold = False
        return True
    
    # ForceActuator implementation
    def waitThreshold(self, displacement:float, timeout:float | None = None) -> float:
        """
        Wait for force sensor to reach the threshold

        Args:
            displacement (float): target displacement
            timeout (float|None, optional): timeout duration in seconds. Defaults to None.

        Returns:
            float: actual displacement upon reaching threshold
        """
        timeout = self.touch_timeout if timeout is None else timeout
        start = time.time()
        while self.displacement != displacement:
            time.sleep(0.001)
            if self.force >= abs(self.force_threshold):
                displacement = self.displacement
                self.flags.threshold = True
                self._logger.warning('Made contact')
                break
            if time.time() - start > timeout:
                self._logger.warning('Touch timeout')
                break
        return self.displacement
    
    # ForceActuator implementation
    def zero(self, timeout:int = 5):
        """
        Set current reading as baseline (i.e. zero force)
        
        Args:
            timeout (int, optional): duration to wait while zeroing, in seconds. Defaults to 5.
        """
        # ForceActuator specific
        temp_record_state = self.record_event.is_set()
        temp_buffer_df = self.buffer_df.copy()
        if self.flags.get_feedback:
            self.stream(False)
        if self.record_event.is_set():
            self.record(False)
        self.reset()
        self.record(True)
        self._logger.info(f"Zeroing... ({timeout}s)")
        time.sleep(timeout)
        self.record(False)
        self.baseline = self.buffer_df['Value'].mean()
        self.clearCache()
        self.buffer_df = temp_buffer_df.copy()
        self._logger.info("Zeroing complete.")
        self.record(temp_record_state)
        return
    
    # ForceActuator implementation
    def record(self, on: bool, show: bool = False, clear_cache: bool = False):
        """
        Start or stop data recording

        Args:
            on (bool): whether to start recording data
        """
        _ = self.record_event.set() if on else self.record_event.clear()
        self.flags.get_feedback = on
        self.flags.pause_feedback = False
        if clear_cache:
            self.clearCache()
        self.stream(on=on)
        return
    
    # ForceActuator implementation
    def stream(self, on: bool, show: bool = False):
    # def stream(self, on:bool):
        """
        Start or stop feedback loop

        Args:
            on (bool): whether to start loop to continuously read from device
        """
        self.flags.get_feedback = on
        if on:
            if 'feedback_loop' in self._threads:
                self._threads['feedback_loop'].join()
            thread = threading.Thread(target=self._loop_feedback)
            thread.start()
            self._threads['feedback_loop'] = thread
        else:
            self._threads['feedback_loop'].join()
        return
    
    # LoadCell implementation
    def _calculate_force(self, value: float) -> float:
        """
        Calculate force from value
        
        Args:
            value (float): Value
            
        Returns:
            float: Force
        """
        return (value-self.baseline)/self.calibration_factor * G
    
    # LoadCell implementation
    def _correct_value(self, value: float) -> float:
        """
        Correct value
        
        Args:
            value (float): Value
            
        Returns:
            float: Corrected value
        """
        # return sum([param * (value**i) for i,param in enumerate(self.correction_parameters[::-1])])
        return (value-self.correction_parameters[1])/self.correction_parameters[0]

    # ForceActuator implementation
    def _loop_feedback(self):
        """Loop to constantly read from device"""
        print('Listening...')
        while self.flags.get_feedback:
            if self.flags.pause_feedback:
                continue
            self.getData()
        print('Stop listening...')
        return

Parallel_ForceActuator = Ensemble.factory(ForceActuator)
