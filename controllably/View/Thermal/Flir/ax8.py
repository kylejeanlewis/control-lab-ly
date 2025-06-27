# -*- coding: utf-8 -*-
""" 
This module contains the AX8 camera class

Attributes:
    BYTE_SIZE (int): size of data packet
    MODBUS_PORT (int): Modbus port
    
## Classes:
    `AX8`: AX8 camera class
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import struct
from typing import Sequence

# Third party imports
import numpy as np
from pyModbusTCP.client import ModbusClient # pip install pyModbusTCP

# Local application imports
from ...camera import Camera
from .ax8_api.ax8_lib import SpotMeterRegs

BYTE_SIZE = 4
MODBUS_PORT = 502

class AX8(Camera):
    """ 
    AX8 camera class
    
    ### Constructor:
        `host` (str): camera IP address
        `port` (int, optional): Modbus port. Defaults to 502.
        `encoding` (str, optional): feed encoding. Defaults to 'avc'.
        `overlay` (bool, optional): whether to overlay data. Defaults to False.
        `connection_details` (dict, optional): connection details. Defaults to None.
        `init_timeout` (int, optional): initial timeout. Defaults to 1.
        `simulation` (bool, optional): whether to simulate the camera. Defaults to False.
        `verbose` (bool, optional): whether to print debug messages. Defaults to False.
        
    ### Attributes and properties:
        `host` (str): camera IP address
        `port` (int): Modbus port
        `modbus` (ModbusClient): Modbus connection
        `connection` (ModbusClient): Modbus connection
        `spotmeter_parameters` (dict): spotmeter parameters
        
    ### Methods:
        `checkDeviceConnection`: check if the camera and feed are connected
        `connect`: connect to camera and feed
        `connectCamera`: connect to camera
        `connectFeed`: connect to feed
        `disconnect`: disconnect from camera and feed
        `disconnectCamera`: disconnect from camera
        `disconnectFeed`: disconnect from feed
        `configureSpotmeter`: set the temperature calculation parameters when enabling a spotmeter
        `disableSpotmeter`: disable spotmeters with given instance IDs
        `enableSpotmeter`: enable spotmeters with given instance IDs
        `getCutline`: get a 1D array of temperature values along the given cutline
        `getInternalTemperature`: get the internal temperature of the camera
        `getSpotPositions`: get the positions for specified spotmeters
        `getSpotTemperatures`: get temperature readings for specified spotmeters
        `invertPalette`: invert the palette of the feed
        `decodeModbus`: parse values from reading modbus holding registers
        `encodeModbus`: format value to create data packet
    """
    
    def __init__(self, 
        host: str,
        *, 
        port: int = MODBUS_PORT,
        encoding: str = 'avc',
        overlay: bool = False,
        connection_details:dict|None = None, 
        init_timeout:int = 1, 
        simulation:bool = False, 
        verbose:bool = False, 
        **kwargs
    ):
        """ 
        Initialize the AX8 object
        
        Args:
            host (str): camera IP address
            port (int, optional): Modbus port. Defaults to 502.
            encoding (str, optional): feed encoding. Defaults to 'avc'.
            overlay (bool, optional): whether to overlay data. Defaults to False.
            connection_details (dict, optional): connection details. Defaults to None.
            init_timeout (int, optional): initial timeout. Defaults to 1.
            simulation (bool, optional): whether to simulate the camera. Defaults to False.
            verbose (bool, optional): whether to print debug messages. Defaults to False.
        """
        super().__init__(
            connection_details=connection_details, init_timeout=init_timeout,
            simulation=simulation, verbose=verbose,
            **kwargs
        )
        self.connection_details['host'] = host
        self.connection_details['port'] = port
        self.connection_details['encoding'] = encoding
        self.connection_details['overlay'] = overlay
        self.connection_details['feed_source'] = self._get_rtsp_url(host, encoding, overlay)
        
        self.connection = ModbusClient()
        self.spotmeter_parameters = dict()
        return

    @property
    def host(self) -> str:
        """Camera IP address"""
        return self.connection_details["host"]
    @host.setter
    def host(self, value: str):
        self.connection_details["host"] = value
        return
    
    @property
    def port(self) -> int:
        """Modbus port"""
        return self.connection_details["port"]
    @port.setter
    def port(self, value: int):
        self.connection_details["port"] = value
        return
    
    @property
    def modbus(self) -> ModbusClient:
        """Modbus connection"""
        return self.connection
    @modbus.setter
    def modbus(self, value: ModbusClient):
        assert isinstance(value, ModbusClient), f"Expected ModbusClient, got {type(value)}"
        self.connection = value
        return
    
    def checkDeviceConnection(self) -> bool:
        modbus_status = self.modbus.is_open
        feed_status = self.feed.isOpened()
        if not modbus_status:
            self._logger.warning(f"Modbus not connected: {self.connection_details['host']}")
        if not feed_status:
            self._logger.warning(f"Feed not connected: {self.connection_details['feed_source']}")
        return modbus_status and feed_status
    
    def connect(self):
        self.connectCamera()
        self.connectFeed()
        return
    
    def connectCamera(self):
        """Connect to camera"""
        # Connect to camera via Modbus
        self._logger.info('Connecting to camera...')
        self.modbus.host = self.host
        self.modbus.port = self.port
        success = self.modbus.open()
        if success:
            self.getInternalTemperature()
        return
    
    def connectFeed(self):
        self._logger.info('Opening feed...')
        host = self.connection_details['host']
        encoding = self.connection_details.get('encoding', 'avc')
        overlay = self.connection_details.get('overlay', False)
        self.connection_details['feed_source'] = self._get_rtsp_url(host, encoding, overlay)
        return super().connect()
    
    def disconnect(self):
        self.disconnectCamera()
        self.disconnectFeed()
        return
    
    def disconnectCamera(self):
        """Disconnect from camera"""
        self._logger.info('Disconnecting from camera...')
        self.modbus.close()
        return
    
    def disconnectFeed(self):
        self._logger.info('Closing feed...')
        return super().disconnect()
    
    def configureSpotmeter(self,
        reflected_temperature: float|None = None,
        emissivity: float|None = None,
        distance: float|None = None
    ):
        """
        Set the temperature calculation parameters when enabling a spotmeter

        Args:
            reflected_temperature (float|None, optional): reflected temperature in Kelvin. Defaults to None.
            emissivity (float|None, optional): emissivity between 0.001 and 1. Defaults to None.
            distance (float|None, optional): distance in metres, at least 0.2. Defaults to None.
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
        self.modbus.unit_id = SpotMeterRegs.UNIT_ID.value
        for instance in instances:
            base_reg_addr = (instance*4000)
            self.modbus.write_multiple_registers(base_reg_addr + SpotMeterRegs.ENABLE_SPOTMETER.value, self.encodeModbus(False)) 
        return
    
    def enableSpotmeter(self, instances:dict[int, tuple[int,int]], use_local_params:bool = True):
        """
        Enable spotmeters with given instance IDs, for up to 5 individual spotmeters
        Spotmeter position range is from (2,2) to (78,58). The lower left corner is pixel (2,58).
        
        Args:
            instances (dict[int, tuple[int,int]]): dictionary of instance and position tuples, {instance_id: (spot_x, spot_y)}
            use_local_params (bool, optional): Each spotmeter can use its own set of local parameters. If set to false, the global parameters will be used by the camera. Defaults to True.
        """
        self.modbus.unit_id = SpotMeterRegs.UNIT_ID.value
        for instance, position in instances.items():
            base_reg_addr = (instance*4000)
            if use_local_params:
                self.modbus.write_multiple_registers(base_reg_addr + SpotMeterRegs.ENABLE_LOCAL_PARAMS.value, self.encodeModbus(True))
                self.modbus.write_multiple_registers(base_reg_addr + SpotMeterRegs.REFLECTED_TEMP.value, self.encodeModbus(self.spotmeter_parameters['reflected_temperature']))
                self.modbus.write_multiple_registers(base_reg_addr + SpotMeterRegs.EMISSIVITY.value, self.encodeModbus(self.spotmeter_parameters['emissivity']))
                self.modbus.write_multiple_registers(base_reg_addr + SpotMeterRegs.DISTANCE.value, self.encodeModbus(self.spotmeter_parameters['distance']))
            self.modbus.write_multiple_registers(base_reg_addr + SpotMeterRegs.SPOT_X_POSITION.value, self.encodeModbus(position[0]))
            self.modbus.write_multiple_registers(base_reg_addr + SpotMeterRegs.SPOT_Y_POSITION.value, self.encodeModbus(position[1]))
            self.modbus.write_multiple_registers(base_reg_addr + SpotMeterRegs.ENABLE_SPOTMETER.value, self.encodeModbus(True))
        return
    
    def getCutline(self, 
        x: int|None = None, 
        y: int|None = None,
        unit_celsius: bool = True,
        reflected_temperature: float|None = None,
        emissivity: float|None = None,
        distance: float|None = None
    ) -> np.ndarray|None:
        """
        Get a 1D array of temperature values along the given cutline, either along given X or Y

        Args:
            x (Optional[int], optional): cutline position along X. Defaults to None.
            y (Optional[int], optional): cutline position along Y. Defaults to None.
            unit_celsius (bool, optional): whether to return the temperatures in Celsius. Defaults to True.
            reflected_temperature (float|None, optional): reflected temperature in Kelvin. Defaults to None.
            emissivity (float|None, optional): emissivity between 0.001 and 1. Defaults to None.
            distance (float|None, optional): distance in metres, at least 0.2. Defaults to None.

        Returns:
            np.ndarray|None: array of temperature values along cutline
        """
        if not any([x,y]) or all([x,y]):
            self._logger.warning("Please only input value for one of 'x' or 'y'")
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
        Get the internal temperature of the camera
        
        Returns:
            float: internal temperature in Kelvin
        """
        self.modbus.unit_id = 1
        out = self.modbus.read_holding_registers(1017, 2)[:2]
        camera_temperature = self.decodeModbus(out, is_int=False)[0]
        self._logger.info(f"Internal Camera Temperature: {camera_temperature:.2f}K")
        return camera_temperature
    
    def getSpotPositions(self, instances:list) -> dict[int, tuple[int,int]]:
        """
        Get the positions for specified spotmeters

        Args:
            instances (list): list of instance IDs

        Returns:
            dict[int, tuple[int,int]]: dictionary of spotmeter positions, {instance_id: (spot_x, spot_y)}
        """
        self.modbus.unit_id = SpotMeterRegs.UNIT_ID.value
        values = {}
        for instance in instances:
            base_reg_addr = (instance*4000)
            spot_x = self.modbus.read_holding_registers(base_reg_addr + SpotMeterRegs.SPOT_X_POSITION.value, 6)[-2:]
            spot_y = self.modbus.read_holding_registers(base_reg_addr + SpotMeterRegs.SPOT_Y_POSITION.value, 6)[-2:]
            spot_x = self.decodeModbus(spot_x, is_int=True)[0]
            spot_y = self.decodeModbus(spot_y, is_int=True)[0]
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
        self.modbus.unit_id = SpotMeterRegs.UNIT_ID.value
        values = {}
        for instance in instances:
            base_reg_addr = (instance*4000)
            temperature = self.modbus.read_holding_registers(base_reg_addr + SpotMeterRegs.SPOT_TEMPERATURE.value, 6)[-2:]
            temperature = self.decodeModbus(temperature, is_int=False)[0]
            value = temperature - 273.15 if unit_celsius else temperature
            values[instance] = value
        return values
    
    def invertPalette(self, blue_cold:bool = True):
        """
        Invert the palette of the feed
        
        Args:
            blue_cold (bool, optional): whether to set the palette to blue cold. Defaults to True.
        """
        self.modbus.unit_id = int("67", base=16)
        base_reg_addr = 4000
        attr_id = 2
        address = base_reg_addr + (attr_id-1)*20
        is_blue_cold = self.modbus.read_holding_registers(address, 2)[1]
        data = self.encodeModbus(not is_blue_cold)
        self.modbus.write_multiple_registers(address, data)
        return

    @staticmethod
    def decodeModbus(data: Sequence[int], is_int:bool) -> tuple:
        """
        Parse values from reading modbus holding registers

        Args:
            data (list[int]): data packet
            is_int (bool): whether the expected value is an integer (as opposed to a float)

        Returns:
            tuple: unpacked values
        """
        form = ">i" if is_int else ">f"
        value = data[0].to_bytes(2, 'big') + data[1].to_bytes(2, 'big')
        return struct.unpack(form, value)

    @staticmethod
    def encodeModbus(value:bool|float|int) -> list[int]:
        """
        Format value to create data packet

        Args:
            value (Union[bool, float, int]): target value

        Returns:
            list[int]: data packet
        """
        if isinstance(value, bool):
            return [1,int(value)]
        form = '>i' if isinstance(value,int) else '>f'
        packed_big = struct.pack(form, value)
        big_endian = [int(packed_big[:2].hex(), base=16), int(packed_big[-2:].hex(), base=16)]
        little_endian = big_endian[::-1]
        return [BYTE_SIZE] + little_endian + [BYTE_SIZE] + big_endian

    @staticmethod
    def _get_rtsp_url(host:str, encoding:str='avc', overlay:bool=False) -> str:
        """
        Generate RTSP feed URL
        
        Args:
            host (str): camera IP address
            encoding (str, optional): feed encoding. Defaults to 'avc'.
            overlay (bool, optional): whether to overlay data. Defaults to False.
            
        Returns:
            str: RTSP feed URL
        """
        assert encoding in ("avc", "mjpg", "mpeg4"), "Choose encoding from 'avc', 'mjpg', 'mpeg4'"
        overlay_tag = '' if overlay else "?overlay=off"
        return f'rtsp://{host}/{encoding}{overlay_tag}'
