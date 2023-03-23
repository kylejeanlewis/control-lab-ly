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

# Third party imports
import cv2 # pip install opencv-python

# Local application imports
from ..view_utils import Camera
print(f"Import: OK <{__name__}>")

class Optical(Camera):
    """
    Optical camera object

    Args:
        cam_index (int, optional): address of camera. Defaults to 0.
        calibration_unit (int, optional): calibration of pixels to mm. Defaults to 1.
        cam_size (tuple, optional): width and height of image. Defaults to (640,480).
        rotation (int, optional): rotation of camera feed. Defaults to 0.
    """
    _package = __name__
    _placeholder_filename = 'placeholders/optical_camera.png'
    def __init__(self, cam_index:int = 0, **kwargs):
        super().__init__(**kwargs)
        self._connect(cam_index)
        return
    
    # Properties
    @property
    def cam_index(self):
        return self.connection_details.get('cam_index', '')
    
    def setResolution(self, size:tuple[int] = (10000,10000)):
        """
        Set resolution of camera feed

        Args:
            size (tuple, optional): width and height of feed in pixels. Defaults to (10000,10000).
        """
        self.feed.set(cv2.CAP_PROP_FRAME_WIDTH, size[0])
        self.feed.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
        return

    # Protected method(s)
    def _connect(self, cam_index=0, **kwargs):
        """
        Connect to the imaging device
        
        Args:
            cam_index (int, optional): address of camera. Defaults to 0.
        """
        self.connection_details['cam_index'] = cam_index
        self.feed = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
        self.setResolution()
        self.setFlag(connected=True)
        return
    
    def _read(self) -> tuple[bool, np.ndarray]:
        """
        Read camera feed

        Returns:
            bool, array: True if frame is obtained; array of frame
        """
        return self.feed.read()
    
    def _release(self):
        """
        Release the camera feed
        """
        try:
            self.feed.release()
        except AttributeError:
            pass
        return
    