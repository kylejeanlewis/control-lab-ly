# -*- coding: utf-8 -*-
# Standard library imports
from __future__ import annotations
import ast
import json
import pickle
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
    def encodeData(data: dict[str, Any]) -> Message|str|bytes:
        try:
            package = json.dumps(data).encode('utf-8')
        except TypeError:
            content = data.pop('data')
            data.update(dict(pickled = str(pickle.dumps(content))))
            package = json.dumps(data).encode('utf-8')
        return package
    
    @staticmethod
    def encodeRequest(command: Mapping[str, Any]) -> Message|str|bytes:
        request = json.dumps(command).encode('utf-8')
        return request
    
    @staticmethod
    def decodeData(package: Message|str|bytes) -> Any:
        data: dict[str, Any] = json.loads(package)
        if 'data' not in data and 'pickled' in data:
            pickled = data.pop('pickled')
            data.update(dict(data = pickle.loads(ast.literal_eval(pickled))))
        return data
    