# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/1 13:20:00
@author: Chang Jie

Notes / actionables:
- validation on copper 
- rewrite the operation modes as programs, instead of subclasses
"""
# Third party imports
import cv2 # pip install opencv-python

# Local application imports
from ..image_utils import Image
print(f"Import: OK <{__name__}>")

class Classifier(object):
    """
    Classifier object
    """
    def __init__(self):
        pass
    
    def detect(self, image:Image, scale:int, neighbors:int):
        """
        Detect targets

        Args:
            image (Image): image to detect from
            scale (int): scale at which to detect targets
            neighbors (int): minimum number of neighbors for targets

        Returns:
            dict: dictionary of detected targets
        """
        return

class CascadeClassifier(Classifier):
    def __init__(self, xml_path:str):
        """
        Cascade classifier object

        Args:
            xml_path (str): filepath of trained cascade xml file
        """
        self.classifier = cv2.CascadeClassifier(xml_path)
        pass
    
    def detect(self, image:Image, scale:int, neighbors:int):
        """
        Detect targets

        Args:
            image (Image): image to detect from
            scale (int): scale at which to detect targets
            neighbors (int): minimum number of neighbors for targets

        Returns:
            dict: dictionary of detected targets
        """
        return self.classifier.detectMultiScale(image=image.frame, scaleFactor=scale, minNeighbors=neighbors)
    