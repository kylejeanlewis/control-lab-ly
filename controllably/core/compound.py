# -*- coding: utf-8 -*-
""" 
This module contains classes to create compound tools.\n
The distinction between Compound, Ensemble, Combined and Multichannel tools 
is presented in the table below:

<table>
<tr><th>Class</th><th>Device(s)</th><th>Components</th></tr>
<tr><td>Compound</td><td>Multiple connection</td><td>Different parts</td></tr>
<tr><td>Ensemble</td><td>Multiple connection</td><td>Duplicate parts</td></tr>
<tr><td>Combined</td><td>Single connection</td><td>Different parts</td></tr>
<tr><td>Multichannel</td><td>Single connection</td><td>Duplicate parts</td></tr>
</table>

## Classes:
    `Part`: Protocol for Part (i.e. component tools)
    `Compound`: Compound class is an aggregation of multiple part tools
    `Ensemble`: Ensemble class is an aggregation of duplicate part tools to form multiple channels
    `Combined`: Combined class is an composition of multiple part tools
    `Multichannel`: Multichannel class is an composition of duplicate part tools to form multiple channels
    
<i>Documentation last updated: 2025-06-11</i>
"""
# Standard library imports
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
import inspect
import logging
import time
from types import SimpleNamespace
from typing import Protocol, Callable, Sequence, Type, Iterable, Any

# Local application imports
from .device import Device
from . import factory

# Configure logging
from controllably import CustomLevelFilter
logger = logging.getLogger(__name__)

class Part(Protocol):
    device: Any
    connection_details: dict
    is_busy: bool
    is_connected: bool
    verbose: bool
    def connect(self):...
    def disconnect(self):...
    def resetFlags(self):...
    def shutdown(self):...


class Compound:
    """ 
    Compound class is an aggregation of multiple part tools.
    Do not instantiate this class directly.
    Subclass this class to create a specific Compound tool.
    
    ## Constructor:
        `parts` (dict[str,Part]): dictionary of parts
        `verbose` (bool, optional): verbosity of class. Defaults to False.
        
    ## Attributes and properties:
        `connection_details` (dict): connection details of each part
        `parts` (SimpleNamespace[str,Part]): namespace of parts
        `flags` (SimpleNamespace[str,bool]): flags of class
        `is_busy` (bool): whether any part is busy
        `is_connected` (bool): whether all parts are connected
        `verbose` (bool): verbosity of class
        
    ## Methods:
        `fromConfig`: factory method to create Compound from configuration dictionary
        `connect`: connect to each component Part
        `disconnect`: disconnect from each component Part
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `shutdown`: shutdown each component Part
    """
    
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(verbose=False)
    def __init__(self, *args, parts: dict[str,Part], verbose:bool = False, **kwargs):
        """
        Initialise Compound class

        Args:
            parts (dict[str,Part]): dictionary of parts
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self._parts = parts
        self.flags = deepcopy(self._default_flags)
        
        self._logger = logger.getChild(f"{self.__class__.__name__}.{id(self)}")
        self.verbose = verbose
        return
    
    def __repr__(self):
        parts = '\n'.join([f"  {name}={part!r}" for name,part in self._parts.items()])
        return f"{super().__repr__()} containing:\n{parts}"
    
    def __str__(self):
        parts = '\n'.join([f"  {name}: {part.__class__.__name__}" for name,part in self._parts.items()])
        _str = f"{self.__class__.__name__} containing:\n{parts}"
        return _str
    
    def __del__(self):
        self.shutdown()
        return
    
    @classmethod
    def fromConfig(cls, config:dict) -> Compound:
        """
        Factory method to create Compound from configuration dictionary
        
        Args:
            config (dict): configuration dictionary
            
        Returns:
            Compound: instance of Compound (or its subclasses)
        """
        details = config.pop('details')
        parts = factory.load_parts(details)
        return cls(parts=parts, **config)
    
    @property
    def connection_details(self):
        """Connection details of each part"""
        return {name:part.connection_details for name,part in self._parts.items()}
    
    @property
    def is_busy(self):
        """Whether any part is busy"""
        return any(part.is_busy for part in self._parts.values())
    
    @property
    def is_connected(self):
        """Whether all parts are connected"""
        return all(part.is_connected for part in self._parts.values())
    
    @property
    def verbose(self) -> bool:
        """Verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        level = logging.DEBUG if value else logging.INFO
        CustomLevelFilter().setModuleLevel(self._logger.name, level)
        for part in self._parts.values():
            part.verbose = value
        return
    
    @property
    def parts(self) -> SimpleNamespace[str,Part]:
        """Namespace of parts"""
        return SimpleNamespace(**self._parts)
    
    def connect(self):
        """Connect to each component Part"""
        for part in self._parts.values():
            part.connect()
        return
    
    def disconnect(self):
        """Disconnect from each component Part"""
        for part in self._parts.values():
            part.disconnect()
        return
    
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = deepcopy(self._default_flags)
        for part in self._parts.values():
            part.resetFlags()
        return
    
    def shutdown(self):
        """Shutdown each component Part"""
        for part in self._parts.values():
            part.shutdown()
        return
    

