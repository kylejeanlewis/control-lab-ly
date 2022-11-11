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
from .Thermal.Flir.ax8.ax8 import Ax8ThermalCamera
print(f"Import: OK <{__name__}>")

class Image(object):
    def __init__(self, frame):
        self.frame = frame
        pass
    
    def blur(self, blur_kernel=3, inplace=False):
        frame = cv2.GaussianBlur(frame, (blur_kernel,blur_kernel), 0)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def convolve(self):
        return
    
    def encode(self, extension='.png'):
        return cv2.imencode(extension, self.frame)[1].tobytes()
    
    def grayscale(self, inplace=False):
        frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def process(self, alpha, beta, blur_kernel, inplace=False):
        frame = self.frame
        frame = cv2.addWeighted(frame, alpha, np.zeros(frame.shape, frame.dtype), 0, beta)
        if blur_kernel > 0:
            frame = cv2.GaussianBlur(frame, (blur_kernel,blur_kernel), 0)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def removeNoise(self, open_iter=0, close_iter=0, inplace=False):
        kernel = np.ones((3,3),np.uint8)
        roi_color = self.frame
        roi_gray = cv2.cvtColor(roi_color, cv2.COLOR_BGR2GRAY)
        roi_gray = cv2.morphologyEx(roi_gray,cv2.MORPH_OPEN,kernel,iterations=open_iter)
        roi_gray = cv2.morphologyEx(roi_gray,cv2.MORPH_CLOSE,kernel,iterations=close_iter)
        return
    
    def resize(self, size, inplace=False):
        frame = cv2.resize(self.frame, size)
        if inplace:
            self.frame = frame
            return
        return Image(frame)

    def save(self, filename):
        return cv2.imwrite(filename, self.frame)


class Camera(object):
    def __init__(self, calib_unit=1, cam_size=(640,480)):
        self.calib_unit = calib_unit
        self.cam_size = cam_size
        
        self.classifier = None
        self.device = None
        self.feed = None
        self.placeholder_image = None
        pass
    
    def __delete__(self):
        self._close()
        return
        
    def _close(self):
        self.feed.release()
        cv2.destroyAllWindows()
        return
    
    def _connect(self):
        return
    
    def _set_placeholder(self, filename='', img_bytes=None):
        frame = None
        if len(filename):
            frame = self.loadImage(filename)
        elif img_bytes == None:
            array = np.asarray(bytearray(img_bytes), dtype="uint8")
            frame = self.decodeImage(array)
        self.placeholder_image = Image(frame)
        return frame
    
    # Image handling
    def decodeImage(self, array):
        frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
        return Image(frame)
    
    def encodeImage(self, image=None, frame=None, ext='.png'):
        if type(frame) == type(None):
            if type(image) != type(None):
                return image.encode(ext)
            else:
                raise Exception('Please input either image or frame.')
        return cv2.imencode(ext, frame)[1].tobytes()
    
    def getImage(self):
        ret = False
        val = None
        ret, val = self.feed.read()
        return ret, val
    
    def loadImage(self, filename):
        frame = cv2.imread(filename)
        return Image(frame)
    
    def saveImage(self, image=None, frame=None, filename='image.png'):
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

    def detect(self, frame, scale, neighbors):
        if type(self.classifier) == type(None):
            raise Exception('Please load a classifier first.')
        df = pd.DataFrame()
        gray_img = self.grayscale(frame)
        detected_items = self.classifier.detectMultiScale(image=gray_img, scaleFactor=scale, minNeighbors=neighbors)
        df = self.data_to_df(detected_items)
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
        return
    
    def getImage(self):
        return super().getImage()
    

class Thermal(Camera):
    def __init__(self, ip_address, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connect()
        
        img_bytes = pkgutil.get_data(__name__, 'placeholders/infrared_camera.png')
        self._set_placeholder(img_bytes=img_bytes)
        return
    
    def _connect(self, ip_address):
        self.device = Ax8ThermalCamera(ip_address)
        self.feed = self.device.video.stream
        return
    
    def getImage(self):
        return super().getImage()
    