# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/1 13:20:00
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
import numpy as np

# Third party imports
import cv2 # pip install opencv-python

# Local application imports
print(f"Import: OK <{__name__}>")

class Image(object):
    def __init__(self, frame):
        self.frame = frame
        pass
    
    def addText(self, text:str, position, inplace=False):
        frame = self.frame
        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def blur(self, blur_kernel=3, inplace=False):
        frame = cv2.GaussianBlur(self.frame, (blur_kernel,blur_kernel), 0)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def convolve(self, inplace=False):
        return
    
    def crosshair(self, inplace=False):
        frame = self.frame
        center_x = int(frame.shape[1] / 2)
        center_y = int(frame.shape[0] / 2)
        cv2.line(frame, (center_x, center_y+50), (center_x, center_y-50), (255,255,255), 1)
        cv2.line(frame, (center_x+50, center_y), (center_x-50, center_y), (255,255,255), 1)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def denoise(self):
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
        frame = self.frame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.morphologyEx(frame,cv2.MORPH_OPEN,kernel,iterations=open_iter)
        frame = cv2.morphologyEx(frame,cv2.MORPH_CLOSE,kernel,iterations=close_iter)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def resize(self, size, inplace=False):
        frame = cv2.resize(self.frame, size)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def rotate(self, angle, inplace=False):
        """
        Rotates a 2D array in multiples of 90 degrees, clockwise
        """
        rotateCodes = {
            90: cv2.ROTATE_90_CLOCKWISE,
            180: cv2.ROTATE_180,
            270: cv2.ROTATE_90_COUNTERCLOCKWISE
        }
        frame = self.frame
        frame = cv2.rotate(frame, rotateCodes.get(angle))
        if inplace:
            self.frame = frame
            return
        return Image(frame)

    def save(self, filename):
        return cv2.imwrite(filename, self.frame)
