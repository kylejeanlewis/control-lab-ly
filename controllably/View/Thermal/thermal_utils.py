# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/1 13:20:00
@author: Chang Jie

Notes / actionables:
- 
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

    Args:
        ip_address (str): IP address of thermal camera
        calibration_unit (int, optional): calibration of pixels to mm. Defaults to 1.
        cam_size (tuple, optional): width and height of image. Defaults to (640,480).
        rotation (int, optional): rotation of camera feed. Defaults to 0.
    """
    _package = __name__
    _placeholder_filename = 'placeholders/infrared_camera.png'
    def __init__(self, ip_address:str, rotation:int = 180, **kwargs):
        super().__init__(rotation=rotation, **kwargs)
        self._connect(ip_address)
        return
    
    # Properties
    @property
    def ip_address(self):
        return self.connection_details.get('ip_address', '')
    
    # Protected method(s)
    def _connect(self, ip_address:str, **kwargs):
        """
        Connect to the imaging device
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
        Read camera feed

        Returns:
            bool, array: True if frame is obtained; array of frame
        """
        return True, self.feed.read()
    
    def _release(self):
        """
        Release the camera feed
        """
        try:
            self.feed.stop()
            self.feed.stream.release()
        except AttributeError:
            pass
        return
    