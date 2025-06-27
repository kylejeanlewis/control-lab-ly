import pytest
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import yaml

from ..context import controllably
from controllably.core.factory import (
    create, create_from_config, dict_to_named_tuple, dict_to_simple_namespace, get_class,
    get_imported_modules, get_method_names, get_plans, get_setup, load_parts,
    load_setup_from_files, parse_configs, zip_kwargs_to_dict
)
from controllably.core.compound import Compound, Ensemble, Combined, Multichannel
from controllably.core.device import SerialDevice, SocketDevice

from .examples import mock_module

HERE = os.environ.get("REPO_ROOT") or Path(__file__).parent.parent.absolute()

@pytest.mark.parametrize("error, class_, kwargs", [
    (True, mock_module.TestClassError, {'a':1, 'b':2}),
    (False, mock_module.TestClass, {'a':1, 'b':2})
])
def test_create(error, class_, kwargs):
    if error:
        with pytest.raises(TypeError):
            obj = create(class_, **kwargs)
    else:
        obj = create(class_, **kwargs)
        assert isinstance(obj, mock_module.TestClass)
        assert obj.a == 1
        assert obj.b == 2

def test_create_compound(monkeypatch):
    mock_modules = sys.modules
    mock_modules.update(dict(mock_module=mock_module))
    monkeypatch.setattr('sys.modules', mock_modules)
    kwargs = {
        'details': {
            'part01': {
                'module':'mock_module', 
                'class':'TestClass',
                'settings':{'ip_address':'192.0.0.1'}},
            'part02': {
                'module':'mock_module', 
                'class':'TestClass',
                'settings':{'setting_D':2}}
        }
    }
    obj = create(mock_module.TestCompoundClass, **kwargs)
    assert isinstance(obj, mock_module.TestCompoundClass)
    assert issubclass(obj.__class__, Compound)
    assert obj.a == 0
    assert obj.b == 1
    assert isinstance(obj.parts.part01, mock_module.TestClass)
    assert obj.parts.part01.ip_address == '192.0.0.1'
    assert isinstance(obj.parts.part02, mock_module.TestClass)
    assert obj.parts.part02.setting_D == 2

@pytest.mark.parametrize("config, class_", [
    ({'device_type': mock_module.TestClass, 'a': 1, 'b': 2}, "TestClass"),
    ({'baudrate': 9600, 'port': 'COM3', 'timeout': 1}, "SerialDevice"),
    ({'host': 'localhost', 'port': 8080, 'timeout': 1}, "SocketDevice")
])
def test_create_from_config(config, class_):
    obj = create_from_config(config)
    match class_:
        case "SerialDevice":
            assert isinstance(obj, SerialDevice)
            assert obj.port == 'COM3'
            assert obj.baudrate == 9600
            assert obj.timeout == 1
        case "SocketDevice":
            assert isinstance(obj, SocketDevice)
            assert obj.host == 'localhost'
            assert obj.port == 8080
            assert obj.timeout == 1
        case _:
            assert isinstance(obj, mock_module.TestClass)
            assert obj.a == 1
            assert obj.b == 2
    
def test_dict_to_named_tuple():
    d = {'a': 1, 'b': 2}
    nt = dict_to_named_tuple(d, 'TestTuple')
    assert nt.__class__.__name__ == 'TestTuple'
    assert nt.a == 1
    assert nt.b == 2

def test_dict_to_simple_namespace():
    d = {'a': 1, 'b': 2}
    ns = dict_to_simple_namespace(d)
    assert ns.__class__ == SimpleNamespace
    assert ns.a == 1
    assert ns.b == 2

@pytest.mark.parametrize("module, class_", [
    ('mock_module', 'TestClass'),
    ('mock_module_not_exist', 'TestClass'),
    ('mock_module', 'TestClassNotExist')
])
def test_get_class(module, class_, monkeypatch):
    new_modules = sys.modules
    new_modules.update(dict(mock_module=mock_module))
    monkeypatch.setattr('sys.modules', new_modules)
    if module == 'mock_module_not_exist':
        with pytest.raises(ModuleNotFoundError):
            _ = get_class(module, class_)
    elif class_ == 'TestClassNotExist':
        with pytest.raises(AttributeError):
            _ = get_class(module, class_)
    else:
        cls = get_class(module, class_)
        assert cls == mock_module.TestClass

def test_get_imported_modules():
    modules = get_imported_modules('controllably')
    assert 'controllably' in modules
    
    modules = get_imported_modules(['controllably', 'pytest'])
    assert 'controllably' in modules
    assert 'pytest' in modules
    
    modules = get_imported_modules()
    assert 'controllably' in modules
    assert 'pytest' not in modules

def test_get_method_names():
    methods = get_method_names(mock_module.TestClass)
    assert 'shutdown' in methods
    assert 'method2' not in methods

def test_get_plans():
    configs = {'config1': {'settings': {}}}
    registry = {'machine_id': {'123456': {'port': 'COM3'}}}
    plans = get_plans(configs, registry)
    assert 'config1' in plans

