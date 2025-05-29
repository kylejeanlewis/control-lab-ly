# Standard library imports
from __future__ import annotations
from copy import deepcopy
from datetime import datetime
import logging
import threading
import time
from types import SimpleNamespace
from typing import Iterable, NamedTuple, Any

# Third party imports
import pandas as pd

# Local application imports
from ...core import factory
from ...core.compound import Ensemble
from ...core.device import StreamingDevice
from .. import Program

_logger = logging.getLogger("controllably.Measure")
_logger.debug(f"Import: OK <{__name__}>")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

COLUMNS = ('Time', 'Displacement', 'Value', 'Factor', 'Baseline', 'Force')
"""Headers for output data from force sensor"""
G = 9.81
"""Acceleration due to Earth's gravity"""

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

    ### Attributes
    - `baseline` (float): baseline readout at which zero newtons is set
    - `calibration_factor` (float): calibration factor of device readout to newtons
    - `displacement` (float): machine displacement
    - `end_stop` (bool): whether the end stop is triggered
    - `home_displacement` (float): starting displacement of home position
    - `precision` (int): number of decimal places to print force value
    - `threshold` (float): force threshold to stop movement
    
    ### Properties
    - `force` (float): force experienced
    - `limits` (np.ndarray): lower and upper limits of movement
    
    ### Methods
    - `clearCache`: clear most recent data and configurations
    - `disconnect`: disconnect from device
    - `getForce`: get the force response
    - `home`: home the actuator
    - `isFeasible`: checks and returns whether the target displacement is feasible
    - `measure`: measure the stress-strain response of sample
    - `move`: move the actuator by desired distance. Alias of `moveBy()` method
    - `moveBy`: move the actuator by desired distance
    - `moveTo`: move the actuator to desired displacement
    - `reset`: reset the device
    - `setThreshold`: set the force threshold for the machine
    - `shutdown`: shutdown procedure for tool
    - `tare`: alias for zero()
    - `stream`: start or stop feedback loop
    - `record`: start or stop data recording
    - `touch`: touch the sample
    - `waitThreshold`: wait for force sensor to reach the force threshold
    - `zero`: set the current reading as baseline (i.e. zero force)
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
        self._logger.addHandler(logging.StreamHandler())
        self.verbose = verbose
        
        self.force_tolerance = force_tolerance
        self.stabilize_timeout = stabilize_timeout
        self._stabilize_start_time = None
        
        self.baseline = 0
        self.calibration_factor = calibration_factor
        self.correction_parameters = correction_parameters
        
        self.displacement = 0
        self.force_threshold = force_threshold
        self.home_displacement = home_displacement
        self.limits = (min(limits), max(limits))
        self.max_speed = max_speed
        self._steps_per_second = steps_per_second
        
        self.end_stop = False
        self._touch_force_threshold: float = touch_force_threshold
        self._touch_timeout : int = 120
        
        self.buffer_df = pd.DataFrame(columns=COLUMNS)
        self.precision = 3
        self._force = 0
        
        # Measurer specific attributes
        self.program: Program|Any|None = None
        self.runs = dict()
        self.n_runs = 0
        self._threads = dict()
        
        # self._connect(port, simulation=kwargs.get('simulation', False))
        # # Category specific attributes
        # # Data logging attributes
        # self.buffer: deque[tuple[NamedTuple, datetime]] = deque(maxlen=MAX_LEN)
        # self.records: deque[tuple[NamedTuple, datetime]] = deque()
        # self.record_event = threading.Event()
        
        # self.connect()
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
        for handler in self._logger.handlers:
            if not isinstance(handler, logging.StreamHandler):
                continue
            handler.setLevel(level)
        return
    
    @property
    def force(self) -> float:
        return round(self._force, self.precision)
    
    @property
    def records_df(self) -> pd.DataFrame:
        """DataFrame of records"""
        return self.buffer_df.copy()
    
    def connect(self):
        """Establish connection with device"""
        self.device.connect()
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
        self.clearCache()
        self.resetFlags()
        self.baseline = 0
        return
    
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = deepcopy(self._default_flags)
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.stream(on=False)
        self.reset()
        self.disconnect()
        return
    
    # Category specific properties and methods
    def clearCache(self):
        """Clear most recent data and configurations"""
        self.flags.pause_feedback = True
        time.sleep(0.1)
        self.buffer_df = pd.DataFrame(columns=COLUMNS)
        self.flags.pause_feedback = False
        return
 
    def getAttributes(self) -> dict:
        """
        Get attributes
        
        Returns:
            dict: Attributes
        """
        relevant = ['correction_parameters', 'baseline', 'calibration_factor', 'force_tolerance', 'stabilize_timeout']
        return {key: getattr(self, key) for key in relevant}
    
    def getForce(self) -> str:
        """
        Get the force response and displacement of actuator
        
        Returns:
            str: device response
        """
        response = self.device.read()
        now = datetime.now()
        try:
            # data: MoveForceData = self.device.processOutput(response)
            # displacement = data.displacement
            # end_stop = data.end_stop
            # value = data.value
            _,_,displacement,end_stop,value = response.split(',')
            displacement = float(displacement)
            end_stop = bool(int(end_stop))
            value = int(value)
        except ValueError:
            return None
        else:
            # value = (value - self.correction_parameters[1]) / self.correction_parameters[0]
            # self._force = (value - self.baseline) / self.calibration_factor * G
            self._force = self._calculate_force(self._correct_value(value)) * G
            self.displacement = displacement
            self.end_stop = end_stop
            over_threshold = (abs(self.force) > abs(self.force_threshold))
            self.flags.threshold = bool(over_threshold)
            if self.verbose:
                print(f"{displacement:.2f} mm | {self.force:.5E} mN | {value:.2f}")
            if self.flags.record:
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
        return self._force
    
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
        except:
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
        except:
            pass
        else:
            displacement = self.waitThreshold(to)
            logger.info(displacement)
            self.device.write(f'G {displacement} {rpm}')
        self.displacement = displacement
        return displacement == to

    def touch(self, 
        force_threshold: float = 0.1, 
        displacement_threshold: float|None = None, 
        speed: float|None = None, 
        from_top: bool = True,
        record: bool = False
    ) -> bool:
        """
        Apply the target force
        
        Args:
            force_threshold (float): target force
            displacement_threshold (float): target displacement
            speed (float): movement speed
            from_top (bool): whether to move from the top or bottom
            
        Returns:
            bool: whether movement is successful (i.e. force threshold is not reached)
        """
        speed = speed or self.max_speed
        
        logger.info('Touching...')
        # if not self.flags.get_feedback:
        #     self.stream(True)
        if abs(round(self.force)) > self._touch_force_threshold:
            # self.stream(False)
            self.zero()
            # self.stream(True)
        
        _threshold = self.force_threshold
        _touch_timeout = self._touch_timeout
        self.force_threshold = self._touch_force_threshold if force_threshold is None else force_threshold
        self._touch_timeout = 3600
        
        if record:
            self.stream(False)
            self.record(True)
        try:
            # touch sample
            self.moveTo(self.limits[0], speed=speed)
            time.sleep(2)
        except Exception as e:
            logger.exception(e)
        else:
            ...
        finally:
            self.force_threshold = _threshold
            self._touch_timeout = _touch_timeout
            time.sleep(2)
        logger.info('In contact')
        if record:
            self.record(False)
            self.stream(True)
        self.flags.threshold = False
        return True
    
    def waitThreshold(self, displacement:float, timeout:float | None = None) -> float:
        """
        Wait for force sensor to reach the threshold

        Args:
            displacement (float): target displacement
            timeout (float|None, optional): timeout duration in seconds. Defaults to None.

        Returns:
            float: actual displacement upon reaching threshold
        """
        timeout = self._touch_timeout if timeout is None else timeout
        start = time.time()
        while self.displacement != displacement:
            time.sleep(0.001)
            if self.force >= abs(self.force_threshold):
                displacement = self.displacement
                self.flags.threshold = True
                logger.warning('Made contact')
                break
            if time.time() - start > timeout:
                logger.warning('Touch timeout')
                break
        return self.displacement
    
    def zero(self, timeout:int = 5):
        """
        Set current reading as baseline (i.e. zero force)
        
        Args:
            timeout (int, optional): duration to wait while zeroing, in seconds. Defaults to 5.
        """
        # if self.flags.record:
        #     logger.warning("Unable to zero while recording.")
        #     logger.warning("Use `record(False)` to stop recording.")
        #     return
        temp_record_state = self.flags.record
        temp_buffer_df = self.buffer_df.copy()
        if self.flags.get_feedback:
            self.stream(False)
        if self.flags.record:
            self.record(False)
        self.reset()
        self.record(True)
        logger.info(f"Zeroing... ({timeout}s)")
        time.sleep(timeout)
        self.record(False)
        self.baseline = self.buffer_df['Value'].mean()
        self.clearCache()
        self.buffer_df = temp_buffer_df.copy()
        logger.info("Zeroing complete.")
        self.record(temp_record_state)
        return
    
    def record(self, on: bool, show: bool = False, clear_cache: bool = False):
        """
        Start or stop data recording

        Args:
            on (bool): whether to start recording data
        """
        self.flags.record = on
        self.flags.get_feedback = on
        self.flags.pause_feedback = False
        self.stream(on=on)
        return
    
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
    
    def _calculate_force(self, value: float) -> float:
        """
        Calculate force from value
        
        Args:
            value (float): Value
            
        Returns:
            float: Force
        """
        return (value-self.baseline)/self.calibration_factor * G
    
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

    def _loop_feedback(self):
        """Loop to constantly read from device"""
        print('Listening...')
        while self.flags.get_feedback:
            if self.flags.pause_feedback:
                continue
            self.getForce()
        print('Stop listening...')
        return

Parallel_ForceActuator = Ensemble.factory(ForceActuator)
