# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/1 13:20:00
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
from datetime import datetime
import numpy as np
import os
import pandas as pd
from threading import Thread

# Third party imports
import cv2 # pip install opencv-python

# Local application imports
from .image_utils import Image
from .Classifiers import Classifier
print(f"Import: OK <{__name__}>")

class Camera(object):
    """
    Camera object

    Args:
        calibration_unit (int, optional): calibration of pixels to mm. Defaults to 1.
        cam_size (tuple, optional): width and height of image. Defaults to (640,480).
        rotation (int, optional): rotation of camera feed. Defaults to 0.
    """
    def __init__(self, calibration_unit=1, cam_size=(640,480), rotation=0):
        self.calibration_unit = calibration_unit
        self.cam_size = cam_size
        
        self.classifier = None
        self.device = None
        self.feed = None
        self.placeholder_image = None
        self.rotation = rotation
        
        self._flags = {
            'isConnected': False,
            'pause_record': False,
            'record': False
        }
        self._threads = {}
        self.record_folder = ''
        self.record_timeout = None
        pass
    
    def __delete__(self):
        self.close()
        return
    
    def _connect(self):
        """
        Connect to the imaging device
        """
        return
    
    def _data_to_df(self, data):
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
        df['row'] = np.ones(len(df), dtype='int64')
        row_num = 1
        for i in np.arange(1,len(df)): 
            # If diff in y-coordinates > 30, assign next row (adjustable)
            if (abs(df.loc[i,'y'] - df.loc[i-1,'y']) > 30):             
                row_num += 1
                df.loc[i,'row'] = row_num
            else:
                df.loc[i,'row'] = row_num
        df.sort_values(by=['row','x'], ascending=[True,True], inplace=True) 
        df.reset_index(inplace = True, drop = True)
        return df
    
    def _loop_record(self):
        """
        Record loop to constantly get and save image frames
        """
        start_message = f'Recording...' if self.record_timeout is None else f'Recording... ({self.record_timeout}s)'
        print(start_message)
        timestamp = []
        frame_num = 0
        start = datetime.now()
        folder = start.strftime("%Y-%m-%d_%H%M")
        if len(self.record_folder):
            folder = '/'.join([self.record_folder, folder])
        if not os.path.exists(f'{folder}/frames'):
            os.makedirs(f'{folder}/frames')
        
        start = datetime.now()
        while self._flags['record']:
            if self._flags['pause_record']:
                continue
            now = datetime.now()
            _, image = self.getImage()
            self.saveImage(image, filename=f'{folder}/frames/frame_{frame_num:05}.png')
            timestamp.append(now)
            frame_num += 1
            if self.record_timeout is not None and (now - start).seconds > self.record_timeout:
                break
        end = datetime.now()
        
        duration = end - start
        print('Stop recording...')
        print(f'\nDuration: {str(duration)}')
        print(f'\nFrames recorded: {frame_num}')
        print(f'\nAverage FPS: {frame_num/duration.seconds}')
        df = pd.DataFrame({'frame_num': [i for i in range(frame_num)], 'timestamp': timestamp})
        df.to_csv(f'{folder}/timestamps.csv')
        return
    
    def _read(self):
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
        self.feed.release()
        return
    
    def _set_placeholder(self, filename='', img_bytes=None, resize=False):
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
        if len(filename):
            image = self.loadImage(filename)
        elif type(img_bytes) == bytes:
            array = np.asarray(bytearray(img_bytes), dtype="uint8")
            image = self.decodeImage(array)
        if resize:
            image.resize(self.cam_size, inplace=True)
        self.placeholder_image = image
        return image
    
    def close(self):
        """
        Close the camera
        """
        self._release()
        cv2.destroyAllWindows()
        self._flags['isConnected'] = False
        return
    
    # Image handling
    def decodeImage(self, array):
        """
        Decode byte array of image

        Args:
            array (bytes): byte array of image

        Returns:
            Image: image of decoded byte array
        """
        frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
        return Image(frame)
    
    def encodeImage(self, image:Image=None, frame=None, ext='.png'):
        """
        Encode image into byte array

        Args:
            image (Image, optional): image object to be encoded. Defaults to None.
            frame (array, optional): frame array to be encoded. Defaults to None.
            ext (str, optional): image format to encode to. Defaults to '.png'.

        Raises:
            Exception: Input needs to be an Image or frame array

        Returns:
            bytes: byte representation of image/frame
        """
        if frame is None:
            if image is not None:
                return image.encode(ext)
            else:
                raise Exception('Please input either image or frame.')
        return cv2.imencode(ext, frame)[1].tobytes()
    
    def getImage(self, crosshair=False, resize=False):
        """
        Get image from camera feed

        Args:
            crosshair (bool, optional): whether to overlay crosshair on image. Defaults to False.
            resize (bool, optional): whether to resize the image. Defaults to False.

        Returns:
            bool, Image: True if image is obtained; image object
        """
        ret = False
        frame = None
        try:
            ret, frame = self._read()
            if ret:
                image = Image(frame)
                if resize:
                    image.resize(self.cam_size, inplace=True)
                image.rotate(self.rotation, inplace=True)
            else:
                image = self.placeholder_image
        except AttributeError:
            image = self.placeholder_image
        if crosshair:
            image.crosshair(inplace=True)
        return ret, image
    
    def isConnected(self):
        """
        Check whether the camera is connected

        Returns:
            bool: whether the camera is connected
        """
        return self._flags['isConnected']
    
    def loadImage(self, filename:str):
        """
        Load image from file

        Args:
            filename (str): filename of image

        Returns:
            Image: file image
        """
        frame = cv2.imread(filename)
        return Image(frame)
    
    def toggleRecord(self, on:bool, folder:str = '', timeout:int = None):
        """
        Toggle record

        Args:
            on (bool): whether to start recording frames
            folder (str, optional): folder to save to. Defaults to ''.
            timeout (int, optional): number of seconds to record. Defaults to None.
        """
        self.setFlag('record', on)
        if on:
            if 'record_loop' in self._threads:
                self._threads['record_loop'].join()
            self.record_folder = folder
            self.record_timeout = timeout
            thread = Thread(target=self._loop_record)
            thread.start()
            self._threads['record_loop'] = thread
        else:
            self._threads['record_loop'].join()
            pass
        return
    
    def saveImage(self, image:Image=None, frame=None, filename='image.png'):
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
        if frame is None:
            if image is not None:
                return image.save(filename)
            else:
                raise Exception('Please input either image or frame.')
        return cv2.imwrite(filename, frame)
    
    def setFlag(self, name:str, value:bool):
        """
        Set a flag truth value

        Args:
            name (str): label
            value (bool): flag value
        """
        self._flags[name] = value
        return
    
    # Image manipulation
    def annotateAll(self, df:pd.DataFrame, frame):
        """
        Annotate all targets

        Args:
            df (pd.DataFrame): dataframe of details of detected targets
            frame (array): frame array

        Returns:
            dict, Image: dictionary of (target index, center positions); image
        """
        data = {}
        image = Image(frame)
        for index in range(len(df)):
            dimensions = tuple(df.loc[index, ['x','y','w','h']].to_list())
            x,y,w,h = dimensions
            area = w*h
            center = [int(x+(w/2)), int(y+(h/2))]
            if area >= 36*36:
                image.annotate(index, dimensions, inplace=True)
                data[f'C{index+1}'] = center
        return data, image

    def detect(self, image:Image, scale:int, neighbors:int):
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
        detected_data = self.classifier.detect(image=image, scale=scale, neighbors=neighbors)
        df = self._data_to_df(detected_data)
        return df
    
    def loadClassifier(self, classifier:Classifier):
        """
        Load target classifier

        Args:
            classifier (Classifier): desired classifier
        """
        try:
            self.classifier = classifier
        except SystemError:
            print('Please select a classifier.')
        return
