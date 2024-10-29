# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
from copy import deepcopy
import inspect
import logging
from types import SimpleNamespace
from typing import Protocol, Callable, Sequence

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

class Part(Protocol):
    connection_details: dict
    is_busy: bool
    is_connected: bool
    verbose: bool
    def connect(self):
        """Connect to the device"""
        raise NotImplementedError
    
    def disconnect(self):
        """Disconnect from the device"""
        raise NotImplementedError
    
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        raise NotImplementedError

    def shutdown(self):
        """Shutdown the device"""
        raise NotImplementedError


class Compound:
    _default_flags: SimpleNamespace[str,bool] = SimpleNamespace(verbose=False)
    def __init__(self, *args, parts: dict[str,Part], verbose:bool = False, **kwargs):
        self.parts: SimpleNamespace[str,Part] = SimpleNamespace(**parts)
        self.flags = deepcopy(self._default_flags)
        self.verbose = verbose
        return
    
    def __repr__(self):
        parts = '\n'.join([f"  {name}={part!r}" for name,part in vars(self.parts).items()])
        return f"{super().__repr__()} containing:\n{parts}"
    
    def __str__(self):
        parts = '\n'.join([f"  {name}: {part.__class__.__name__}" for name,part in vars(self.parts).items()])
        _str = f"{self.__class__.__name__} containing:\n{parts}"
        return _str
    
    def __del__(self):
        self.shutdown()
        return
    
    @classmethod
    def fromConfig(cls, config:dict):
        details = config.pop('details')
        parts = {name:Part(**detail) for name,detail in details.items()}
        return cls(parts=parts, **config)
    
    @property
    def connection_details(self):
        return {name:part.connection_details for name,part in vars(self.parts).items()}
    
    @property
    def is_busy(self):
        return any(part.is_busy for part in vars(self.parts).values())
    
    @property
    def is_connected(self):
        return all(part.is_connected for part in vars(self.parts).values())
    
    @property
    def verbose(self) -> bool:
        """Get verbosity of class"""
        return self.flags.verbose
    @verbose.setter
    def verbose(self, value:bool):
        """Set verbosity of class"""
        assert isinstance(value,bool), "Ensure assigned verbosity is boolean"
        self.flags.verbose = value
        for part in vars(self.parts).values():
            part.verbose = value
        level = logging.INFO if value else logging.WARNING
        logger.setLevel(level)
        for handler in logger.handlers:
            if isinstance(handler, type(logging.StreamHandler())):
                handler.setLevel(level)
        return
    
    def connect(self):
        for part in vars(self.parts).values():
            part.connect()
        return
    
    def disconnect(self):
        for part in vars(self.parts).values():
            part.disconnect()
        return
    
    def resetFlags(self):
        """Reset all flags to class attribute `_default_flags`"""
        self.flags = deepcopy(self._default_flags)
        for part in vars(self.parts).values():
            part.resetFlags()
        return
    
    def shutdown(self):
        for part in vars(self.parts).values():
            part.shutdown()
        return
    

class Multichannel(Compound):
    _channel_class: Part = Part
    _channel_prefix: str = "chn_"
    def __init__(self, *args, parts: dict[str,Part], verbose:bool = False, **kwargs):
        parts = {f"{self._channel_prefix}{chn}":part for chn,part in parts.items()}
        super().__init__(*args, parts=parts, verbose=verbose, **kwargs)
        return
    
    @classmethod
    def create(cls, channels: Sequence[int], details:dict|Sequence[dict], *args, **kwargs):
        if isinstance(details,dict):
            details = [details]*len(channels)
        elif isinstance(details,Sequence) and len(details) == 1:
            details = details*len(channels)
        assert len(channels) == len(details), "Ensure the number of channels match the number of part details"
        
        assert type(cls._channel_class) == type, "Use the `factory` method to generate the desired class first"
        
        primary = cls._channel_class
        parts_list = [primary(**detail) for detail in details]
        parts = {chn:part for chn,part in zip(channels,parts_list)}
        assert len(channels) == len(parts), "Ensure the number of channels match the number of parts"
        return cls(parts=parts, **kwargs)
    
    @classmethod
    def factory(cls, primary: type) -> Multichannel:
        assert inspect.isclass(primary), "Ensure the argument for `primary` is a class"
        attrs = {attr:cls._make_multichannel(getattr(primary,attr)) for attr in dir(primary) if callable(getattr(primary,attr)) and (attr not in dir(cls))}
        attrs.update({"_channel_class":primary})
        new_class = type(f"Multi_{primary.__name__}", (cls,), attrs)
        return new_class
    
    @property
    def channels(self) -> dict[int,Part]:
        return {int(chn.replace(self._channel_prefix,"")):part for chn,part in vars(self.parts).items()}
    
    @classmethod
    def _make_multichannel(cls, function: Callable) -> Callable:
        func_name = function.__name__
        def func(self, *args, channel: int|Sequence[int]|None = None, **kwargs):
            outs = []
            for chn,obj in cls._get_channel(self, channel).items():
                logger.info(f"Executing {func_name} on channel {chn}")
                function = getattr(obj, func_name)
                out = function(*args, **kwargs)
                outs.append(out)
            if all([o is None for o in outs]):
                return None
            return outs
        
        # Set function name, docstring, signature and annotations
        func.__name__ = func_name
        
        channel_doc = '    channel (int|Sequence[int]|None, optional): select channel(s). Defaults to None.\n\n'
        doc = function.__doc__
        if isinstance(doc, str):
            doc_parts = doc.split('Returns:')
            indent = doc_parts[0].split('\n')[-1]
            if 'Args:' not in doc_parts[0]:
                doc_parts[0] = doc_parts[0] + "Args:\n" + indent
            doc_parts[0] = doc_parts[0] + channel_doc + indent
            doc = 'Returns:'.join(doc_parts) if len(doc_parts) > 1 else doc_parts[0]
        func.__doc__ = doc
        
        signature = inspect.signature(function)
        parameters = list(signature.parameters.values())
        new_parameter = inspect.Parameter('channel', inspect.Parameter.KEYWORD_ONLY, default=None, annotation=int|Sequence[int]|None)
        if inspect.Parameter('kwargs', inspect.Parameter.VAR_KEYWORD) in parameters:
            parameters.insert(-1, new_parameter)
        else:
            parameters.append(new_parameter)
        func.__signature__ = signature.replace(parameters = tuple(parameters))
        return func
    
    def _get_channel(self, channel:int|Sequence[int]|None = None) -> dict[str,Part]:
        if channel is None:
            return self.channels
        elif isinstance(channel, int):
            if channel not in self.channels:
                raise ValueError(f"Channel {channel} not found in {self.channels.keys()}")
            return {channel:self.channels[channel]}
        elif isinstance(channel, Sequence):
            not_found = [chn for chn in channel if chn not in self.channels]
            if not_found:
                raise ValueError(f"Channel(s) {', '.join(not_found)} not found in {self.channels.keys()}")
            return {chn:self.channels[chn] for chn in channel}