class Ensemble(Compound):
    """ 
    Ensemble class is an aggregation of duplicate part tools to form multiple channels.
    Do not instantiate this class directly. Use the `factory` method to generate the desired class first.
    
    ## Constructor:
        `channels` (Sequence[int] | None, optional): sequence of channels. Defaults to None.
        `details` (dict | Sequence[dict] | None, optional): dictionary or sequence of dictionaries of part details. Defaults to None.
        `parts` (dict[str,Part] | None, optional): dictionary of parts. Defaults to None.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
        
    ## Attributes and properties:
        `channels` (dict[int,Part]): dictionary of channels
        `connection_details` (dict): connection details of each part
        `parts` (SimpleNamespace[str,Part]): namespace of parts
        `flags` (SimpleNamespace[str,bool]): flags of class
        `is_busy` (bool): whether any part is busy
        `is_connected` (bool): whether all parts are connected
        `verbose` (bool): verbosity of class
        
    ## Methods:
        `createParts`: factory method to instantiate Ensemble from channels and part details
        `factory`: factory method to generate Ensemble class from parent class
        `fromConfig`: factory method to create Compound from configuration dictionary
        `parallel`: execute function in parallel on all channels
        `connect`: connect to each component Part in parallel
        `disconnect`: disconnect from each component Part
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `shutdown`: shutdown each component Part
    """
    
    _channel_class: type = Part
    _channel_prefix: str = "chn_"
    def __init__(self, 
        channels: Sequence[int]|None = None, 
        details:dict|Sequence[dict]|None = None, 
        *args, 
        parts: dict[str,Part]|None = None, 
        verbose:bool = False, 
        **kwargs
    ):
        """
        Initialise Ensemble class

        Args:
            channels (Sequence[int]): sequence of channels
            details (dict | Sequence[dict]): dictionary or sequence of dictionaries of part details
            parts (dict[str,Part]): dictionary of parts
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        if parts is None:
            parts = self.createParts(channels, details, *args, **kwargs)
        parts = {f"{self._channel_prefix}{chn}":part for chn,part in parts.items()}
        for part in parts.values():
            part._parent = self
        super().__init__(*args, parts=parts, verbose=verbose, **kwargs)
        return
    
    @classmethod
    def createParts(cls, channels: Sequence[int], details:dict|Sequence[dict], *args, **kwargs) -> dict[str,Part]:
        """
        Factory method to instantiate Ensemble from channels and part details

        Args:
            channels (Sequence[int]): sequence of channels
            details (dict | Sequence[dict]): dictionary or sequence of dictionaries of part details

        Returns:
            dict[str,Part]: dictionary of parts
        """
        if isinstance(details,dict):
            details = [details]*len(channels)
        elif isinstance(details,Sequence) and len(details) == 1:
            details = details*len(channels)
        assert len(channels) == len(details), "Ensure the number of channels match the number of part details"
        assert type(cls._channel_class) is type, "Use the `factory` method to generate the desired class first"
        
        parent = cls._channel_class
        parts_list = [parent(final=False, **settings) for settings in details]
        parts = {chn:part for chn,part in zip(channels,parts_list)}
        assert len(channels) == len(parts), "Ensure the number of channels match the number of parts"
        return parts
    
    @classmethod
    def factory(cls, parent: type) -> Type[Ensemble]:
        """
        Factory method to generate Ensemble class from parent class

        Args:
            parent (type): parent class

        Returns:
            Type[Ensemble]: subclass of Ensemble class
        """
        assert inspect.isclass(parent), "Ensure the argument for `parent` is a class"
        attrs = {attr:cls._make_multichannel(getattr(parent,attr)) for attr in dir(parent) if callable(getattr(parent,attr)) and (attr not in dir(cls))}
        attrs.update({"_channel_class":parent})
        new_class = type(f"Multi_{parent.__name__}", (cls,), attrs)
        return new_class
    
    @classmethod
    def fromConfig(cls, config:dict) -> Ensemble:
        """
        Factory method to create Compound from configuration dictionary
        
        Args:
            config (dict): configuration dictionary
            
        Returns:
            Ensemble: instance of Compound (or its subclasses)
        """
        details = config.pop('details')
        if all([isinstance(k,int) for k in details.keys()]):  # If keys are integers
            details = [details[k]['settings'] for k in sorted(details.keys())]
        config['details'] = details
        # parts = factory.load_parts(details)
        instance = cls(**config)
        instance.connect()
        return instance
    
    @property
    def channels(self) -> dict[int,Part]:
        """Dictionary of channels"""
        return {int(chn.replace(self._channel_prefix,"")):part for chn,part in self._parts.items()}
    
    def connect(self):
        """Connect to each component Part in parallel"""
        self.parallel('connect', lambda i,key,part: dict(), channels=list(self.channels.keys()))
        return
    
    def parallel(self, 
        method_name: str, 
        kwargs_generator: Callable[[int,int,Part], dict[str,Any]]|None = None,
        *args, 
        channels: Iterable[int],
        max_workers: int = 4,
        timeout:int|float = 120,
        stagger: int|float = 0.5,
        **kwargs
    ) -> dict[int,Any]:
        """
        Execute function in parallel on all channels
        
        Args:
            method_name (str): method name to be executed
            kwargs_generator (Callable[[int,int,Part], dict[str,Any]]|None): function to generate kwargs for each channel using indices, channels, and Parts. Defaults to None.
            channels (Iterable[int]): channels to execute on
            max_workers (int, optional): maximum number of workers. Defaults to 4.
            timeout (int|float, optional): timeout for each worker. Defaults to 120.
            stagger (int|float, optional): time to wait between each worker. Defaults to 0.5.
            
        Returns:
            dict[int,Any]: dictionary of outputs
        """
        if kwargs_generator is None:
            def kwargs_generator(_i, _key, _part):
                return (dict())
        with ThreadPoolExecutor(max_workers=max_workers) as e:
            futures = {}
            for i,(key,part) in enumerate(self.channels.items()):
                if key not in channels:
                    continue
                if not hasattr(part, method_name):
                    raise AttributeError(f"Method {method_name} not found in {part.__class__.__name__}")
                func: Callable = getattr(part, method_name)
                assert callable(func), f"Ensure {method_name} is a callable method"
                kwargs.update(kwargs_generator(i,key,part))
                future = e.submit(func, *args, **kwargs)
                futures[future] = key
                time.sleep(stagger)
            outs = dict()
            for future in as_completed(futures, timeout=timeout):
                key = futures[future]
                out = future.result()
                self._logger.info(f"Channel {key}: {out}")
                outs[key] = out
        return outs
    
    @classmethod
    def _make_multichannel(cls, method: Callable) -> Callable:
        """
        Make a method multichannel

        Args:
            method (Callable): method to be made multichannel

        Returns:
            Callable: multichannel method
        """
        func_name = method.__name__
        if func_name.endswith("__") and not func_name.startswith("__"):
            return method
        def func(self, *args, channel: int|Sequence[int]|None = None, **kwargs) -> dict|None:
            outs = dict()
            for chn,obj in cls._get_channel(self, channel).items():
                obj_method: Callable = getattr(obj, func_name)
                assert callable(obj_method), f"Ensure {func_name} is a callable method"
                logger.info(f"Executing {func_name} on channel {chn}")
                out = obj_method(*args, **kwargs)
                outs[chn] = out
            if all([o is None for o in outs.values()]):
                return None
            return outs
        
        # Set method name, docstring, signature and annotations
        func.__name__ = func_name
        
        channel_doc = '    channel (int|Sequence[int]|None, optional): select channel(s). Defaults to None.\n\n'
        doc = method.__doc__
        if isinstance(doc, str):
            doc_parts = doc.split('Returns:')
            indent = doc_parts[0].split('\n')[-1]
            if 'Args:' not in doc_parts[0]:
                doc_parts[0] = doc_parts[0] + "Args:\n" + indent
            doc_parts[0] = doc_parts[0] + channel_doc + indent
            doc = 'Returns:'.join(doc_parts) if len(doc_parts) > 1 else doc_parts[0]
        func.__doc__ = doc
        
        signature = inspect.signature(method)
        parameters = list(signature.parameters.values())
        new_parameter = inspect.Parameter('channel', inspect.Parameter.KEYWORD_ONLY, default=None, annotation=int|Sequence[int]|None)
        if inspect.Parameter('kwargs', inspect.Parameter.VAR_KEYWORD) in parameters:
            parameters.insert(-1, new_parameter)
        else:
            parameters.append(new_parameter)
        func.__signature__ = signature.replace(parameters = tuple(parameters))
        return func
    
    def _get_channel(self, channel:int|Sequence[int]|None = None) -> dict[str,Part]:
        """
        Get channel(s)
        
        Args:
            channel (int|Sequence[int]|None, optional): select channel(s). Defaults to None.
            
        Returns:
            dict[str,Part]: dictionary of channel(s)
        """
        if channel is None:
            return self.channels
        elif isinstance(channel, int):
            if channel not in self.channels:
                raise KeyError(f"Channel {channel} not found in {self.channels.keys()}")
            return {channel:self.channels[channel]}
        elif isinstance(channel, Sequence):
            not_found = [str(chn) for chn in channel if chn not in self.channels]
            if not_found:
                raise KeyError(f"Channel(s) {', '.join(not_found)} not found in {self.channels.keys()}")
            return {chn:self.channels[chn] for chn in channel}
        raise ValueError(f"Invalid channel input: {channel}")
    

class Combined:
    """
    Combined class is an composition of multiple part tools.
    Do not instantiate this class directly.
    Subclass this class to create a specific Combined tool.
    
    ## Constructor:
        `parts` (dict[str,Part]): dictionary of parts
        `verbose` (bool, optional): verbosity of class. Defaults to False.
        
    ## Attributes and properties:
        `device` (Device): device object
        `connection_details` (dict): connection details for the device
        `parts` (SimpleNamespace[str,Part]): namespace of parts
        `flags` (SimpleNamespace[str,bool]): flags of class
        `is_busy` (bool): whether any part is busy
        `is_connected` (bool): whether all parts are connected
        `verbose` (bool): verbosity of class
        
    ## Methods:
        `fromConfig`: factory method to create Combined from configuration dictionary
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `shutdown`: shutdown the device
    """
    
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(busy=False, verbose=False)
    def __init__(self, *args, parts: dict[str,Part], verbose:bool = False, **kwargs):
        """
        Initialise Combined class

        Args:
            parts (dict[str,Part]): dictionary of parts
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        self.device: Device = kwargs.get('device', factory.create_from_config(kwargs))
        self._parts = parts
        self.flags = deepcopy(self._default_flags)
        
        self._logger = logger.getChild(f"{self.__class__.__name__}.{id(self)}")
        self.verbose = verbose
        return
    
    def __repr__(self):
        parts = '\n'.join([f"  {name}={part!r}" for name,part in self._parts.items()])
        return f"{super().__repr__()} containing:\n{parts}"
    
    def __str__(self):
        parts = '\n'.join([f"  {name}: {part.__class__.__name__}" for name,part in self._parts.items()])
        _str = f"{self.__class__.__name__} containing:\n{parts}"
        return _str
    
    def __del__(self):
        self.shutdown()
        return
    
    @classmethod
    def fromConfig(cls, config:dict) -> Combined:
        """
        Factory method to create Combined from configuration dictionary
        
        Args:
            config (dict): configuration dictionary
            
        Returns:
            Combined: instance of Combined (or its subclasses)
        """
        details = config.pop('details')
        device = factory.create_from_config(config)
        for part_config in details.values():
            part_config['settings']['device'] = device
        parts = factory.load_parts(details)
        return cls(device=device, parts=parts, **config)
    
    @property
    def connection_details(self):
        """Connection details for the device"""
        return self.device.connection_details
    
    @property
    def is_busy(self):
        """Whether any part is busy"""
        return any(part.is_busy for part in self._parts.values())
    
    @property
    def is_connected(self) -> bool:
        """Whether all parts are connected"""
        return self.device.is_connected
    
    @property
    def verbose(self) -> bool:
        """Verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        level = logging.DEBUG if value else logging.INFO
        CustomLevelFilter().setModuleLevel(self._logger.name, level)
        for part in self._parts.values():
            part.verbose = value
        return
    
    @property
    def parts(self) -> SimpleNamespace[str,Part]:
        """Namespace of parts"""
        return SimpleNamespace(**self._parts)
    
    def connect(self):
        """Connect to the device"""
        self.device.connect()
        return
    
    def disconnect(self):
        """Disconnect from the device"""
        self.device.disconnect()
        return
    
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = deepcopy(self._default_flags)
        for part in self._parts.values():
            part.resetFlags()
        return
    
    def shutdown(self):
        """Shutdown the device"""
        for part in self._parts.values():
            part.shutdown()
        return


class Multichannel(Combined):
    """
    Multichannel class is an composition of duplicate part tools to form multiple channels.
    
    ## Constructor:
        `channels` (Sequence[int] | None, optional): sequence of channels. Defaults to None.
        `details` (dict | Sequence[dict] | None, optional): dictionary or sequence of dictionaries of part details. Defaults to None.
        `parts` (dict[str,Part] | None, optional): dictionary of parts. Defaults to None.
        `verbose` (bool, optional): verbosity of class. Defaults to False.
        
    ## Attributes and properties:
        `channels` (dict[int,Part]): dictionary of channels
        `device` (Device): device object
        `connection_details` (dict): connection details for the device
        `parts` (SimpleNamespace[str,Part]): namespace of parts
        `flags` (SimpleNamespace[str,bool]): flags of class
        `is_busy` (bool): whether any part is busy
        `is_connected` (bool): whether all parts are connected
        `verbose` (bool): verbosity of class
        
    ## Methods:
        `createParts`: factory method to instantiate Multichannel from channels and part details
        `factory`: factory method to generate Multichannel class from parent class
        `fromConfig`: factory method to create Combined from configuration dictionary
        `setActiveChannel`: set active channel
        `connect`: connect to the device
        `disconnect`: disconnect from the device
        `resetFlags`: reset all flags to class attribute `_default_flags`
        `shutdown`: shutdown the device
    """
    
    _channel_class: type = Part
    _channel_prefix: str = "chn_"
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(busy=False, verbose=False)
    def __init__(self, 
        channels: Sequence[int]|None = None, 
        details:dict|Sequence[dict]|None = None, 
        *args, 
        parts: dict[str,Part]|None = None, 
        verbose:bool = False, 
        **kwargs 
    ):
        """
        Initialise Multichannel class
        
        Args:
            channels (Sequence[int] | None, optional): sequence of channels. Defaults to None.
            details (dict | Sequence[dict] | None, optional): dictionary or sequence of dictionaries of part details. DEfaults to None.
            parts (dict[str,Part] | None, optional): dictionary of parts. Defaults to None.
            verbose (bool, optional): verbosity of class. Defaults to False.
        """
        if parts is None:
            parts, device = self.createParts(channels, details, *args, **kwargs)
            kwargs['device'] = device
        parts = {f"{self._channel_prefix}{chn}":part for chn,part in parts.items()}
        for part in parts.values():
            part._parent = self
        super().__init__(*args, parts=parts, verbose=verbose, **kwargs)
        
        self.active_channel = None
        self.setActiveChannel()
        return
    
    @classmethod
    def createParts(cls, channels: Sequence[int], details:dict|Sequence[dict]|None, *args, **kwargs) -> tuple[dict[str,Part],Device]:
        """
        Factory method to instantiate Multichannel from channels and part details
        
        Args:
            channels (Sequence[int]): sequence of channels
            details (dict | Sequence[dict]|None): dictionary or sequence of dictionaries of part details
            
        Returns:
            tuple[dict[str,Part],Device]: dictionary of parts and device
        """
        details = dict() if details is None else details
        if isinstance(details,dict):
            details = [details.copy() for _ in range(len(channels))]
            for d,c in zip(details,channels):
                d['channel'] = c
        elif isinstance(details,Sequence) and len(details) == 1:
            details = details*len(channels)
        assert len(channels) == len(details), "Ensure the number of channels match the number of part details"
        assert type(cls._channel_class) is type, "Use the `factory` method to generate the desired class first"
        
        parent = cls._channel_class
        parts_list: list[Part] = []
        for i,settings in enumerate(details):
            if i == 0:
                part: Part = parent(**settings)
                device = part.device
            else:
                settings['device'] = device
                part: Part = parent(**settings)
            parts_list.append(part)
        # parts_list = [parent(**settings) for settings in details]
        parts = {chn:part for chn,part in zip(channels,parts_list)}
        assert len(channels) == len(parts), "Ensure the number of channels match the number of parts"
        return parts, device
    
    @classmethod
    def factory(cls, parent: type) -> Type[Multichannel]:
        """
        Factory method to generate Multichannel class from parent
        
        Args:
            parent (type): parent class
            
        Returns:
            Type[Multichannel]: subclass of Multichannel class
        """
        assert inspect.isclass(parent), "Ensure the argument for `parent` is a class"
        attrs = {attr:cls._make_multichannel(getattr(parent,attr)) for attr in dir(parent) if callable(getattr(parent,attr)) and (attr not in dir(cls))}
        attrs.update({"_channel_class":parent})
        new_class = type(f"Multi_{parent.__name__}", (cls,), attrs)
        return new_class
    
    @classmethod
    def fromConfig(cls, config:dict) -> Multichannel:
        """
        Factory method to create Compound from configuration dictionary
        
        Args:
            config (dict): configuration dictionary
            
        Returns:
            Multichannel: instance of Compound (or its subclasses)
        """
        details = config.pop('details')
        if all([isinstance(k,int) for k in details.keys()]):  # If keys are integers
            details = [details[k]['settings'] for k in sorted(details.keys())]
        config['details'] = details
        # parts = factory.load_parts(details)
        instance = cls(**config)
        instance.connect()
        return instance
    
    @property
    def channel(self) -> int:
        """Active channel"""
        return self.active_channel
    @channel.setter
    def channel(self, value:int):
        self.setActiveChannel(value)
        return
    
    @property
    def channels(self) -> dict[int,Part]:
        """Dictionary of channels"""
        return {int(chn.replace(self._channel_prefix,"")):part for chn,part in self._parts.items()}
    
    @classmethod
    def _make_multichannel(cls, method: Callable) -> Callable:
        """
        Make a method multichannel
        
        Args:
            method (Callable): method to be made multichannel
            
        Returns:
            Callable: multichannel method
        """
        func_name = method.__name__
        if func_name.endswith("__") and not func_name.startswith("__"):
            return method
        def func(self, *args, channel: int|Sequence[int]|None = None, **kwargs) -> dict|None:
            outs = dict()
            for chn,obj in cls._get_channel(self, channel).items():
                cls.setActiveChannel(self, chn)
                obj_method: Callable = getattr(obj, func_name)
                assert callable(obj_method), f"Ensure {func_name} is a callable method"
                logger.info(f"Executing {func_name} on channel {chn}")
                out = obj_method(*args, **kwargs)
                outs[chn] = out
                time.sleep(0.1)
            if all([o is None for o in outs.values()]):  # If all outputs are None
                return None # Return None
            return outs
        
        # Set method name, docstring, signature and annotations
        func.__name__ = func_name
        
        channel_doc = '    channel (int|Sequence[int]|None, optional): select channel(s). Defaults to None.\n\n'
        doc = method.__doc__
        if isinstance(doc, str):
            doc_parts = doc.split('Returns:')
            indent = doc_parts[0].split('\n')[-1]
            if 'Args:' not in doc_parts[0]:
                doc_parts[0] = doc_parts[0] + "Args:\n" + indent
            doc_parts[0] = doc_parts[0] + channel_doc + indent
            doc = 'Returns:'.join(doc_parts) if len(doc_parts) > 1 else doc_parts[0]
        func.__doc__ = doc
        
        signature = inspect.signature(method)
        parameters = list(signature.parameters.values())
        new_parameter = inspect.Parameter('channel', inspect.Parameter.KEYWORD_ONLY, default=None, annotation=int|Sequence[int]|None)
        if inspect.Parameter('kwargs', inspect.Parameter.VAR_KEYWORD) in parameters:
            parameters.insert(-1, new_parameter)
        else:
            parameters.append(new_parameter)
        func.__signature__ = signature.replace(parameters = tuple(parameters))
        return func
    
    def setActiveChannel(self, channel:int|None = None):
        """
        Set active channel
        
        Args:
            channel (int|None, optional): select channel. Defaults to None.
        """
        if channel is None:
            self.active_channel = list(self.channels.keys())[0]
            return
        if channel not in self.channels:
            raise KeyError(f"Channel {channel} not found in {self.channels.keys()}")
        self.active_channel = channel
        return
    
    def _get_channel(self, channel:int|Sequence[int]|None = None) -> dict[str,Part]:
        """
        Get channel(s)
        
        Args:
            channel (int|Sequence[int]|None, optional): select channel(s). Defaults to None.
            
        Returns:
            dict[str,Part]: dictionary of channel(s)
        """
        if channel is None:
            return self.channels
        elif isinstance(channel, int):
            if channel not in self.channels:
                raise KeyError(f"Channel {channel} not found in {self.channels.keys()}")
            return {channel:self.channels[channel]}
        elif isinstance(channel, Sequence):
            not_found = [str(chn) for chn in channel if chn not in self.channels]
            if not_found:
                raise KeyError(f"Channel(s) {', '.join(not_found)} not found in {self.channels.keys()}")
            return {chn:self.channels[chn] for chn in channel}
        raise ValueError(f"Invalid channel input: {channel}")
    