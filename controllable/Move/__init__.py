class Mover(object):
    def __init__(self, **kwargs) -> None:
        self.verbose = False
        pass
    
    def _connect(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method '_connect'")
        return
    
    def _freeze(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method '_freeze'")
        return
    
    def _shutdown(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method '_shutdown'")
        return
    
    def calibrate(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'calibrate'")
        return
    
    def calibrationMode(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'calibrationMode'")
        return
    
    def connect(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'connect'")
        return
    
    def getOrientation(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'getOrientation'")
        return

    def getPosition(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'getPosition'")
        return
    
    def getWorkspacePosition(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'getWorkspacePosition'")
        return
    
    def getSettings(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'getSettings'")
        return
    
    def home(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'home'")
        return

    def isFeasible(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'isFeasible'")
        return

    def move(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'move'")
        return
    
    def moveBy(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'moveBy'")
        return

    def moveTo(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'moveTo'")
        return
    
    def reset(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'reset'")
        return
    
    def rotateBy(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'rotateBy'")
        return

    def rotateTo(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'rotateTo'")
        return
    
    def setImplementOffset(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'setImplementOffset'")
        return

    def setPosition(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'setPosition'")
        return
    
    def setSpeed(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'setSpeed'")
        return
    
    def stop(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'stop'")
        return

    def updatePosition(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method '_tuck'")
        return

from . import Cartesian
from . import Jointed
from . import Liquid