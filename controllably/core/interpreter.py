# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import json
from typing import Protocol, Mapping, Any

class Message(Protocol):
    ...
    
class Interpreter:
    def __init__(self):
        return
    
    @staticmethod
    def decodeRequest(request: Message) -> dict[str, Any]:
        command = request
        return command
    
    @staticmethod
    def encodeData(data: Any) -> Message:
        package = data
        return package
    
    @staticmethod
    def encodeRequest(command: Mapping[str, Any]) -> Message:
        request = command
        return request
    
    @staticmethod
    def decodeData(package: Message) -> Any:
        data = package
        return data
    
    
class JSONInterpreter(Interpreter):
    def __init__(self):
        return
    
    @staticmethod
    def decodeRequest(request: Message|str|bytes) -> dict[str, Any]:
        command = json.loads(request)
        return command
    
    @staticmethod
    def encodeData(data: Any) -> Message|str|bytes:
        try:
            package = json.dumps(data).encode('utf-8')
        except TypeError:
            data.update(dict(data=f"{data['data'].__class__.__name__}[{data['data']!r}]"))
            package = json.dumps(data).encode('utf-8')
        return package
    
    @staticmethod
    def encodeRequest(command: Mapping[str, Any]) -> Message|str|bytes:
        request = json.dumps(command).encode('utf-8')
        return request
    
    @staticmethod
    def decodeData(package: Message|str|bytes) -> Any:
        data = json.loads(package)
        return data