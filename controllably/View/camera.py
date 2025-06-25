# -*- coding: utf-8 -*-
""" 
This module provides a Camera class for handling camera feed

## Classes:
    `Camera`: Camera class for handling camera feed
    
<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
from collections import deque
from copy import deepcopy
from datetime import datetime
import logging
import queue
import threading
import time
from types import SimpleNamespace
from typing import Any, Callable, Iterable, Mapping

# Third party imports
import cv2              # pip install opencv-python
import numpy as np

# Local application imports
from .placeholder import PLACEHOLDER

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)

class Camera:
    """ 
    Camera class for handling camera feed
    
    ### Constructor:
        `connection_details` (dict, optional): connection details for the device. Defaults to None.
        `init_timeout` (int, optional): timeout for initialization. Defaults to 1.
        `buffer_size` (int, optional): size of the buffer. Defaults to 2000.
        `simulation` (bool, optional): whether to simulate the camera feed. Defaults to False.
        `verbose` (bool, optional): verbosity of the class. Defaults to False.
        
    ### Attributes and properties:
        `placeholder` (np.ndarray): Placeholder image
        `transforms` (list[tuple[Callable[[np.ndarray,Any], np.ndarray], Iterable|None, Mapping|None]]): List of transformations
        `callbacks` (list[tuple[Callable[[np.ndarray,Any], np.ndarray], Iterable|None, Mapping|None]]): List of callbacks
        `connection` (Any|None): Connection to the device
        `connection_details` (dict): Connection details for the device
        `flags` (SimpleNamespace): Flags for the device
        `init_timeout` (int): Timeout for initialization
        `buffer` (deque): Buffer for storing frames
        `data_queue` (queue.Queue): Queue for storing data
        `show_event` (threading.Event): Event for showing the stream
        `stream_event` (threading.Event): Event for streaming
        `threads` (dict): Threads for streaming and processing data
        `verbose` (bool): Verbosity of class
        `feed` (cv2.VideoCapture): Video feed
        `is_connected` (bool): Whether the device is connected
        `verbose` (bool): Verbosity of class
        `frame_rate` (int|float): Frame rate of camera feed
        `frame_size` (tuple[int,int]): Frame size of camera feed
        
    ### Methods:
        `checkDeviceConnection`: Check the connection to the device
        `connect`: Connect to the device
        `connectFeed`: Connect to the camera feed
        `disconnect`: Disconnect from the device
        `disconnectFeed`: Disconnect from the camera feed
        `setFrameRate`: Set the frame rate of camera feed
        `setFrameSize`: Set the resolution of camera feed
        `decodeBytesToFrame`: Decode byte array of image
        `encodeFrameToBytes`: Encode image into byte array
        `loadImageFile`: Load an image from file
        `saveFrame`: Save image to file
        `saveFramesToVideo`: Save frames to video file
        `transformFrame`: Transform the frame
        `processFrame`: Process the frame
        `getFrame`: Get image from camera feed
        `show`: Show image in window
        `checkDeviceBuffer`: Check the connection buffer
        `clear`: Clear the input and output buffers
        `read`: Read data from the device
        `showStream`: Show the stream
        `startStream`: Start the stream
        `stopStream`: Stop the stream
        `stream`: Toggle the stream
    """
    
    _default_flags: SimpleNamespace = SimpleNamespace(verbose=False, connected=False, simulation=False)
    def __init__(self, 
        *, 
        connection_details: dict|None = None, 
        init_timeout: int = 1, 
        buffer_size: int = 2000,
        simulation:bool = False, 
        verbose:bool = False, 
        **kwargs
    ):
        """ 
        Initialize the camera object
        
        Args:
            connection_details (dict, optional): connection details for the device. Defaults to None.
            init_timeout (int, optional): timeout for initialization. Defaults to 1.
            buffer_size (int, optional): size of the buffer. Defaults to 2000.
            simulation (bool, optional): whether to simulate the camera feed. Defaults to False.
            verbose (bool, optional): verbosity of the class. Defaults to False.
        """
        # Camera attributes
        self._feed = cv2.VideoCapture()
        self.placeholder = self.decodeBytesToFrame(np.asarray(bytearray(PLACEHOLDER), dtype="uint8"))
        self.transforms: list[tuple[Callable[[np.ndarray,Any], np.ndarray], Iterable|None, Mapping|None]] = []
        self.callbacks: list[tuple[Callable[[np.ndarray,Any], np.ndarray], Iterable|None, Mapping|None]] = []
        self.transforms.append((cv2.cvtColor, (cv2.COLOR_BGR2RGB,), None))
        if 'transforms' in kwargs:
            self.transforms.extend(kwargs['transforms'])
        
        # Connection attributes
        self.connection: Any|None = None
        self.connection_details = dict() if connection_details is None else connection_details
        self.flags = deepcopy(self._default_flags)
        self.init_timeout = init_timeout
        self.flags.simulation = simulation
        
        # Streaming attributes
        self.buffer = deque(maxlen=buffer_size)
        self.data_queue = queue.Queue()
        self.show_event = threading.Event()
        self.stream_event = threading.Event()
        self.threads = dict()
        
        # Logging attributes
        self._logger = logger.getChild(f"{self.__class__.__name__}.{id(self)}")
        self.verbose = verbose
        return
    
    def __del__(self):
        self.disconnect()
        return
    
    def __enter__(self):
        """Context manager enter method"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit method"""
        self.disconnect()
        return False
    
    @property
    def feed(self) -> cv2.VideoCapture:
        """Video feed"""
        return self._feed
    @feed.setter
    def feed(self, value: cv2.VideoCapture):
        assert isinstance(value, cv2.VideoCapture)
        self._feed = value
        return
    
    @property
    def is_connected(self) -> bool:
        """Whether the device is connected"""
        connected = self.flags.connected if self.flags.simulation else self.checkDeviceConnection()
        return connected
    
    @property
    def verbose(self) -> bool:
        """Verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        level = logging.DEBUG if value else logging.INFO
        CustomLevelFilter().setModuleLevel(self._logger.name, level)
        return
    
    @property
    def frame_rate(self) -> int|float:
        """Frame rate of camera feed"""
        return self.feed.get(cv2.CAP_PROP_FPS)
    
    @property
    def frame_size(self) -> tuple[int,int]:
        """Frame size of camera feed"""
        width = int(self.feed.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.feed.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (width,height)
    
    # Connection methods
    def checkDeviceConnection(self) -> bool:
        """
        Check the connection to the device
        
        Returns:
            bool: whether the device is connected
        """
        return self.feed.isOpened()
    
    def connect(self):
        """Connect to the device"""
        return self.connectFeed()
    
    def connectFeed(self):
        """Connect to the camera feed"""
        # if self.is_connected:
        #     return
        try:
            feed_source = self.connection_details.get('feed_source', 0)
            feed_api = self.connection_details.get('feed_api', None)
            self._logger.info(f'Opening feed: {feed_source}')
            success = self.feed.open(feed_source, feed_api)
        except Exception as e:
            self._logger.error(f"Failed to connect to {self.connection_details}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Connected to {self.connection_details}")
            time.sleep(self.init_timeout)
            width = int(self.feed.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.feed.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.setFrameSize((width,height))
        self.flags.connected = success
        self.getFrame(latest=True)
        return
    
    def disconnect(self):
        """Disconnect from the device"""
        return self.disconnectFeed()
    
    def disconnectFeed(self):
        """Disconnect from the camera feed"""
        if not self.is_connected:
            return
        try:
            self.feed.release()
        except Exception as e:
            self._logger.error(f"Failed to disconnect from {self.connection_details}")
            self._logger.debug(e)
        else:
            self._logger.info(f"Disconnected from {self.connection_details}")
        self.flags.connected = False
        return
    
    def setFrameRate(self, fps:int|float = 30.0):
        """
        Set the frame rate of camera feed
        
        Args:
            fps (int|float, optional): frame rate in frames per second. Defaults to 30.0.
        """
        assert isinstance(fps, (int, float)), "Please provide a number for fps"
        self.feed.set(cv2.CAP_PROP_FPS, fps)
        self._logger.info(f"Set frame rate to {fps} fps")
        return
    
    def setFrameSize(self, size:Iterable[int] = (10_000,10_000)):
        """
        Set the resolution of camera feed

        Args:
            size (tuple[int], optional): width and height of feed in pixels. Defaults to (10000,10000).
        """
        assert len(size)==2, "Please provide a tuple of (w,h) in pixels"
        self.feed.set(cv2.CAP_PROP_FRAME_WIDTH, size[0])
        self.feed.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
        return
    
    # Image handling
    @staticmethod
    def decodeBytesToFrame(bytearray: bytes) -> np.ndarray:
        """
        Decode byte array of image

        Args:
            bytearray (bytes): byte array of image

        Returns:
            np.ndarray: image array of decoded byte array
        """
        return cv2.imdecode(bytearray, cv2.IMREAD_COLOR)
    
    @staticmethod
    def encodeFrameToBytes(frame: np.ndarray, extension: str = '.png') -> bytes:
        """
        Encode image into byte array

        Args:
            frame (np.ndarray): image array to be encoded
            extension (str, optional): image format to encode to. Defaults to '.png'.

        Returns:
            bytes: byte array of image
        """
        ret, frame_bytes = cv2.imencode(extension, frame)
        return frame_bytes.tobytes()
    
    @staticmethod
    def loadImageFile(filename: str) -> np.ndarray:
        """
        Load an image from file

        Args:
            filename (str): image filename

        Returns:
            np.ndarray: image array from file
        """
        return cv2.imread(filename)
    
    @staticmethod
    def saveFrame(frame: np.ndarray, filename: str|None = None) -> bool:
        """
        Save image to file

        Args:
            frame (np.ndarray): frame array to be saved
            filename (str, optional): filename to save to. Defaults to 'image.png'.

        Returns:
            bool: whether the image array is successfully saved
        """
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        if filename is None:
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'image-{now}.png'
        return cv2.imwrite(filename, frame)
    
    @staticmethod
    def saveFramesToVideo(frames: Iterable[np.ndarray], fps:int|float, filename: str|None = None) -> bool:
        """
        Save frames to video file

        Args:
            frames (list[np.ndarray]): list of frames to be saved
            fps (int|float): frame rate of video
            filename (str, optional): filename to save to. Defaults to 'video.mp4'.

        Returns:
            bool: whether the video is successfully saved
        """
        if filename is None:
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'video-{now}.mp4'
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        height, width, _ = frames[0].shape
        out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
        for frame in frames:
            out.write(frame)
        out.release()
        return True
    
    @staticmethod
    def transformFrame(
        frame: np.ndarray,
        transforms: Iterable[tuple[Callable[[np.ndarray,Any], np.ndarray], Iterable|None, Mapping|None]]|None = None,
    ) -> np.ndarray:
        """
        Transform the frame
        
        Args:
            frame (np.ndarray): image array to be transformed
            transforms (list[tuple[Callable[[np.ndarray,Any], np.ndarray], Iterable|None, Mapping|None]], optional): list of transformations. Defaults to None.
            
        Returns:
            np.ndarray: transformed image array
        """
        transformed_frame = frame
        transforms = transforms or []
        for transform, args, kwargs in transforms:
            args = args or []
            kwargs = kwargs or {}
            transformed_frame = transform(transformed_frame, *args, **kwargs)
        return transformed_frame
    
    @staticmethod
    def processFrame(
        frame: np.ndarray,
        callbacks: Iterable[tuple[Callable[[np.ndarray,Any], np.ndarray], Iterable|None, Mapping|None]]|None = None,
    ) -> np.ndarray:
        """ 
        Process the frame
        
        Args:
            frame (np.ndarray): image array to be processed
            callbacks (list[tuple[Callable[[np.ndarray,Any], np.ndarray], Iterable|None, Mapping|None], optional): list of callbacks. Defaults to None.
            
        Returns:
            np.ndarray: processed image array
        """
        processed_frame = deepcopy(frame)
        callbacks = callbacks or []
        for callback, args, kwargs in callbacks:
            args = args or []
            kwargs = kwargs or {}
            processed_frame = callback(processed_frame, *args, **kwargs)
        return processed_frame
    
    def getFrame(self, latest: bool = False) -> tuple[bool, np.ndarray]:
        """
        Get image from camera feed

        Args:
            latest (bool, optional): whether to get the latest image. Default to False.

        Returns:
            tuple[bool, np.ndarray]: (whether an image is obtained, image array)
        """
        ret, frame = self.read()
        if latest:
            ret, frame = self.read()
        transformed_frame = self.transformFrame(frame, self.transforms)
        return ret, transformed_frame
    
    def show(self, transforms: list[Callable[[np.ndarray], np.ndarray]]|None = None):
        """
        Show image in window

        Args:
            transforms (list[Callable[[np.ndarray], np.ndarray]], optional): list of transformations. Defaults to None.
        """
        self.transforms = transforms or self.transforms
        cv2.destroyAllWindows()
        self.startStream(show=True, buffer=self.buffer)
        return
    
    # IO methods
    def checkDeviceBuffer(self) -> bool:
        """
        Check the connection buffer
        
        Returns:
            bool: whether the device buffer is available
        """
        ...
        raise NotImplementedError
    
    def clear(self):
        """Clear the input and output buffers"""
        self.stopStream()
        self.buffer = deque()
        self.data_queue = queue.Queue()
        return
    
    def read(self) -> tuple[bool, np.ndarray]:
        """
        Read data from the device
        
        Returns:
            tuple[bool, np.ndarray]: (whether data is received, data)
        """
        ret = False
        frame = self.placeholder
        try:
            ret, frame = self.feed.read() # Replace with specific implementation
        except KeyboardInterrupt:
            self._logger.debug("Received keyboard interrupt")
            self.disconnect()
        except Exception as e: # Replace with specific exception
            self._logger.debug("Failed to receive data")
            self._logger.exception(e)
        if frame is None:
            frame = self.placeholder
        if self.flags.simulation:
            ret = True
        return ret, frame

    # Streaming methods
    def showStream(self, on: bool):
        """
        Show the stream
        
        Args:
            on (bool): whether to show the stream
        """
        _ = self.show_event.set() if on else self.show_event.clear()
        return
    
    def startStream(self,  
        buffer: deque|None = None,
        *, 
        show: bool = False,
        sync_start: threading.Barrier|None = None
    ):
        """
        Start the stream
        
        Args:
            buffer (deque, optional): buffer to store frames. Defaults to None.
            show (bool, optional): whether to show the stream. Defaults to False.
            sync_start (threading.Barrier, optional): synchronization barrier. Defaults to
        """
        sync_start = sync_start or threading.Barrier(2, timeout=2)
        assert isinstance(sync_start, threading.Barrier), "Ensure sync_start is a threading.Barrier"
        
        self.stream_event.set()
        self.threads['stream'] = threading.Thread(
            target=self._loop_stream, 
            kwargs=dict(sync_start=sync_start), 
            daemon=True
        )
        self.threads['process'] = threading.Thread(
            target=self._loop_process_data, 
            kwargs=dict(buffer=buffer, sync_start=sync_start), 
            daemon=True
        )
        self.showStream(show)
        self.threads['stream'].start()
        self.threads['process'].start()
        return
    
    def stopStream(self):
        """Stop the stream"""
        self.stream_event.clear()
        self.showStream(False)
        for thread in self.threads.values():
            _ = thread.join() if isinstance(thread, threading.Thread) else None
        return
    
    def stream(self, 
        on:bool, 
        buffer: deque|None = None, 
        *,
        sync_start:threading.Barrier|None = None,
        **kwargs
    ):
        """
        Toggle the stream
        
        Args:
            on (bool): whether to start the stream
            buffer (deque, optional): buffer to store frames. Defaults to None.
            sync_start (threading.Barrier, optional): synchronization barrier. Defaults to None.
        """
        return self.startStream(buffer=buffer, sync_start=sync_start, **kwargs) if on else self.stopStream()
    
    def _loop_process_data(self, buffer: deque|None = None, sync_start:threading.Barrier|None = None):
        """ 
        Process data loop
        
        Args:
            buffer (deque, optional): buffer to store frames. Defaults to None.
            sync_start (threading.Barrier, optional): synchronization barrier. Defaults to None.
        """
        if buffer is None:
            buffer = self.buffer
        assert isinstance(buffer, deque), "Ensure buffer is a deque"
        if isinstance(sync_start, threading.Barrier):
            sync_start.wait()
        
        while self.stream_event.is_set():
            try:
                frame, now = self.data_queue.get(timeout=5)
                transformed_frame = self.transformFrame(frame=frame, transforms=self.transforms)
                self.processFrame(transformed_frame, self.callbacks)
                buffer.append((transformed_frame, now))
                self.data_queue.task_done()
            except queue.Empty:
                time.sleep(0.01)
                continue
            except KeyboardInterrupt:
                self.stream_event.clear()
                break
            else:
                if not self.show_event.is_set():
                    continue
                cv2.imshow('output', cv2.cvtColor(transformed_frame, cv2.COLOR_RGB2BGR))  
                if (cv2.waitKey(1) & 0xFF) == ord('q'):
                    self.stream_event.clear()
                    break
        time.sleep(1)
        
        while self.data_queue.qsize() > 0:
            try:
                frame, now = self.data_queue.get(timeout=1)
                transformed_frame = self.transformFrame(frame=frame, transforms=self.transforms)
                self.processFrame(transformed_frame, self.callbacks)
                buffer.append((transformed_frame, now))
                self.data_queue.task_done()
            except queue.Empty:
                break
            except KeyboardInterrupt:
                break
            else:
                if not self.show_event.is_set():
                    continue
                cv2.imshow('output', cv2.cvtColor(transformed_frame, cv2.COLOR_RGB2BGR))
                if (cv2.waitKey(1) & 0xFF) == ord('q'):
                    self.stream_event.clear()
                    break
        self.data_queue.join()
        return
    
    def _loop_stream(self, sync_start:threading.Barrier|None = None):
        """
        Stream loop
        
        Args:
            sync_start (threading.Barrier, optional): synchronization barrier. Defaults to None.
        """
        if isinstance(sync_start, threading.Barrier):
            sync_start.wait()
        
        time_step = 1/self.frame_rate
        while self.stream_event.is_set():
            try:
                start_time = time.perf_counter()
                ret,frame = self.read()
                if ret:
                    now = datetime.now()
                    self.data_queue.put((frame, now), block=False)
                    delay = time.perf_counter()-start_time
                    time.sleep(max(time_step-delay, 0))       # match the frame rate
            except queue.Full:
                time.sleep(0.01)
                continue
            except KeyboardInterrupt:
                self.stream_event.clear()
                break
        return