@pytest.mark.parametrize("config, use_platform", [
    ({'tool': mock_module.TestClass()}, False),
    ({'tool': mock_module.TestClass()}, True),
    ({'tool': mock_module.TestClass(), 'error':Exception()}, False)
])
def test_get_setup(config, use_platform, monkeypatch):
    monkeypatch.setattr('controllably.core.factory.load_setup_from_files', lambda *args,**kwargs: dict_to_named_tuple(config, 'TestClasses'))
    monkeypatch.setattr('os.getcwd', lambda : str(Path(HERE).parent))
    @dataclass
    class Platform:
        tool: mock_module.TestClass
    platform = Platform if use_platform else None
    if 'error' not in config:
        setup = get_setup('config.yaml', 'registry.yaml', platform)
        if use_platform:
            assert isinstance(setup, Platform)
            assert isinstance(setup.tool, mock_module.TestClass)
        else:
            assert setup.__class__.__name__ == 'TestClasses'
            assert isinstance(setup[0], mock_module.TestClass)
            assert 'tool' in setup._fields
            assert isinstance(setup.tool, mock_module.TestClass)
    else:
        with pytest.raises(RuntimeError):
            _ = get_setup('config_file', 'registry_file')

def test_load_parts(monkeypatch, caplog):
    new_modules = sys.modules
    new_modules.update(dict(mock_module=mock_module))
    monkeypatch.setattr('sys.modules', new_modules)
    monkeypatch.setattr('os.getcwd', lambda : str(Path(HERE).parent))
    config_file = 'control-lab-ly/tests/core/examples/tool.yaml'
    config_file = controllably.core.file_handler.resolve_repo_filepath(config_file)
    with open(config_file, 'r') as f:
        configs = yaml.safe_load(f)
    with caplog.at_level(logging.ERROR):
        parts = load_parts(configs)
        assert 'Device02' in parts
        assert isinstance(parts['DeviceFail'], Exception)

def test_load_setup_from_files(monkeypatch, caplog):
    new_modules = sys.modules
    new_modules.update(dict(mock_module=mock_module))
    monkeypatch.setattr('sys.modules', new_modules)
    monkeypatch.setattr('os.getcwd', lambda : str(Path(HERE).parent))
    monkeypatch.setattr('controllably.core.connection.get_node', lambda _: '012345678901234')
    config_file = 'control-lab-ly/tests/core/examples/tool.yaml'
    config_file = controllably.core.file_handler.resolve_repo_filepath(config_file)
    registry_file = 'control-lab-ly/tests/core/examples/registry.yaml'
    registry_file = controllably.core.file_handler.resolve_repo_filepath(registry_file)
    
    with caplog.at_level(logging.WARNING):
        setup = load_setup_from_files(config_file, registry_file, create_tuple=False)
        assert 'Device01' in setup
        assert 'Device02' in setup
        assert 'Device04' in setup
        assert 'shortcut1' in setup
        assert 'shortcut2' in setup
        assert 'shortcut3' not in setup
        assert 'Tool does not exist' in caplog.text
        assert 'shortcut4' not in setup
        assert 'does not have parts' in caplog.text
    
    setup = load_setup_from_files(config_file, registry_file)
    device1,device2,device4,_,_,shortcut1,shortcut2 = setup
    assert isinstance(device1, mock_module.TestClass)
    assert device1.port == 'COM2'
    assert device1.setting_A == (300,0,200)
    assert np.allclose(device1.setting_B, np.array([[0,1,0],[-1,0,0]]))
    
    assert isinstance(device2, mock_module.TestCompoundClass)
    assert isinstance(device2.parts.part01, mock_module.TestClass)
    assert isinstance(shortcut1, mock_module.TestClass)
    assert device2.parts.part01 == shortcut1
    assert shortcut1.ip_address == '192.0.0.1'
    
    assert isinstance(device2.parts.part02, mock_module.TestClass)
    assert isinstance(shortcut2, mock_module.TestClass)
    assert device2.parts.part02 == shortcut2
    assert shortcut2.setting_D == 2
    
    assert isinstance(device4, mock_module.TestCombinedClass)
    assert isinstance(device4.parts.part01, mock_module.TestClass)
    assert device4.parts.part01.name == 'part1'
    assert device4.parts.part02.name == 'part2'
    
def test_parse_configs(monkeypatch):
    monkeypatch.setattr('os.getcwd', lambda : str(Path(HERE).parent))
    config_file = 'control-lab-ly/tests/core/examples/tool.yaml'
    config_file = controllably.core.file_handler.resolve_repo_filepath(config_file)
    registry_file = 'control-lab-ly/tests/core/examples/registry.yaml'
    registry_file = controllably.core.file_handler.resolve_repo_filepath(registry_file)
    with open(config_file, 'r') as f:
        configs = yaml.safe_load(f)
    with open(registry_file, 'r') as f:
        addresses = yaml.safe_load(f)
    parsed_configs = parse_configs(configs, addresses['machine_id']['012345678901234'])
    assert parsed_configs['Device01']['settings']['port'] == 'COM2'
    assert parsed_configs['Device01']['settings']['setting_A'] == (300,0,200)
    assert np.allclose(parsed_configs['Device01']['settings']['setting_B'], np.array([[0,1,0],[-1,0,0]]))
    assert parsed_configs['Device02']['settings']['details']['part01']['settings']['ip_address'] == '192.0.0.1'

def test_zip_kwargs_to_dict():
    kwargs = {'primary_key': ['key1', 'key2'], 'value1': 1, 'value2': (3, 4), 'value3': {5,6}}
    zipped_dict = zip_kwargs_to_dict('primary_key', kwargs)
    assert zipped_dict['key1']['value1'] == 1
    assert zipped_dict['key1']['value2'] == 3
    assert zipped_dict['key1']['value3'] == 5
    assert zipped_dict['key2']['value1'] == 1
    assert zipped_dict['key2']['value2'] == 4
    assert zipped_dict['key2']['value3'] == 6
    