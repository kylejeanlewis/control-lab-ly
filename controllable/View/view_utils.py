# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/1 13:20:00
@author: Chang Jie

Notes / actionables:
- validation on copper 
- rewrite the operation modes as programs, instead of subclasses
"""
# Standard library imports
import numpy as np
import os
import pandas as pd
import pkgutil
import time

# Third party imports
import cv2 # pip install opencv-python

# Local application imports
from .image_utils import Image
from .Thermal.Flir.ax8.ax8 import Ax8ThermalCamera
print(f"Import: OK <{__name__}>")

class Camera(object):
    def __init__(self, calib_unit=1, cam_size=(640,480)):
        self.calib_unit = calib_unit
        self.cam_size = cam_size
        
        self.classifier = None
        self.device = None
        self.feed = None
        self.placeholder_image = None
        
        self.flags = {
            'isConnected': False
        }
        pass
    
    def __delete__(self):
        self.close()
        return
    
    def _connect(self):
        return
    
    def _data_to_df(self, data):
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
    
    def _set_placeholder(self, filename='', img_bytes=None):
        image = None
        if len(filename):
            image = self.loadImage(filename)
        elif type(img_bytes) == bytes:
            array = np.asarray(bytearray(img_bytes), dtype="uint8")
            image = self.decodeImage(array)
        image.resize(self.cam_size, inplace=True)
        self.placeholder_image = image
        return image
    
    def close(self):
        self.feed.release()
        cv2.destroyAllWindows()
        self.flags['isConnected'] = False
        return
    
    # Image handling
    def decodeImage(self, array):
        frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
        return Image(frame)
    
    def encodeImage(self, image:Image=None, frame=None, ext='.png'):
        if type(frame) == type(None):
            if type(image) != type(None):
                return image.encode(ext)
            else:
                raise Exception('Please input either image or frame.')
        return cv2.imencode(ext, frame)[1].tobytes()
    
    def getImage(self, crosshair=False):
        ret = False
        frame = None
        try:
            ret, frame = self.feed.read()
            if ret:
                image = Image(frame)
                image.resize(self.cam_size, inplace=True)
            else:
                image = self.placeholder_image
        except AttributeError:
            image = self.placeholder_image
        if crosshair:
            image.crosshair(inplace=True)
        return ret, image
    
    def loadImage(self, filename):
        frame = cv2.imread(filename)
        return Image(frame)
    
    def saveImage(self, image:Image=None, frame=None, filename='image.png'):
        if type(frame) == type(None):
            if type(image) != type(None):
                return image.save(filename)
            else:
                raise Exception('Please input either image or frame.')
        return cv2.imwrite(filename, frame)
    
    # Image manipulation
    def annotate(self, index, dimensions, frame, opening_iter=0, closing_iter=0):
        """
        Annotate the image to label identified targets
        - df: dataframe of identified targets
        - frame: image
        - opening_iter: BG noise removal iterations
        - closing_iter: FG noise removal iterations

        Return: image
        """
        x,y,w,h = dimensions
        center = [int(x+(w/2)), int(y+(h/2))]
        cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
        cv2.circle(frame, (int(x+(w/2)), int(y+(h/2))), 3, (0,0,255), -1)
        cv2.putText(frame, '{}'.format(index+1), (x-8, y-4), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.6, (255,255,255), 1)

        # Morphological Transformations - Noise Removal
        roi_color = frame[y:y+h, x:x+w]
        roi_gray = cv2.cvtColor(roi_color, cv2.COLOR_BGR2GRAY)
        kernel = np.ones((3,3),np.uint8)
        roi_gray = cv2.morphologyEx(roi_gray,cv2.MORPH_OPEN,kernel,iterations=opening_iter)
        roi_gray = cv2.morphologyEx(roi_gray,cv2.MORPH_CLOSE,kernel,iterations=closing_iter)

        # Image Thresholding: Inverse Binary Thresholding + the OTSU method
        ret, thresh = cv2.threshold(roi_gray, 127, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        
        # Contour Detection
        # contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        # contours = contours[1:]
        # cv2.drawContours(roi_color, contours, -1, (255,0,0), 2)
        return center, frame
    
    def annotateAll(self, df, frame, opening_iter=0, closing_iter=0):
        data = {}
        for index in range(len(df)):
            dimensions = df.loc[index, ['x','y','w','h']].to_list()
            area = dimensions[2]*dimensions[3]
            if area >= 36*36:
                center, frame = self.annotate(index, dimensions, frame, opening_iter, closing_iter)
                data[f'C{index+1}'] = center
        return data, frame

    def detect(self, image:Image, scale, neighbors):
        if type(self.classifier) == type(None):
            raise Exception('Please load a classifier first.')
        image.grayscale(inplace=True)
        detected_data = self.classifier.detectMultiScale(image=image.frame, scaleFactor=scale, minNeighbors=neighbors)
        df = self._data_to_df(detected_data)
        return df
    
    def loadClassifier(self, xml_path):
        clf = None
        try:
            clf = cv2.CascadeClassifier(xml_path)
            self.classifier = clf
        except SystemError:
            print('Please select a trained xml file.')
        return clf


class Optical(Camera):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connect()
        
        img_bytes = pkgutil.get_data(__name__, 'placeholders/optical_camera.png')
        self._set_placeholder(img_bytes=img_bytes)
        return
    
    def _connect(self):
        self.feed = cv2.VideoCapture(0)
        self.flags['isConnected'] = True
        return
    
    def getImage(self):
        if not self.flags['isConnected']:
            self._connect()
        return super().getImage(crosshair=True)


class Thermal(Camera):
    def __init__(self, ip_address, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connect(ip_address)
        
        img_bytes = pkgutil.get_data(__name__, 'placeholders/infrared_camera.png')
        self._set_placeholder(img_bytes=img_bytes)
        return
    
    def _connect(self, ip_address):
        self.device = Ax8ThermalCamera(ip_address)
        self.feed = self.device.video.stream
        self.flags['isConnected'] = True
        return
    
    def getImage(self):
        if not self.flags['isConnected']:
            self._connect()
        ret, image = super().getImage(crosshair=True)
        if ret:
            image.rotate(180, inplace=True)
        return ret, image
    