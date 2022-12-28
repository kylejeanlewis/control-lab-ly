# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/1 13:20:00
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
import pkgutil

# Local application imports
from ..view_utils import Camera
from .Flir.ax8.ax8 import Ax8ThermalCamera
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
    def __init__(self, ip_address:str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ip_address = ip_address
        self.rotation = 180
        self._connect()
        
        img_bytes = pkgutil.get_data(__name__, 'placeholders/infrared_camera.png')
        self._set_placeholder(img_bytes=img_bytes)
        return
    
    def _connect(self):
        """
        Connect to the imaging device
        """
        self.device = Ax8ThermalCamera(self.ip_address, verbose=False)
        if self.device.modbus.is_open:
            self.feed = self.device.video.stream
            self._flags['isConnected'] = True
        return
    
    def _read(self):
        """
        Read camera feed

        Returns:
            bool, array: True if frame is obtained; array of frame
        """
        return self.device.modbus.is_open, self.feed.read()
    
    def _release(self):
        """
        Release the camera feed
        """
        if self.device.modbus.is_open:
            self.feed.stop()
            self.feed.stream.release()
        return
    