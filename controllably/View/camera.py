# -*- coding: utf-8 -*-
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
from typing import Any, Callable, Iterable, Mapping, Sequence

# Third party imports
import cv2              # pip install opencv-python
import numpy as np

# Local application imports
from .placeholder import PLACEHOLDER

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

class Camera:
    _default_flags: SimpleNamespace = SimpleNamespace(verbose=False, connected=False, simulation=False)
    def __init__(self, 
        *, 
        connection_details:dict|None = None, 
        init_timeout:int = 1, 
        simulation:bool = False, 
        verbose:bool = False, 
        **kwargs
    ):
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
        self.buffer = deque()
        self.data_queue = queue.Queue()
        self.show_event = threading.Event()
        self.stream_event = threading.Event()
        self.threads = dict()
        
        # Logging attributes
        self._logger = logger.getChild(f"{self.__class__.__name__}_{id(self)}")
        self._logger.addHandler(logging.StreamHandler())
        self.verbose = verbose
        return
    
    def __del__(self):
        self.disconnect()
        return
    
    @property
    def feed(self) -> cv2.VideoCapture:
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
        for handler in self._logger.handlers:
            if not isinstance(handler, logging.StreamHandler):
                continue
            handler.setLevel(level)
        return
    
    @property
    def frame_rate(self) -> int|float:
        return self.feed.get(cv2.CAP_PROP_FPS)
    
    @property
    def frame_size(self) -> tuple[int,int]:
        width = int(self.feed.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.feed.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (width,height)
    
    # Connection methods
    def checkDeviceConnection(self) -> bool:
        """Check the connection to the device"""
        return self.feed.isOpened()
    
    def connect(self):
        return self.connectFeed()
    
    def connectFeed(self):
        """Connect to the device"""
        # if self.is_connected:
        #     return
        try:
            feed_source = self.connection_details.get('feed_source', 0)
            feed_api = self.connection_details.get('feed_api', None)
            logger.info(f'Opening feed: {feed_source}')
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
        return
    
    def disconnect(self):
        return self.disconnectFeed()
    
    def disconnectFeed(self):
        """Disconnect from the device"""
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
            array (bytes): byte array of image

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
    def transformFrame(
        frame: np.ndarray,
        transforms: Iterable[tuple[Callable[[np.ndarray,Any], np.ndarray], Iterable|None, Mapping|None]]|None = None,
    ) -> np.ndarray:
        """Process the output"""
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
        """Process the output"""
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
            crosshair (bool, optional): whether to overlay crosshair on image. Defaults to False.
            resize (bool, optional): whether to resize the image. Defaults to False.
            latest (bool, optional): whether to get the latest image. Default to False.

        Returns:
            tuple[bool, np.ndarray]: (whether an image is obtained, image array)
        """
        ret, frame = self.read()
        if latest:
            ret, frame = self.read()
        transformed_frame = self.transformFrame(frame, self.transforms)
        return ret, transformed_frame
    
    def show(self, 
        transforms: list[Callable[[np.ndarray], np.ndarray]]|None = None
    ):
        """
        Show image in window

        Args:
            frame (np.ndarray): image array to be displayed
            window_name (str, optional): name of window. Defaults to 'Camera Feed'.
        """
        self.transforms = transforms or []
        cv2.destroyAllWindows()
        self.startStream(show=True, buffer=self.buffer)
        return
    
    # IO methods
    def checkDeviceBuffer(self) -> bool:
        """Check the connection buffer"""
        ...
        raise NotImplementedError
    
    def clear(self):
        """Clear the input and output buffers"""
        self.stopStream()
        self.buffer = deque()
        self.data_queue = queue.Queue()
        return
    
    def read(self) -> tuple[bool, np.ndarray]:
        """Read data from the device"""
        ret = False
        frame = self.placeholder
        try:
            ret, frame = self.feed.read() # Replace with specific implementation
        except KeyboardInterrupt:
            self._logger.debug("Received keyboard interrupt")
            self.disconnect()
        except Exception as e: # Replace with specific exception
            self._logger.debug(f"Failed to receive data")
            self._logger.exception(e)
        if frame is None:
            frame = self.placeholder
        if self.flags.simulation:
            ret = True
        return ret, frame

    # Streaming methods
    def showStream(self, on: bool):
        """Show the stream"""
        _ = self.show_event.set() if on else self.show_event.clear()
        return
    
    def startStream(self,  
        buffer: deque|None = None,
        *, 
        show: bool = False,
        sync_start: threading.Barrier|None = None
    ):
        """Start the stream"""
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
        """Toggle the stream"""
        return self.startStream(buffer=buffer, sync_start=sync_start, **kwargs) if on else self.stopStream()
    
    def _loop_process_data(self, buffer: deque|None = None, sync_start:threading.Barrier|None = None) -> Any:
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
                cv2.imshow('output', transformed_frame)  
                if (cv2.waitKey(1) & 0xFF) == ord('q'):
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
                    break
        self.data_queue.join()
        return
    
    def _loop_stream(self, sync_start:threading.Barrier|None = None):
        """Stream loop"""
        if isinstance(sync_start, threading.Barrier):
            sync_start.wait()
        
        while self.stream_event.is_set():
            try:
                ret,frame = self.read()
                if ret:
                    now = datetime.now()
                    self.data_queue.put((frame, now), block=False)
            except queue.Full:
                time.sleep(0.01)
                continue
            except KeyboardInterrupt:
                self.stream_event.clear()
                break
        return
