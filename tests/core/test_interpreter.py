import pytest
import json
import pickle
import numpy as np
from scipy.spatial.transform import Rotation
from unittest.mock import MagicMock
from controllably.core.interpreter import Interpreter, JSONInterpreter, Message
from controllably.core.position import Position

# fixture for interpreter
@pytest.fixture
def interpreter():
    return Interpreter()

# fixture for json interpreter
@pytest.fixture
def json_interpreter():
    return JSONInterpreter()

mock_request = {
    "object_id": "",
    "method": "",
    "args": [""],
    "kwargs": {"":""},
    "address": {"sender": [""], "target": [""]},
    "request_id": "",
    "priority": False,
    "rank": None
}
mock_data = {
    "data": None,
    "status": "",
    "address": {"sender": [""], "target": [""]},
    "request_id": "",
    "reply_id": "",
    "priority": False,
    "rank": None
}

def test_interpreter_init(interpreter):
    assert isinstance(interpreter, Interpreter)
    
def test_json_interpreter_init(json_interpreter):
    assert isinstance(json_interpreter, JSONInterpreter)

def test_interpreter_encode_decode_request():
    encoded = Interpreter.encodeRequest(mock_request)
    decoded = Interpreter.decodeRequest(encoded)
    assert decoded == mock_request

def test_interpreter_encode_decode_data():
    encoded = Interpreter.encodeData(mock_data)
    decoded = Interpreter.decodeData(encoded)
    assert decoded == mock_data

def test_json_interpreter_encode_decode_request():
    encoded = JSONInterpreter.encodeRequest(mock_request)
    decoded = JSONInterpreter.decodeRequest(encoded)
    assert decoded == mock_request

def test_json_interpreter_encode_decode_data():
    encoded = JSONInterpreter.encodeData(mock_data)
    decoded = JSONInterpreter.decodeData(encoded)
    assert decoded == mock_data

def test_json_interpreter_encode_decode_data_with_position():
    rotation = Rotation.from_euler('xyz', [4, 5, 6], degrees=True)
    position = Position([1, 2, 3], rotation)
    data = mock_data.copy()
    data["data"] = position
    encoded = JSONInterpreter.encodeData(data)
    decoded = JSONInterpreter.decodeData(encoded)
    assert isinstance(decoded["data"], Position)
    assert decoded == data

def test_json_interpreter_encode_decode_data_with_pickle():
    array = np.array([1, 2, 3])
    data = mock_data.copy()
    data["data"] = array
    encoded = JSONInterpreter.encodeData(data)
    decoded = JSONInterpreter.decodeData(encoded)
    assert isinstance(decoded["data"], np.ndarray)
    decoded_array = decoded.pop("data")
    assert np.array_equal(decoded_array, array)
    data.pop("data")
    assert decoded == data
