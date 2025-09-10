# -*- coding: utf-8 -*-
from typing import Type, Any, Callable, Iterable

class Part:
    device: Any
    connection_details: dict
    is_busy: bool
    is_connected: bool
    verbose: bool
    def connect(self):...
    def disconnect(self):...
    def resetFlags(self):...
    def shutdown(self):...

class TriContinent:
    volume: float
    start_speed: int|str
    acceleration: int|str
    valve_position: str|None
    init_status: bool|str
    def connect(self): ...
    def aspirate(self, 
        volume: float, 
        speed: float|None = None, 
        reagent: str|None = None,
        *,
        start_speed: int|None = None,
        pullback: bool = False,
        delay: int = 0, 
        pause: bool = False, 
        ignore: bool = False,
        blocking: bool = True,
        **kwargs
    ) -> bool: ...
    def dispense(self, 
        volume: float, 
        speed: float|None = None, 
        *,
        start_speed: int|None = None,
        blowout: bool = False,
        delay: int = 0, 
        pause: bool = False, 
        ignore: bool = False,
        blocking: bool = True,
        **kwargs
    ) -> bool: ...
    def getState(self) -> dict[str, int|str|bool]: ...
    def home(self): ...
    def setSpeed(self, speed: float): ...
    def reverse(self): ...
    def setChannel(self): ...

class Multi_TriContinent:
    volume: float
    start_speed: int|str
    acceleration: int|str
    valve_position: str|None
    init_status: bool|str
    channel: int
    channels: dict[str,Part]
    def setActiveChannel(self, channel:int|None = None):...
    def connect(self):...
    def aspirate(self, 
        volume: float, 
        speed: float|None = None, 
        reagent: str|None = None,
        *,
        start_speed: int|None = None,
        pullback: bool = False,
        delay: int = 0, 
        pause: bool = False, 
        ignore: bool = False,
        blocking: bool = True,
        **kwargs
    ) -> bool:...
    def dispense(self, 
        volume: float, 
        speed: float|None = None, 
        *,
        start_speed: int|None = None,
        blowout: bool = False,
        delay: int = 0, 
        pause: bool = False, 
        ignore: bool = False,
        blocking: bool = True,
        **kwargs
    ) -> bool:...
    def getState(self) -> dict[str, int|str|bool]:...
    def home(self):...
    def setSpeed(self, speed: float):...
    def reverse(self):...
    def setChannel(self):...

class Parallel_TriContinent:
    volume: float
    start_speed: int|str
    acceleration: int|str
    valve_position: str|None
    init_status: bool|str
    channels: dict[str,Part]
    def parallel(self, 
        method_name: str, 
        kwargs_generator: Callable[[int,int,Part], dict[str,Any]]|None = None,
        *args, 
        channels: Iterable[int],
        max_workers: int = 4,
        timeout:int|float = 120,
        stagger: int|float = 0.5,
        **kwargs
    ) -> dict[int,Any]:...
    def connect(self):...
    def aspirate(self, 
        volume: float, 
        speed: float|None = None, 
        reagent: str|None = None,
        *,
        start_speed: int|None = None,
        pullback: bool = False,
        delay: int = 0, 
        pause: bool = False, 
        ignore: bool = False,
        blocking: bool = True,
        **kwargs
    ) -> bool:...
    def dispense(self, 
        volume: float, 
        speed: float|None = None, 
        *,
        start_speed: int|None = None,
        blowout: bool = False,
        delay: int = 0, 
        pause: bool = False, 
        ignore: bool = False,
        blocking: bool = True,
        **kwargs
    ) -> bool:...
    def getState(self) -> dict[str, int|str|bool]:...
    def home(self):...
    def setSpeed(self, speed: float):...
    def reverse(self):...
    def setChannel(self):...

Multi_TriContinent: Type[Multi_TriContinent]
Parallel_TriContinent: Type[Parallel_TriContinent]
