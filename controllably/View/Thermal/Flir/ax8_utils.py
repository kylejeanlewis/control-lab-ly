# %% -*- coding: utf-8 -*-
"""
WIP: This module holds the class for thermal cameras by FLIR.

Classes:
    AX8 (Camera)
"""
# Standard library imports
from __future__ import annotations
import numpy as np
from typing import Optional

# Third party imports
import cv2                                  # pip install opencv-python
# from imutils.video import VideoStream       # pip install imutils
from pyModbusTCP.client import ModbusClient # pip install pyModbusTCP

# Local application imports
from ...view_utils import Camera
from .ax8_lib import SpotmeterRegs, decode_from_modbus, encode_to_modbus
print(f"Import: OK <{__name__}>")

class AX8(Camera):
    """
    AX8 provides methods for controlling AX8 thermal cameras from FLIR

    ### Constructor
    Args:
        `ip_address` (str): IP address of thermal camera
        `calibration_unit` (float, optional): calibration from pixels to mm. Defaults to 1.
        `cam_size` (tuple[int], optional): (width, height) of camera output. Defaults to (640,480).
        `rotation` (int, optional): rotation angle for camera feed. Defaults to 0.
        `encoding` (str, optional): video encoding format. Defaults to "avc".
        `overlay` (bool, optional): whether to have an overlay. Defaults to False.
        `verbose` (bool, optional): verbosity of class. Defaults to True.

    ### Attributes
    - `rtsp_url` (str): stream for real time stream
    - `spotmeter_parameters` (dict[str,bool]): reflected temperature, emissivity, and distance for spotmeter)
    
    ### Properties
    - `ip_address` (str): IP address of thermal camera
    - `modbus` (ModbusClient): alias for `device`
    
    ### Methods
    - `configureSpotmeter`: set the temperature calculation parameters when enabling a spotmeter
    - `disableSpotmeter`: disable spotmeters with given instance IDs
    - `disconnect`: disconnect from camera
    - `enableSpotmeter`: enable spotmeters with given instance IDs, for up to 5 individual spotmeters
    - `getCutline`: get a 1D array of temperature values along the given cutline, either along given X or Y
    - `getInternalTemperature`: retrieve the camera's internal temperature
    - `getSpotPositions`: get the positions for specified spotmeters
    - `getSpotTemperatures`: get temperature readings for specified spotmeters
    - `isConnected`: checks and returns whether the device is connected
    - `toggleVideo`: toggle between opening or closing video feed
    """
    
    _package = __name__.split('Thermal')[0]+'Thermal'
    _placeholder_filename = 'placeholders/infrared_camera.png'
    _default_spotmeter_parameters: dict[str, bool] = {
        'reflected_temperature': 298.0,
        'emissivity': 0.95,
        'distance': 0.5
    }
    def __init__(self,
        ip_address: str, 
        calibration_unit: float = 1, 
        cam_size: tuple[int] = (640,480), 
        rotation:int = 180, 
        encoding: str = "avc", 
        overlay: bool = False, 
        verbose: bool = True,
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            ip_address (str): IP address of thermal camera
            calibration_unit (float, optional): calibration from pixels to mm. Defaults to 1.
            cam_size (tuple[int], optional): (width, height) of camera output. Defaults to (640,480).
            rotation (int, optional): rotation angle for camera feed. Defaults to 0.
            encoding (str, optional): video encoding format. Defaults to "avc".
            overlay (bool, optional): whether to have an overlay. Defaults to False.
            verbose (bool, optional): verbosity of class. Defaults to True.
        """
        super().__init__(calibration_unit=calibration_unit, cam_size=cam_size, rotation=rotation, **kwargs)
        self.rtsp_url = ''
        self.spotmeter_parameters = self._default_spotmeter_parameters.copy()
        
        self.verbose = verbose
        self._connect(ip_address=ip_address, encoding=encoding, overlay=overlay)
        return
    
    # Properties
    @property
    def ip_address(self) -> str:
        return self.connection_details.get('ip_address', '')

    @property
    def modbus(self) -> ModbusClient:
        return self.device
    
    def configureSpotmeter(self,
        reflected_temperature: Optional[float] = None,
        emissivity: Optional[float] = None,
        distance: Optional[float] = None
    ):
        """
        Set the temperature calculation parameters when enabling a spotmeter

        Args:
            reflected_temperature (Optional[float], optional): reflected temperature in Kelvin. Defaults to None.
            emissivity (Optional[float], optional): emissivity between 0.001 and 1. Defaults to None.
            distance (Optional[float], optional): distance in metres, at least 0.2. Defaults to None.
        """
        params = dict(
            reflected_temperature = reflected_temperature,
            emissivity = emissivity,
            distance = distance
        )
        for key,value in params.items():
            if value is None:
                continue
            self.spotmeter_parameters[key] = value
        return

    def disableSpotmeter(self, instances:list):
        """
        Disable spotmeters with given instance IDs

        Args:
            instances (list): list of instance IDs
        """
        self.modbus.unit_id = SpotmeterRegs.UNIT_ID.value
        for instance in instances:
            base_reg_addr = (instance*4000)
            self.modbus.write_multiple_registers(base_reg_addr + SpotmeterRegs.ENABLE_SPOTMETER.value, encode_to_modbus(False)) 
        return

    def disconnect(self):
        """Disconnect from camera"""
        try:
            # self.feed.stop()
            # self.feed.stream.release()
            self.feed.release()
        except AttributeError:
            pass
        self.setFlag(connected=False)
        return

    def enableSpotmeter(self, instances:dict[int, tuple[int,int]], use_local_params:bool = True):
        """
        Enable spotmeters with given instance IDs, for up to 5 individual spotmeters
        Spotmeter position range is from (2,2) to (78,58). The lower left corner is pixel (2,58).
        
        Args:
            instances (dict[int, tuple[int,int]]): dictionary of instance and position tuples, {instance_id: (spot_x, spot_y)}
            use_local_params (bool, optional): Each spotmeter can use its own set of local parameters. If set to false, the global parameters will be used by the camera. Defaults to True.
        """
        self.modbus.unit_id = SpotmeterRegs.UNIT_ID.value
        for instance, position in instances.items():
            base_reg_addr = (instance*4000)
            if use_local_params:
                self.modbus.write_multiple_registers(base_reg_addr + SpotmeterRegs.ENABLE_LOCAL_PARAMS.value, encode_to_modbus(True))
                self.modbus.write_multiple_registers(base_reg_addr + SpotmeterRegs.REFLECTED_TEMP.value, encode_to_modbus(self.spotmeter_parameters['reflected_temperature']))
                self.modbus.write_multiple_registers(base_reg_addr + SpotmeterRegs.EMISSIVITY.value, encode_to_modbus(self.spotmeter_parameters['emissivity']))
                self.modbus.write_multiple_registers(base_reg_addr + SpotmeterRegs.DISTANCE.value, encode_to_modbus(self.spotmeter_parameters['distance']))
            self.modbus.write_multiple_registers(base_reg_addr + SpotmeterRegs.SPOT_X_POSITION.value, encode_to_modbus(position[0]))
            self.modbus.write_multiple_registers(base_reg_addr + SpotmeterRegs.SPOT_Y_POSITION.value, encode_to_modbus(position[1]))
            self.modbus.write_multiple_registers(base_reg_addr + SpotmeterRegs.ENABLE_SPOTMETER.value, encode_to_modbus(True))
        return

    def getCutline(self, 
        x: Optional[int] = None, 
        y: Optional[int] = None,
        unit_celsius: bool = True,
        reflected_temperature: Optional[float] = None,
        emissivity: Optional[float] = None,
        distance: Optional[float] = None
    ) -> Optional[np.ndarray]:
        """
        Get a 1D array of temperature values along the given cutline, either along given X or Y

        Args:
            x (Optional[int], optional): cutline position along X. Defaults to None.
            y (Optional[int], optional): cutline position along Y. Defaults to None.
            unit_celsius (bool, optional): whether to return the temperatures in Celsius. Defaults to True.
            reflected_temperature (Optional[float], optional): reflected temperature in Kelvin. Defaults to None.
            emissivity (Optional[float], optional): emissivity between 0.001 and 1. Defaults to None.
            distance (Optional[float], optional): distance in metres, at least 0.2. Defaults to None.

        Returns:
            Optional[np.ndarray]: array of temperature values along cutline
        """
        if not any([x,y]) or all([x,y]):
            print("Please only input value for one of 'x' or 'y'")
            return
        if any([reflected_temperature, emissivity, distance]):
            self.configureSpotmeter(reflected_temperature, emissivity, distance)
        
        length = 60 if y is None else 80
        values = []
        for p in range(0,length,5):
            instances = {i+1: (x,p+i) for i in range(5)} if y is None else {i+1: (p+i,y) for i in range(5)}
            self.enableSpotmeter(instances=instances)
            temperatures = self.getSpotTemperatures([1,2,3,4,5], unit_celsius=unit_celsius)
            values.append(temperatures.values())
        return np.array(values)
    
    def getInternalTemperature(self) -> float:
        """
        Retrieve the camera's internal temperature

        Returns:
            float: camera temperature
        """
        # self.modbus.unit_id(SpotmeterRegs.UNIT_ID)
        self.modbus.unit_id = 1
        camera_temperature = self.modbus.read_holding_registers(1017, 2)[0:2]
        camera_temperature = decode_from_modbus(camera_temperature, is_int=False)[0]
        if self.verbose:
            print(f"Internal Camera Temperature: {camera_temperature:.2}K")
        return camera_temperature
    
    def getSpotPositions(self, instances:list) -> dict[int, tuple[int,int]]:
        """
        Get the positions for specified spotmeters

        Args:
            instances (list): list of instance IDs

        Returns:
            dict[int, tuple[int,int]]: dictionary of spotmeter positions, {instance_id: (spot_x, spot_y)}
        """
        self.modbus.unit_id = SpotmeterRegs.UNIT_ID.value
        values = {}
        for instance in instances:
            base_reg_addr = (instance*4000)
            spot_x = self.modbus.read_holding_registers(base_reg_addr + SpotmeterRegs.SPOT_X_POSITION.value, 6)[-2:]
            spot_y = self.modbus.read_holding_registers(base_reg_addr + SpotmeterRegs.SPOT_Y_POSITION.value, 6)[-2:]
            spot_x = decode_from_modbus(spot_x, is_int=True)[0]
            spot_y = decode_from_modbus(spot_y, is_int=True)[0]
            values[instance] = (spot_x, spot_y)
        return values
    
    def getSpotTemperatures(self, instances:list, unit_celsius:bool = True) -> dict[int, float]:
        """
        Get temperature readings for specified spotmeters

        Args:
            instances (list): list of instance IDs
            unit_celsius (bool, optional): whether to return the temperatures in Celsius. Defaults to True.

        Returns:
            dict[int, float]: dictionary of spotmeter temperatures, {instance_id: temperature}
        """
        self.modbus.unit_id = SpotmeterRegs.UNIT_ID.value
        values = {}
        for instance in instances:
            base_reg_addr = (instance*4000)
            temperature = self.modbus.read_holding_registers(base_reg_addr + SpotmeterRegs.SPOT_TEMPERATURE.value, 6)[-2:]
            temperature = decode_from_modbus(temperature, is_int=False)[0]
            value = temperature - 273.15 if unit_celsius else temperature
            values[instance] = value
        return values
    
    def isConnected(self) -> bool:
        """
        Checks and returns whether the device is connected

        Returns:
            bool: whether the device is connected
        """
        connected = self.modbus.is_open
        self.setFlag(connected=connected)
        return connected
    
    def toggleVideo(self):
        """
        Toggle between opening or closing video feed
        """
        # if self.feed.stream.isOpened():
        if self.feed.isOpened():
            print("Closing the feed..")
            self.disconnect()
        else:
            print("Opening the feed..")
            # self.feed = VideoStream(self.rtsp_url).start()
            self.feed = cv2.VideoCapture(self.rtsp_url)
        return
    
    # Protected methods
    def _connect(self, ip_address:str, encoding:str, overlay:bool):
        """
        Connection procedure for tool
        
        Args:
            ip_address (str): IP address of thermal camera
            encoding (str): video encoding format
            overlay (bool): whether to have an overlay
        """
        modbus = ModbusClient()
        self.connection_details = dict(ip_address=ip_address, encoding=encoding, overlay=overlay)
        try:
            modbus = ModbusClient(
                host=ip_address, port=502,
                auto_open=True, auto_close=False
            )
        except Exception as e:
            print(f"Unable to establish Modbus TCP! Error: {e}")
        else:
            self.device = modbus
            self.getInternalTemperature()
            self.setFlag(connected=True)
            if self.verbose:
                print(f"Established Modbus TCP at: {modbus.host}")
            
            self.rtsp_url = self._get_rtsp_url(ip_address, encoding, overlay)
            print(f"Opening camera feed at {self.rtsp_url}")
            # self.feed = VideoStream(self.rtsp_url).start()
            self.feed = cv2.VideoCapture(self.rtsp_url)
            # if self.feed.frame is None:
            #     self.feed.stop() # Probably unnecessary since it is a daemon
            #     raise AttributeError(f"Could not open stream at {self.rtsp_url}!")
        self.device = modbus
        return
    
    def _get_rtsp_url(self, ip_address:str, encoding:str, overlay:bool) -> str:
        """
        Get the RTSP URL for the feed

        Args:
            ip_address (str): IP address of thermal camera
            encoding (str): video encoding format
            overlay (bool): whether to have an overlay

        Returns:
            str: RTSP URL
        """
        encoding = 'avc' if encoding not in ("avc", "mjpg", "mpeg4") else encoding
        overlay_tag = '' if overlay else "?overlay=off"
        url = f'rtsp://{ip_address}/{encoding}{overlay_tag}'
        return url
    
    def _read(self) -> tuple[bool, np.ndarray]:
        """
        Read camera feed to retrieve image

        Returns:
            tuple[bool, np.ndarray]: (whether frame is obtained, frame array)
        """
        # return True, self.feed.read()
        return self.feed.read()
