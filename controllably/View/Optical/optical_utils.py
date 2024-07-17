# %% -*- coding: utf-8 -*-
"""
This module holds the class for optical cameras.

Classes:
    Optical (Camera)
"""
# Standard library imports
from __future__ import annotations
import logging
import numpy as np

# Third party imports
import cv2 # pip install opencv-python

# Local application imports
from ..view_utils import Camera

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class Optical(Camera):
    """
    Optical provides methods for controlling a optical web camera

    ### Constructor
    Args:
        `cam_index` (int, optional): camera index. Defaults to 0.
        `calibration_unit` (float, optional): calibration from pixels to mm. Defaults to 1.
        `cam_size` (tuple[int], optional): (width, height) of camera output. Defaults to (640,480).
    
    ### Properties
    - `cam_index` (int): camera index
    
    ### Methods
    - `disconnect`: disconnect from camera
    - `setResolution`: set the resolution of camera feed
    """
    
    _package = __name__
    _placeholder_filename = 'placeholders/optical_camera.png'
    def __init__(self, 
        cam_index: int = 0, 
        calibration_unit: float = 1, 
        cam_size: tuple[int] = (640,480), 
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            cam_index (int, optional): camera index. Defaults to 0.
            calibration_unit (float, optional): calibration from pixels to mm. Defaults to 1.
            cam_size (tuple[int], optional): (width, height) of camera output. Defaults to (640,480).
        """
        super().__init__(calibration_unit=calibration_unit, cam_size=cam_size, **kwargs)
        self._connect(cam_index)
        return
    
    # Properties
    @property
    def cam_index(self) -> str:
        return self.connection_details.get('cam_index', '')
    
    def disconnect(self):
        """Disconnect from camera"""
        try:
            self.feed.release()
        except AttributeError:
            pass
        self.setFlag(connected=False)
        return
    
    def setResolution(self, size:tuple[int] = (10000,10000)):
        """
        Set the resolution of camera feed

        Args:
            size (tuple[int], optional): width and height of feed in pixels. Defaults to (10000,10000).
        """
        self.feed.set(cv2.CAP_PROP_FRAME_WIDTH, size[0])
        self.feed.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
        return

    # Protected method(s)
    def _connect(self, cam_index:int = 0, **kwargs):
        """
        Connection procedure for tool
        
        Args:
            cam_index (int, optional): camera index. Defaults to 0.
        """
        self.connection_details['cam_index'] = cam_index
        self.feed = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
        self.setResolution()
        self.setFlag(connected=True)
        return
    
    def _read(self) -> tuple[bool, np.ndarray]:
        """
        Read camera feed to retrieve image

        Returns:
            tuple[bool, np.ndarray]: (whether frame is obtained, frame array)
        """
        return self.feed.read()
    