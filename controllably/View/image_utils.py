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
    """
    Image class with image manipulation methods

    Args:
        frame (array): image frame
    """
    def __init__(self, frame):
        self.frame = frame
        pass
    
    def addText(self, text:str, position, inplace=False):
        """
        Add text to the image

        Args:
            text (str): text to be added
            position (tuple): x,y position of where to place the text
            inplace (bool, optional): whether to perform action in place. Defaults to False.

        Returns:
            Image, or None: Image object, or None (if inplace=True)
        """
        frame = self.frame
        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def annotate(self, index:int, dimensions:tuple, inplace=False):
        """
        Annotate the image to label identified targets

        Args:
            index (int): index of target
            dimensions (list): list of x,y,w,h
            inplace (bool, optional): whether to perform action in place. Defaults to False.

        Returns:
            Image, or None: Image object, or None (if inplace=True)
        """
        x,y,w,h = dimensions
        frame = self.frame
        frame = cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
        frame = cv2.circle(frame, (int(x+(w/2)), int(y+(h/2))), 3, (0,0,255), -1)
        frame = cv2.putText(frame, '{}'.format(index+1), (x-8, y-4), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def blur(self, blur_kernel=3, inplace=False):
        """
        Blur the image

        Args:
            blur_kernel (int, optional): level of blurring, odd numbers only, minimum value of 3. Defaults to 3.
            inplace (bool, optional): whether to perform action in place. Defaults to False.

        Returns:
            Image, or None: Image object, or None (if inplace=True)
        """
        frame = cv2.GaussianBlur(self.frame, (blur_kernel,blur_kernel), 0)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def convertToRGB(self, inplace=False):
        """
        Turn image to RGB

        Args:
            inplace (bool, optional): whether to perform action in place. Defaults to False.

        Returns:
            Image, or None: Image object, or None (if inplace=True)
        """
        frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def convolve(self, inplace=False):
        """
        Perform convolution on image

        Args:
            inplace (bool, optional): whether to perform action in place. Defaults to False.

        Returns:
            Image, or None: Image object, or None (if inplace=True)
        """
        return
    
    def crosshair(self, inplace=False):
        """
        Add crosshair in the middle of image

        Args:
            inplace (bool, optional): whether to perform action in place. Defaults to False.

        Returns:
            Image, or None: Image object, or None (if inplace=True)
        """
        frame = self.frame
        center_x = int(frame.shape[1] / 2)
        center_y = int(frame.shape[0] / 2)
        cv2.line(frame, (center_x, center_y+50), (center_x, center_y-50), (255,255,255), 1)
        cv2.line(frame, (center_x+50, center_y), (center_x-50, center_y), (255,255,255), 1)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def encode(self, extension='.png'):
        """
        Encode the frame into bytes

        Args:
            extension (str, optional): image format to encode to. Defaults to '.png'.

        Returns:
            bytes: byte representation of image
        """
        return cv2.imencode(extension, self.frame)[1].tobytes()
    
    def grayscale(self, inplace=False):
        """
        Turn image to grayscale

        Args:
            inplace (bool, optional): whether to perform action in place. Defaults to False.

        Returns:
            Image, or None: Image object, or None (if inplace=True)
        """
        frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def process(self, alpha, beta, blur_kernel=3, inplace=False):
        """
        Process the image

        Args:
            alpha (float): alpha value
            beta (float): beta value
            blur_kernel (int, optional): level of blurring, odd numbers only, minimum value of 3. Defaults to 3.
            inplace (bool, optional): whether to perform action in place. Defaults to False.

        Returns:
            Image, or None: Image object, or None (if inplace=True)
        """
        frame = self.frame
        frame = cv2.addWeighted(frame, alpha, np.zeros(frame.shape, frame.dtype), 0, beta)
        if blur_kernel > 0:
            frame = cv2.GaussianBlur(frame, (blur_kernel,blur_kernel), 0)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def removeNoise(self, open_iter=0, close_iter=0, inplace=False):
        """
        Remove noise from image

        Args:
            open_iter (int, optional): opening iteration. Defaults to 0.
            close_iter (int, optional): closing iteration. Defaults to 0.
            inplace (bool, optional): whether to perform action in place. Defaults to False.

        Returns:
            Image, or None: Image object, or None (if inplace=True)
        """
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
        """
        Resize the image

        Args:
            size (tuple): tuple of desired image width and height
            inplace (bool, optional): whether to perform action in place. Defaults to False.

        Returns:
            Image, or None: Image object, or None (if inplace=True)
        """
        frame = cv2.resize(self.frame, size)
        if inplace:
            self.frame = frame
            return
        return Image(frame)
    
    def rotate(self, angle:int, inplace=False):
        """
        Rotate a 2D array of multiples of 90 degrees, clockwise

        Args:
            angle (int): 90, 180, or 270 degrees
            inplace (bool, optional): whether to perform action in place. Defaults to False.

        Returns:
            Image, or None: Image object, or None (if inplace=True)
        """
        rotateCodes = {
            90: cv2.ROTATE_90_CLOCKWISE,
            180: cv2.ROTATE_180,
            270: cv2.ROTATE_90_COUNTERCLOCKWISE
        }
        frame = self.frame
        if angle != 0:
            frame = cv2.rotate(frame, rotateCodes.get(angle))
        if inplace:
            self.frame = frame
            return
        return Image(frame)

    def save(self, filename):
        """
        Save image to file

        Args:
            filename (str): filename to save to

        Returns:
            bool: True if successfully saved
        """
        return cv2.imwrite(filename, self.frame)
