# -*- coding: utf-8 -*-
""" 
This module contains the `Interpreter` abstract class and its implementation `JSONInterpreter`.

## Classes:
    `Interpreter`: Abstract class for encoding and decoding messages.
    `JSONInterpreter`: Class for encoding and decoding messages in JSON format.

<i>Documentation last updated: 2025-06-11</i>
"""
# Standard library imports
from __future__ import annotations
import ast
import json
import pickle
from typing import Mapping, Any

# Third party imports
import pandas as pd

# Local application imports
from .position import Position

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
    def decodeRequest(packet: str|bytes) -> dict[str, Any]:
        """
        Decode a request message into a command dictionary.
        
        Args:
            packet (str|bytes): request message to be decoded
            
        Returns:
            dict[str, Any]: command dictionary
        """
        command = packet
        return command
    
    @staticmethod
    def encodeData(data: Any) -> bytes:
        """
        Encode data into a message.
        
        Args:
            data (Any): data to be encoded
            
        Returns:
            bytes: encoded message in bytes
        """
        packet = data
        return packet
    
    @staticmethod
    def encodeRequest(command: Mapping[str, Any]) -> bytes:
        """
        Encode a command dictionary into a request message.
        
        Args:
            command (Mapping[str, Any]): command dictionary
            
        Returns:
            bytes: request message in bytes
        """
        request = command
        return request
    
    @staticmethod
    def decodeData(packet: str|bytes) -> dict[str, Any]:
        """
        Decode a message into data.
        
        Args:
            packet (str|bytes): message to be decoded
            
        Returns:
            dict[str, Any]: decoded data
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
    def decodeRequest(packet: str|bytes) -> dict[str, Any]:
        """
        Decode a request message into a command dictionary.
        
        Args:
            packet (str|bytes): request message
            
        Returns:
            dict[str, Any]: command dictionary
        """
        command = json.loads(packet)
        return command
    
    @staticmethod
    def encodeData(data: Mapping[str, Any]) -> bytes:
        """
        Encode data into a message.
        
        Args:
            data (Mapping[str, Any]): data to be encoded
            
        Returns:
            bytes: encoded message
        """
        data = data.copy()
        for k,v in data.items():
            # Convert objects to JSON strings
            if isinstance(v, Position):
                data[k] = v.toJSON()
            elif isinstance(v, (pd.DataFrame, pd.Series)):
                data[k] = v.to_json(orient='table')
        try:
            packet = json.dumps(data).encode('utf-8')
        except TypeError:
            content = data.pop('data')
            data.update(dict(pickled = str(pickle.dumps(content))))
            packet = json.dumps(data).encode('utf-8')
        return packet
    
    @staticmethod
    def encodeRequest(command: Mapping[str, Any]) -> bytes:
        """
        Encode a command dictionary into a request message.
        
        Args:
            command (Mapping[str, Any]): command dictionary
            
        Returns:
            bytes: request message
        """
        request = json.dumps(command).encode('utf-8')
        return request
    
    @staticmethod
    def decodeData(packet: str|bytes) -> dict[str, Any]:
        """
        Decode a message into data.
        
        Args:
            packet (str|bytes): message to be decoded
            
        Returns:
            dict[str, Any]: decoded data
        """
        data: dict[str, Any] = json.loads(packet)
        if 'data' not in data and 'pickled' in data:
            pickled = data.pop('pickled')
            data.update(dict(data = pickle.loads(ast.literal_eval(pickled))))
        elif 'data' in data:
            for k,v in data.items():
                # Convert JSON strings to objects
                if isinstance(v, str) and v.startswith('Position('):
                    data[k] = Position.fromJSON(v)
                if isinstance(v, str) and v.startswith('{"schema":'):
                    data[k] = pd.read_json(v, orient='table')
        return data
    