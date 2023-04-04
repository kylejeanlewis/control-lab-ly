# %% -*- coding: utf-8 -*-
"""

"""
# Standard library imports
from __future__ import annotations
import numpy as np

# Local application imports
from ..view_utils import Camera
from .Flir.ax8 import Ax8ThermalCamera
print(f"Import: OK <{__name__}>")

class Thermal(Camera):
    """
    Thermal camera object

    ### Constructor
    Args:
        `ip_address` (str): IP address of thermal camera
        `calibration_unit` (float, optional): calibration from pixels to mm. Defaults to 1.
        `cam_size` (tuple[int], optional): (width, height) of camera output. Defaults to (640,480).
        `rotation` (int, optional): rotation angle for camera feed. Defaults to 180.
    
    ### Properties
    - `ip_address` (str): IP address of thermal camera
    
    ### Methods
    - `disconnect`: disconnect from camera
    """
    _package = __name__
    _placeholder_filename = 'placeholders/infrared_camera.png'
    def __init__(self, 
        ip_address:str, 
        calibration_unit: float = 1, 
        cam_size: tuple[int] = (640,480), 
        rotation:int = 180, 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            ip_address (str): IP address of thermal camera
            calibration_unit (float, optional): calibration from pixels to mm. Defaults to 1.
            cam_size (tuple[int], optional): (width, height) of camera output. Defaults to (640,480).
            rotation (int, optional): rotation angle for camera feed. Defaults to 180.
        """
        super().__init__(calibration_unit=calibration_unit, cam_size=cam_size, rotation=rotation, **kwargs)
        self._connect(ip_address)
        return
    
    # Properties
    @property
    def ip_address(self) -> str:
        return self.connection_details.get('ip_address', '')

    def disconnect(self):
        """Disconnect from camera"""
        try:
            self.feed.stop()
            self.feed.stream.release()
        except AttributeError:
            pass
        self.setFlag(connected=False)
        return
    
    # Protected method(s)
    def _connect(self, ip_address:str, **kwargs):
        """
        Connection procedure for tool
        
        Args:
            ip_address (str): IP address of thermal camera
        """
        self.connection_details['ip_address'] = ip_address
        self.device = Ax8ThermalCamera(ip_address, verbose=True)
        # if self.device.modbus.is_open:
        if True:
            self.feed = self.device.video.stream
            self.setFlag(connected=True)
        return
    
    def _read(self) -> tuple[bool, np.ndarray]:
        """
        Read camera feed to retrieve image

        Returns:
            tuple[bool, np.ndarray]: (whether frame is obtained, frame array)
        """
        return True, self.feed.read()
    

    