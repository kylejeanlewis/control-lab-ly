import controllably

class TestClass:
    def __init__(self, a=0, b=1, *args, **kwargs):
        self.a = a
        self.b = b
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    def shutdown(self):
        pass

class TestClassError:
    def __init__(self, a=0, b=1, *args, **kwargs):
        self.a = a
        self.b = b
        for key, value in kwargs.items():
            setattr(self, key, value)
        raise TypeError
            
    def shutdown(self):
        """shutdown"""
 
class TestCompoundClass(controllably.core.compound.Compound):
    def __init__(self, a=0, b=1, *args, parts: dict[str,object], verbose:bool = False, **kwargs):
        super().__init__(*args, parts=parts, verbose=verbose, **kwargs)
        self.a = a
        self.b = b

class TestCombinedClass(controllably.core.compound.Combined):
    def __init__(self, a=0, b=1, *args, parts: dict[str,object], verbose:bool = False, **kwargs):
        super().__init__(*args, parts=parts, verbose=verbose, **kwargs)
        self.a = a
        self.b = b
        
TestEnsembleClass = controllably.core.compound.Ensemble.factory(TestClass)
TestMultichannelClass = controllably.core.compound.Multichannel.factory(TestClass)