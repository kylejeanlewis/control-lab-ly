# -*- coding: utf-8 -*-
""" 
This module contains the `Interpreter` abstract class and its implementation `JSONInterpreter`.

## Classes:
    `Interpreter`: Abstract class for encoding and decoding messages.
    `JSONInterpreter`: Class for encoding and decoding messages in JSON format.

<i>Documentation last updated: 2025-02-22</i>
"""
# Standard library imports
from __future__ import annotations
import ast
import json
import pickle
from typing import Protocol, Mapping, Any

# Local application imports
from .position import Position

class Message(Protocol):
    ...
    
class Interpreter:
    """
    Abstract class for encoding and decoding messages.
    
    ### Methods:
        `decodeRequest`: Decode a request message into a command dictionary.
        `encodeData`: Encode data into a message.
        `encodeRequest`: Encode a command dictionary into a request message.
        `decodeData`: Decode a message into data.
    """
    
    def __init__(self):
        return
    
    @staticmethod
    def decodeRequest(packet: Message) -> dict[str, Any]:
        """
        Decode a request message into a command dictionary.
        
        Args:
            packet (Message): request message
            
        Returns:
            dict[str, Any]: command dictionary
        """
        command = packet
        return command
    
    @staticmethod
    def encodeData(data: Any) -> Message:
        """
        Encode data into a message.
        
        Args:
            data (Any): data to be encoded
            
        Returns:
            Message: encoded message
        """
        package = data
        return package
    
    @staticmethod
    def encodeRequest(command: Mapping[str, Any]) -> Message:
        """
        Encode a command dictionary into a request message.
        
        Args:
            command (Mapping[str, Any]): command dictionary
            
        Returns:
            Message: request message
        """
        request = command
        return request
    
    @staticmethod
    def decodeData(packet: Message) -> Any:
        """
        Decode a message into data.
        
        Args:
            packet (Message): message to be decoded
            
        Returns:
            Any: decoded data
        """
        data = packet
        return data
    
    
class JSONInterpreter(Interpreter):
    """
    Class for encoding and decoding messages in JSON format.
    
    ### Methods:
        `decodeRequest`: Decode a request message into a command dictionary.
        `encodeData`: Encode data into a message.
        `encodeRequest`: Encode a command dictionary into a request message.
        `decodeData`: Decode a message into data
    """
    
    def __init__(self):
        return
    
    @staticmethod
    def decodeRequest(packet: Message|str|bytes) -> dict[str, Any]:
        """
        Decode a request message into a command dictionary.
        
        Args:
            packet (Message|str|bytes): request message
            
        Returns:
            dict[str, Any]: command dictionary
        """
        command = json.loads(packet)
        return command
    
    @staticmethod
    def encodeData(data: dict[str, Any]) -> Message|str|bytes:
        """
        Encode data into a message.
        
        Args:
            data (dict[str, Any]): data to be encoded
            
        Returns:
            Message|str|bytes: encoded message
        """
        data = data.copy()
        for k,v in data.items():
            if isinstance(v, Position):
                data[k] = v.toJSON()
        try:
            package = json.dumps(data).encode('utf-8')
        except TypeError:
            content = data.pop('data')
            data.update(dict(pickled = str(pickle.dumps(content))))
            package = json.dumps(data).encode('utf-8')
        return package
    
    @staticmethod
    def encodeRequest(command: Mapping[str, Any]) -> Message|str|bytes:
        """
        Encode a command dictionary into a request message.
        
        Args:
            command (Mapping[str, Any]): command dictionary
            
        Returns:
            Message|str|bytes: request message
        """
        request = json.dumps(command).encode('utf-8')
        return request
    
    @staticmethod
    def decodeData(packet: Message|str|bytes) -> Any:
        """
        Decode a message into data.
        
        Args:
            packet (Message|str|bytes): message to be decoded
            
        Returns:
            Any: decoded data
        """
        data: dict[str, Any] = json.loads(packet)
        if 'data' not in data and 'pickled' in data:
            pickled = data.pop('pickled')
            data.update(dict(data = pickle.loads(ast.literal_eval(pickled))))
        elif 'data' in data:
            for k,v in data.items():
                if isinstance(v, str) and v.startswith('Position('):
                    data[k] = Position.fromJSON(v)
        return data
    