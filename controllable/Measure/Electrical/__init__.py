class ElectricalMeasurer(object):
    def __init__(self) -> None:
        self.ip_address = ''
        self.inst = None
        self.buffer_df = None
        self.data = None
        self.program = None
        self.flags = {}
        
        self._parameters = {}
        pass
    
    def _mapColumnNames(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method '_mapColumnNames'")
        return
    
    def _readData(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method '_readData'")
        return
    
    def _run_program(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method '_run_program'")
        return
    
    def connect(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'connect'")
        return
    
    def getData(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'getData'")
        return
    
    def loadProgram(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'loadProgram'")
        return
    
    def logData(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'logData'")
        return
    
    def measure(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'measure'")
        return
    
    def plot(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'plot'")
        return
    
    def recallParameters(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'recallParameters'")
        return
    
    def reset(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'reset'")
        return
    
    def saveData(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'saveData'")
        return
    
    def sendMessage(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'sendMessage'")
        return
    
    def setParameters(self, *args, **kwargs):
        """EMPTY METHOD"""
        print(f"'{self.__class__.__name__}' class has no method 'setParameters'")
        return
