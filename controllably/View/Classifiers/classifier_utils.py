# %% -*- coding: utf-8 -*-
"""
This module holds the base class for image classifiers
and the class for cascade classifiers.

Classes:
    Classifier (ABC)
    CascadeClassifier (Classifier)
"""
# Standard library imports
from abc import ABC, abstractmethod

# Third party imports
import cv2 # pip install opencv-python

# Local application imports
from .. import image as Image
print(f"Import: OK <{__name__}>")

class Classifier(ABC):
    """
    Abstract Base Class (ABC) for Classifier objects (i.e. models that can detect image targets).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Attributes
    - `classifier` (Callable): image classifier model
    
    ### Methods
    #### Abstract
    - `detect`: detect image targets
    """
    
    def __init__(self):
        """Instantiate the class"""
        self.classifier = None
        pass
    
    @abstractmethod
    def detect(self, image:Image, scale:int, neighbors:int) -> dict:
        """
        Detect image targets

        Args:
            image (Image): image to detect from
            scale (int): scale at which to detect targets
            neighbors (int): minimum number of neighbors for targets

        Returns:
            dict: dictionary of detected targets
        """

class CascadeClassifier(Classifier):
    """
    Abstract Base Class (ABC) for Classifier objects (i.e. models that can detect image targets).
    ABC cannot be instantiated, and must be subclassed with abstract methods implemented before use.
    
    ### Constructor
    Args:
        `xml_path` (str): filepath of trained cascade xml file
    
    ### Methods
    #### Abstract
    - `detect`: detect image targets
    """
    
    def __init__(self, xml_path:str):
        """
        Cascade classifier object

        Args:
            xml_path (str): filepath of trained cascade xml file
        """
        self.classifier = cv2.CascadeClassifier(xml_path)
        pass
    
    def detect(self, image:Image, scale:int, neighbors:int) -> dict:
        """
        Detect image targets

        Args:
            image (Image): image to detect from
            scale (int): scale at which to detect targets
            neighbors (int): minimum number of neighbors for targets

        Returns:
            dict: dictionary of detected targets
        """
        return self.classifier.detectMultiScale(image=image.frame, scaleFactor=scale, minNeighbors=neighbors)
    