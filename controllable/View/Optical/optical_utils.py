# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/1 13:20:00
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
import pkgutil

# Third party imports
import cv2 # pip install opencv-python

# Local application imports
from ..view_utils import Camera
print(f"Import: OK <{__name__}>")

class Optical(Camera):
    """
    Optical camera object

    Args:
        calibration_unit (int, optional): calibration of pixels to mm. Defaults to 1.
        cam_size (tuple, optional): width and height of image. Defaults to (640,480).
        rotation (int, optional): rotation of camera feed. Defaults to 0.
    """
    def __init__(self, cam_index=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connect(cam_index)
        
        img_bytes = pkgutil.get_data(__name__, 'placeholders/optical_camera.png')
        self._set_placeholder(img_bytes=img_bytes)
        return
    
    def _connect(self, cam_index=0):
        """
        Connect to the imaging device
        """
        self.feed = cv2.VideoCapture(cam_index)
        self._flags['isConnected'] = True
        return
