# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/1 13:20:00
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
import numpy as np
import pandas as pd
import pkgutil
from threading import Thread
from typing import Optional, Protocol

# Third party imports
import cv2              # pip install opencv-python

# Local application imports
from ..misc import Helper
from .image_utils import Image
print(f"Import: OK <{__name__}>")

DIMENSION_THRESHOLD = 36
ROW_DISTANCE = 30

class Classifier(Protocol):
    def detect(self, frame:np.ndarray, scale:int, neighbors:int, **kwargs) -> dict:
        ...

class Camera(ABC):
    """
    Camera object

    Args:
        calibration_unit (int, optional): calibration of pixels to mm. Defaults to 1.
        cam_size (tuple, optional): width and height of image. Defaults to (640,480).
        rotation (int, optional): rotation of camera feed. Defaults to 0.
    """
    _default_flags: dict[str, bool] = {
        'connected': False,
        'pause_record': False,
        'record': False
    }
    _package: str
    _placeholder_filename: str
    def __init__(self, 
        calibration_unit: float = 1, 
        cam_size: tuple[int] = (640,480), 
        rotation: int = 0
    ):
        self.calibration_unit = calibration_unit
        self.cam_size = cam_size
        self.classifier = None
        self.connection_details = {}
        self.device = None
        self.feed = None
        self.placeholder_image = None
        self.record_folder = ''
        self.record_timeout = None
        self.rotation = rotation
        
        self.flags = self._default_flags.copy() 
        self._threads = {}
        self._set_placeholder()
        pass
    
    def __del__(self):
        self.shutdown()
        return
    
    @abstractmethod
    def _connect(self, *args, **kwargs):
        """
        Connect to the imaging device
        """
        self.connection_details = {}
        self.device = None
        self.setFlag(connected=True)
        return
   
    @abstractmethod
    def _read(self) -> tuple[bool, np.ndarray]:
        """
        Read camera feed

        Returns:
            bool, array: True if frame is obtained; array of frame
        """
    
    @abstractmethod
    def disconnect(self):
        """
        Release the camera feed
        """
        self.setFlag(connected=False)
    
    def annotateAll(self, 
        df:pd.DataFrame, 
        image: Optional[Image] = None, 
        frame: Optional[np.ndarray] = None    
    ) -> tuple[dict[str,tuple[int]], Image]:
        """
        Annotate all targets

        Args:
            df (pd.DataFrame): dataframe of details of detected targets
            frame (array): frame array

        Returns:
            dict, Image: dictionary of (target index, center positions); image
        """
        data = {}
        if (frame is None) == (image is None):
            raise Exception('Please input either image or frame.')
        elif frame is not None:
            image = Image(frame)
            
        for index in range(len(df)):
            dimensions = df.loc[index, ['x','y','w','h']].to_list()
            x,y,w,h = dimensions
            if w*h >= DIMENSION_THRESHOLD**2:                       # Compare area to threshold
                image.annotate(index, (x,y,w,h), inplace=True)
                data[f'C{index+1}'] = (int(x+(w/2)), int(y+(h/2)))  # Center of target
        return data, image

    def detect(self, image:Image, scale:int, neighbors:int) -> pd.DataFrame:
        """
        Detect targets

        Args:
            image (Image): image to detect from
            scale (int): scale at which to detect targets
            neighbors (int): minimum number of neighbors for targets

        Raises:
            Exception: Classifier not loaded

        Returns:
            pd.DataFrame: dataframe of detected targets
        """
        if self.classifier is None:
            raise Exception('Please load a classifier first.')
        image.grayscale(inplace=True)
        detected_data = self.classifier.detect(frame=image.frame, scale=scale, neighbors=neighbors)
        return self._data_to_df(detected_data)
    
    def loadClassifier(self, classifier:Classifier):
        """
        Load target classifier

        Args:
            classifier (Classifier): desired classifier
        """
        # try:
        self.classifier = classifier
        # except SystemError:
        #     print('Please select a classifier.')
        return

    def isConnected(self) -> bool:
        """
        Check whether the camera is connected

        Returns:
            bool: whether the camera is connected
        """
        if not self.flags.get('connected', False):
            print(f"{self.__class__} is not connected.")
        return self.flags.get('connected', False)
    
    def resetFlags(self):
        self.flags = self._default_flags.copy()
        return
    
    def setFlag(self, **kwargs):
        """
        Set a flag's truth value

        Args:
            `name` (str): label
            `value` (bool): flag value
        """
        if not all([type(v)==bool for v in kwargs.values()]):
            raise ValueError("Ensure all assigned flag values are boolean.")
        for key, value in kwargs.items():
            self.flags[key] = value
        return
    
    def shutdown(self):
        """
        Close the camera
        """
        self.disconnect()
        cv2.destroyAllWindows()
        self.resetFlags()
        return
    
    def toggleRecord(self, on:bool, folder:str = '', timeout:Optional[int] = None):
        """
        Toggle record

        Args:
            on (bool): whether to start recording frames
            folder (str, optional): folder to save to. Defaults to ''.
            timeout (int, optional): number of seconds to record. Defaults to None.
        """
        self.setFlag(record=on)
        if on:
            # Ensure only one record thread at a time
            if 'record_loop' in self._threads:
                self._threads['record_loop'].join()
            
            self.record_folder = folder
            self.record_timeout = timeout
            thread = Thread(target=self._loop_record)
            thread.start()
            self._threads['record_loop'] = thread
        else:
            self._threads['record_loop'].join()
        return
 
    # Image handling
    def decodeImage(self, array:np.ndarray) -> Image:
        """
        Decode byte array of image

        Args:
            array (bytes): byte array of image

        Returns:
            Image: image of decoded byte array
        """
        frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
        return Image(frame)
    
    def encodeImage(self, 
        image: Optional[Image] = None, 
        frame: Optional[np.ndarray] = None, 
        extension: str = '.png'
    ) -> bytes:
        """
        Encode image into byte array

        Args:
            image (Image, optional): image object to be encoded. Defaults to None.
            frame (array, optional): frame array to be encoded. Defaults to None.
            extension (str, optional): image format to encode to. Defaults to '.png'.

        Raises:
            Exception: Input needs to be an Image or frame array

        Returns:
            bytes: byte representation of image/frame
        """
        if (frame is None) == (image is None):
            raise Exception('Please input either image or frame.')
        elif image is not None:
            return image.encode(extension)
        return cv2.imencode(extension, frame)[1].tobytes()
    
    def getImage(self, 
        crosshair: bool = False, 
        resize: bool = False
    ) -> tuple[bool, Image]:
        """
        Get image from camera feed

        Args:
            crosshair (bool, optional): whether to overlay crosshair on image. Defaults to False.
            resize (bool, optional): whether to resize the image. Defaults to False.

        Returns:
            bool, Image: True if image is obtained; image object
        """
        ret = False
        image = self.placeholder_image
        try:
            ret, frame = self._read()
        except AttributeError:
            pass
        if ret:
            image = Image(frame)
            if resize:
                image.resize(self.cam_size, inplace=True)
            image.rotate(self.rotation, inplace=True)
        if crosshair:
            image.crosshair(inplace=True)
        return ret, image

    def loadImage(self, filename:str) -> Image:
        """
        Load image from file

        Args:
            filename (str): filename of image

        Returns:
            Image: file image
        """
        frame = cv2.imread(filename)
        return Image(frame)
    
    def saveImage(self, 
        image: Optional[Image] = None, 
        frame: Optional[np.ndarray] = None, 
        filename: str = ''
    ) -> bool:
        """
        Save image to file

        Args:
            image (Image, optional): image object to be encoded. Defaults to None.
            frame (array, optional): frame array to be encoded. Defaults to None.
            filename (str, optional): filename to save to. Defaults to 'image.png'.

        Raises:
            Exception: Input needs to be an Image or frame array

        Returns:
            bool: True if successfully saved
        """
        if not len(filename):
            now = datetime.now().strftime("%Y%m%d_%H-%M-%S")
            filename = f'image{now}.png'
        
        if (frame is None) == (image is None):
            raise Exception('Please input either image or frame.')
        elif image is not None:
            return image.save(filename)
        return cv2.imwrite(filename, frame)
    
    # Protected method(s)
    def _data_to_df(self, data:dict) -> pd.DataFrame:
        """
        Convert data dictionary to dataframe

        Args:
            data (dict): dictionary of data

        Returns:
            pd.DataFrame: dataframe of data
        """
        df = pd.DataFrame(data)
        df.rename(columns={0: 'x', 1: 'y', 2: 'w', 3: 'h'}, inplace=True)
        df.sort_values(by='y', ascending=True, inplace=True)
        df.reset_index(inplace=True, drop=True)
        differences = df['y'].diff()[1:]
        row_numbers = [1]
        for diff in differences: 
            # If diff in y-coordinates > 30, assign next row (adjustable)
            row = (row_numbers[-1] + 1) if diff > ROW_DISTANCE else row_numbers[-1]
            row_numbers.append(row)
        df['row'] = row_numbers
        df.sort_values(by=['row','x'], ascending=[True,True], inplace=True) 
        df.reset_index(inplace = True, drop = True)
        return df
    
    def _loop_record(self):
        """
        Record loop to constantly get and save image frames
        """
        start_message = f'Recording...' if self.record_timeout is None else f'Recording... ({self.record_timeout}s)'
        print(start_message)
        timestamps = []
        # frames = []
        frame_num = 0
        folder = Helper.create_folder(self.record_folder, 'frames')
        
        start = datetime.now()
        while self.flags['record']:
            if self.flags['pause_record']:
                continue
            now = datetime.now()
            _, image = self.getImage()
            self.saveImage(image, filename=f'{folder}/frames/frame_{frame_num:05}.png')
            timestamps.append(now)
            # frames.append(image.frame)
            frame_num += 1
            
            # Timer check
            if self.record_timeout is not None and (now - start).seconds > self.record_timeout:
                break
        end = datetime.now()
        
        # for i,frame in enumerate(frames):
        #     self.saveImage(frame=frame, filename=f'{folder}/frames/frame_{i:05}.png')
        # frame_num = len(frames)
        # del frames
        
        duration = end - start
        print('Stop recording...')
        print(f'\nDuration: {str(duration)}')
        print(f'\nFrames recorded: {frame_num}')
        print(f'\nAverage FPS: {frame_num/duration.seconds}')
        df = pd.DataFrame({'frame_num': [i for i in range(frame_num)], 'timestamp': timestamps})
        df.to_csv(f'{folder}/timestamps.csv')
        return
    
    def _set_placeholder(self, 
        filename: str = '', 
        img_bytes: Optional[bytes] = None, 
        resize: bool = False
    ):
        """
        Gets placeholder image for camera, if not connected

        Args:
            filename (str, optional): name of placeholder image file. Defaults to ''.
            img_bytes (bytes, optional): byte representation of placeholder image. Defaults to None.
            resize (bool, optional): whether to resize the image. Defaults to False.

        Returns:
            Image: image of placeholder
        """
        image = None
        if not len(filename) and img_bytes is None:
            img_bytes = pkgutil.get_data(self._package, self._placeholder_filename)
        if len(filename):
            image = self.loadImage(filename)
        elif type(img_bytes) == bytes:
            array = np.asarray(bytearray(img_bytes), dtype="uint8")
            image = self.decodeImage(array)
        
        if resize:
            image.resize(self.cam_size, inplace=True)
        self.placeholder_image = image
        return
 