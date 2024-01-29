# %% -*- coding: utf-8 -*-
"""
This module holds the base class for camera tools.

Classes:
    Camera (ABC)

Other constants and variables:
    DIMENSION_THRESHOLD (int)
    ROW_DISTANCE (int)
"""
# Standard library imports
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
import numpy as np
import pandas as pd
import pkgutil
from threading import Thread
from typing import Optional, Protocol, Callable

# Third party imports
import cv2              # pip install opencv-python

# Local application imports
from ..misc import Helper
from . import image as Image
print(f"Import: OK <{__name__}>")

DIMENSION_THRESHOLD = 36
"""Minimum width in pixels of target for detection"""
ROW_DISTANCE = 30
"""Number of pixels between rows of detected targets"""

class Classifier(Protocol):
    def detect(self, frame:np.ndarray, scale:int, neighbors:int, **kwargs) -> dict:
        ...

class Camera(ABC):
    """
    Abstract Base Class (ABC) for Camera objects (i.e. tools that capture images).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Args:
        `calibration_unit` (float, optional): calibration from pixels to mm. Defaults to 1.
        `cam_size` (tuple[int], optional): (width, height) of camera feed. Defaults to (640,480).
        `rotation` (int, optional): rotation angle for camera feed. Defaults to 0.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
    
    ### Attributes
    - `calibration_unit` (float): calibration from pixels to mm
    - `cam_size` (tuple[int], optional): (width, height) of camera feed
    - `classifier` (Classifier): image classifier object
    - `connection_details` (dict): dictionary of connection details (e.g. COM port / IP address)
    - `device` (Callable): device object that communicates with physical tool
    - `feed` (Callable): connection to image feed
    - `flags` (dict[str, bool]): keywords paired with boolean flags
    - `placeholder_image` (np.ndarray): placeholder image for when there is no feed available
    - `record_folder` (str): filepath at which to store images and data
    - `record_timeout` (int): number of seconds to record images for
    - `rotation` (int): rotation angle for camera feed (multiples of 90 degrees)
    - `verbose` (bool): verbosity of class
    
    ### Methods
    #### Abstract
    - `disconnect`: disconnect from device
    - `_connect`: connection procedure for tool
    - `_read`: read camera feed to retrieve image
    #### Public
    - `annotateAll`: annotate all detected targets
    - `connect`: establish connection with device
    - `decodeImage`: decode byte array of image
    - `detect`: perform image detection
    - `encodeImage`: encode image into byte array
    - `getImage`: retrieve image from camera feed
    - `isConnected`: checks and returns whether the device is connected
    - `loadClassifier`: load the desired image classifier
    - `loadImage`: load an image from file
    - `resetFlags`: reset all flags to class attribute `_default_flags`
    - `saveImage`: save image to file
    - `setFlag`: set flags by using keyword arguments
    - `shutdown`: shutdown procedure for tool
    - `toggleRecord`: start or stop image capture and recording
    - `view`: view the camera feed
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
        rotation: int = 0,
        verbose: bool = False,
        **kwargs
    ):
        """
        Instantiate the class

        Args:
            calibration_unit (float, optional): calibration from pixels to mm. Defaults to 1.
            cam_size (tuple[int], optional): (width, height) of camera output. Defaults to (640,480).
            rotation (int, optional): rotation angle for camera feed. Defaults to 0.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
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
        self.verbose = verbose
        self._threads = {}
        self._set_placeholder()
        pass
    
    def __del__(self):
        self.shutdown()
        return
    
    @abstractmethod
    def disconnect(self):   # TODO
        """Disconnect from device"""
        self.setFlag(connected=False)
    
    @abstractmethod
    def _connect(self, *args, **kwargs):
        """Connection procedure for tool"""
        self.connection_details = {}
        self.device = None
        self.setFlag(connected=True)
        return
   
    @abstractmethod
    def _read(self) -> tuple[bool, np.ndarray]: # TODO
        """
        Read camera feed to retrieve image

        Returns:
            tuple[bool, np.ndarray]: (whether frame is obtained, frame array)
        """
    
    def annotateAll(self, 
        df: pd.DataFrame, 
        frame: np.ndarray
    ) -> tuple[dict[str,tuple[int]], np.ndarray]:
        """
        Annotate all detected targets

        Args:
            df (pd.DataFrame): dataframe of detected targets detail
            frame (np.ndarray): image array

        Returns:
            tuple[dict[str,tuple[int]], np.ndarray]: ({target index: center positions}, image array)
        """
        data = {}
        for index in range(len(df)):
            dimensions = df.loc[index, ['x','y','w','h']].to_list()
            x,y,w,h = dimensions
            if w*h >= DIMENSION_THRESHOLD**2:                       # Compare area to threshold
                frame = Image.annotate(frame=frame, index=index, dimensions=(x,y,w,h))
                data[f'C{index+1}'] = (int(x+(w/2)), int(y+(h/2)))  # Center of target
        return data, frame
    
    def connect(self):
        """Establish connection with device"""
        return self._connect(**self.connection_details)

    def detect(self, frame:np.ndarray, scale:int, neighbors:int) -> pd.DataFrame:
        """
        Perform image detection

        Args:
            frame (np.ndarray): image array to detect from
            scale (int): scale at which to detect targets
            neighbors (int): minimum number of neighbors for targets

        Raises:
            RuntimeError: Please load a classifier first.

        Returns:
            pd.DataFrame: dataframe of detected targets
        """
        if self.classifier is None:
            raise RuntimeError('Please load a classifier first.')
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected_data = self.classifier.detect(frame=frame, scale=scale, neighbors=neighbors)
        return self._data_to_df(detected_data)
    
    def isConnected(self) -> bool:
        """
        Checks and returns whether the device is connected

        Returns:
            bool: whether the device is connected
        """
        if not self.flags.get('connected', False):
            print(f"{self.__class__} is not connected.")
        return self.flags.get('connected', False)
    
    def loadClassifier(self, classifier:Classifier):
        """
        Load the desired image classifier

        Args:
            classifier (Classifier): desired image classifier
        """
        self.classifier = classifier
        return

    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = self._default_flags.copy()
        return
    
    def setFlag(self, **kwargs):
        """
        Set flags by using keyword arguments

        Kwargs:
            key, value: (flag name, boolean) pairs
        """
        if not all([type(v)==bool for v in kwargs.values()]):
            raise ValueError("Ensure all assigned flag values are boolean.")
        self.flags.update(kwargs)
        return
    
    def shutdown(self):
        """Shutdown procedure for tool"""
        self.disconnect()
        cv2.destroyAllWindows()
        self.resetFlags()
        return
    
    def toggleRecord(self, on:bool, folder:str = '', timeout:Optional[int] = None):
        """
        Start or stop image capture and recording

        Args:
            on (bool): whether to start recording frames
            folder (str, optional): folder to save to. Defaults to ''.
            timeout (Optional[int], optional): number of seconds to record. Defaults to None.
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
    def decodeImage(self, array:bytes) -> np.ndarray:
        """
        Decode byte array of image

        Args:
            array (bytes): byte array of image

        Returns:
            np.ndarray: image array of decoded byte array
        """
        return cv2.imdecode(array, cv2.IMREAD_COLOR)
    
    def encodeImage(self, frame:np.ndarray, extension:str = '.png') -> bytes:
        """
        Encode image into byte array

        Args:
            frame (np.ndarray): image array to be encoded
            extension (str, optional): image format to encode to. Defaults to '.png'.

        Returns:
            bytes: byte array of image
        """
        return cv2.imencode(extension, frame)[1].tobytes()
    
    def getImage(self, 
        crosshair: bool = False, 
        resize: bool = False
    ) -> tuple[bool, np.ndarray]:
        """
        Get image from camera feed

        Args:
            crosshair (bool, optional): whether to overlay crosshair on image. Defaults to False.
            resize (bool, optional): whether to resize the image. Defaults to False.

        Returns:
            tuple[bool, np.ndarray]: (whether an image is obtained, image array)
        """
        ret = False
        frame = self.placeholder_image
        try:
            ret, frame = self._read()
        except AttributeError:
            pass
        if ret:
            if resize:
                frame = cv2.resize(frame, self.cam_size)
            frame = Image.rotate(frame=frame, angle=self.rotation)
        if crosshair:
            frame = Image.crosshair(frame=frame)
        return ret, frame

    def loadImage(self, filename:str) -> np.ndarray:
        """
        Load an image from file

        Args:
            filename (str): image filename

        Returns:
            np.ndarray: image array from file
        """
        return cv2.imread(filename)
    
    def saveImage(self, 
        frame: np.ndarray, 
        filename: str = 'image.png'
    ) -> bool:
        """
        Save image to file

        Args:
            frame (np.ndarray): frame array to be saved
            filename (str, optional): filename to save to. Defaults to 'image.png'.

        Returns:
            bool: whether the image array is successfully saved
        """
        if filename == 'image.png':
            now = datetime.now().strftime("%Y%m%d_%H-%M-%S")
            filename = f'image{now}.png'
        return cv2.imwrite(filename, frame)
    
    def view(self, process_func:Optional[Callable] = None, **kwargs):
        """
        View the camera feed

        Args:
            process_func (Callable, optional): callable process function. Defaults to None.
        """
        cv2.destroyAllWindows()
        thread = Thread(
            target = self._loop_display, 
            name = "CameraViewer", 
            args = [process_func], 
            kwargs = kwargs,
            daemon = True
        )
        thread.start()
        return
    
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
    
    def _loop_display(self, process_func:Optional[Callable] = None, **kwargs):
        """
        Loop to display video stream

        Args:
            process_func (Optional[Callable], optional): callable process function. Defaults to None.
        """
        while True:
            if not self.isConnected():
                print("Stream is not open.")
                return
            # ret,frame = self._read()
            ret,frame = self.getImage(resize=True)
            # if callable(process_func):
            #     frame = process_func(frame, **kwargs)
            if frame is None or not ret:
                continue
            cv2.putText(frame, "Press 'q' to close", (5, 15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255))
            cv2.imshow('output', frame)
            key = cv2.waitKey(1) & 0xFF     
            if key == ord('q'):
                break
        return
    
    def _loop_record(self):
        """Loop to constantly get and save image frames"""
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
            _, frame = self.getImage()
            self.saveImage(frame=frame, filename=f'{folder}/frames/frame_{frame_num:05}.png')
            timestamps.append(now)
            # frames.append(frame)
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
        Sets placeholder image for camera, if not  camera is not connected

        Args:
            filename (str, optional): name of placeholder image file. Defaults to class attribute `_placeholder_filename`.
            img_bytes (Optional[bytes], optional): byte array of placeholder image. Defaults to None.
            resize (bool, optional): whether to resize the image. Defaults to False.
        """
        frame = None
        if not len(filename) and img_bytes is None:
            img_bytes = pkgutil.get_data(self._package, self._placeholder_filename)
        if len(filename):
            frame = self.loadImage(filename)
        elif type(img_bytes) == bytes:
            array = np.asarray(bytearray(img_bytes), dtype="uint8")
            frame = self.decodeImage(array)
        if resize:
            frame = cv2.resize(frame, self.cam_size)
        self.placeholder_image = frame
        return
 