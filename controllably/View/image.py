# %% -*- coding: utf-8 -*-
"""
This module holds the base class for image data.

## Functions:
    `addText`: Add text to the image
    `annotate`: Annotate the image to label identified targets
    `blur`: Blur the image
    `convolve`: Perform convolution on image
    `crosshair`: Add crosshair in the middle of image
    `process`: Process the image
    `removeNoise`: Remove noise from image
    `rotate`: Rotate a 2D array of multiples of 90 degrees, clockwise
"""
# Standard library imports
from __future__ import annotations
import logging
import numpy as np

# Third party imports
import cv2              # pip install opencv-python

# Local application imports

logger = logging.getLogger(__name__)
logger.debug(f"Import: OK <{__name__}>")

def addText(frame:np.ndarray, text:str, position:tuple[int]) -> np.ndarray:
    """
    Add text to the image

    Args:
        frame (np.ndarray): frame array
        text (str): text to be added
        position (tuple[int]): x,y position of where to place the text

    Returns:
        np.ndarray: frame array
    """
    return cv2.putText(frame, text, position, cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)

def annotate(frame:np.ndarray, index:int, dimensions:tuple[int]) -> np.ndarray:
    """
    Annotate the image to label identified targets

    Args:
        frame (np.ndarray): frame array
        index (int): index of target
        dimensions (tuple[int]): list of x,y,w,h

    Returns:
        np.ndarray: frame array
    """
    x,y,w,h = dimensions
    frame = cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
    frame = cv2.circle(frame, (int(x+(w/2)), int(y+(h/2))), 3, (0,0,255), -1)
    frame = cv2.putText(frame, '{}'.format(index+1), (x-8, y-4), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
    return frame

def blur(frame:np.ndarray, blur_kernel:int = 3) -> np.ndarray:
    """
    Blur the image

    Args:
        frame (np.ndarray): frame array
        blur_kernel (int, optional): level of blurring, odd numbers only, minimum value of 3. Defaults to 3.

    Returns:
        np.ndarray: frame array
    """
    return cv2.GaussianBlur(frame, (blur_kernel,blur_kernel), 0)

def convolve(frame:np.ndarray) -> np.ndarray: # FIXME
    """
    Perform convolution on image

    Args:
        frame (np.ndarray): frame array

    Returns:
        np.ndarray: frame array
    """
    return

def crosshair(frame:np.ndarray) -> np.ndarray:
    """
    Add crosshair in the middle of image

    Args:
        frame (np.ndarray): frame array

    Returns:
        np.ndarray: frame array
    """
    center_x = int(frame.shape[1] / 2)
    center_y = int(frame.shape[0] / 2)
    cv2.line(frame, (center_x, center_y+50), (center_x, center_y-50), (255,255,255), 1)
    cv2.line(frame, (center_x+50, center_y), (center_x-50, center_y), (255,255,255), 1)
    return frame

def process(frame:np.ndarray, alpha:float, beta:float, blur_kernel:int = 3) -> np.ndarray: # FIXME
    """
    Process the image

    Args:
        frame (np.ndarray): frame array
        alpha (float): alpha value
        beta (float): beta value
        blur_kernel (int, optional): level of blurring, odd numbers only, minimum value of 3. Defaults to 3.

    Returns:
        np.ndarray: frame array
    """
    frame = cv2.addWeighted(frame, alpha, np.zeros(frame.shape, frame.dtype), 0, beta)
    if blur_kernel > 0:
        frame = cv2.GaussianBlur(frame, (blur_kernel,blur_kernel), 0)
    return frame

def removeNoise(frame:np.ndarray, open_iter:int = 0, close_iter:int = 0) -> np.ndarray:
    """
    Remove noise from image

    Args:
        frame (np.ndarray): frame array
        open_iter (int, optional): opening iteration. Defaults to 0.
        close_iter (int, optional): closing iteration. Defaults to 0.

    Returns:
        np.ndarray: frame array
    """
    kernel = np.ones((3,3),np.uint8)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.morphologyEx(frame,cv2.MORPH_OPEN,kernel,iterations=open_iter)
    frame = cv2.morphologyEx(frame,cv2.MORPH_CLOSE,kernel,iterations=close_iter)
    return frame

def rotate(frame:np.ndarray, angle:int) -> np.ndarray:
    """
    Rotate a 2D array of multiples of 90 degrees, clockwise

    Args:
        frame (np.ndarray): frame array
        angle (int): 90, 180, or 270 degrees

    Returns:
        np.ndarray: frame array
    """
    rotateCodes = {
        90: cv2.ROTATE_90_CLOCKWISE,
        180: cv2.ROTATE_180,
        270: cv2.ROTATE_90_COUNTERCLOCKWISE
    }
    if angle != 0:
        frame = cv2.rotate(frame, rotateCodes.get(angle))
    return frame
