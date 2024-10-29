# %% -*- coding: utf-8 -*-
"""
This module holds the factory functions in Control.lab.ly.

Classes:
    DottableDict (dict)
    ModuleDirectory (dataclass)

Functions:
    get_class
    get_details
    include_this_module
    load_components
    register
    unregister

Other constants and variables:
    HOME_PACKAGES (list)
    modules (ModuleDirectory)
"""
# Standard library imports
from dataclasses import dataclass, field
import importlib
import inspect
import logging
import numpy as np
import pprint
import sys
from typing import Callable, Optional

# Local application imports
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")

HOME_PACKAGES = ['controllably','lab']
"""Names and aliases of base package"""

class DottableDict(dict):
    """DottableDict provides a way to use dot notation on dictionaries"""
    
    def __init__(self, *args, **kwargs):
        """Instantiate the class"""
        dict.__init__(self, *args, **kwargs)
        self.__dict__ = self
        
    def allow_dotting(self, state:bool = True):
        """
        Turn on or off the dot notation feature

        Args:
            state (bool, optional): whether to turn on dot notation feature. Defaults to True.
        """
        if state:
            self.__dict__ = self
        else:
            self.__dict__ = dict()

@dataclass
class ModuleDirectory:
    """
    ModuleDirectory represents the entire collection of imported modules into `controllably`
    
    ### Properties
    - `at`: dictionary structure of imported Classes
    
    ### Methods
    - `get_class`: get Class object from collection
    - `get_parent`: get parent dictionary of target Class
    """
    
    _modules: DottableDict = field(default_factory=DottableDict, init=False)
    
    def __repr__(self) -> str:
        printable_mod = self._modules.copy()
        def remove_docs(d):
            """
            Purge empty dictionaries from nested dictionary

            Args:
                d (dict): dictionary to be purged
            """
            for k, v in list(d.items()):
                if isinstance(v, dict):
                    remove_docs(v)
                if k == "_doc_":
                    del d[k]
        remove_docs(printable_mod)
        return pprint.pformat(printable_mod)
    
    @property
    def at(self) -> DottableDict:
        return self._modules
    
    def get_class(self, dot_notation:str) -> Callable:
        """
        Get Class object from collection

        Args:
            dot_notation (str): dot notation of target Class

        Returns:
            Callable: Class object
        """
        name = dot_notation.split('.')[-1]
        temp = self.get_parent(dot_notation=dot_notation)
        return temp.get(name)
    
    def get_parent(self, dot_notation:str) -> DottableDict:
        """
        Get parent dictionary of target Class

        Args:
            dot_notation (str): dot notation of target Class

        Returns:
            DottableDict: parent dictionary of target Class
        """
        keys = dot_notation.split('.')
        keys = keys[:-1]
        temp = self._modules
        for key in keys:
            if key in HOME_PACKAGES:
                continue
            temp = temp[key]
        return temp
        
modules = ModuleDirectory()
"""Holds all `controllably` and user-registered classes and functions"""

def get_class(dot_notation:str) -> Callable:
    """
    Retrieve the relevant class from the sub-package

    Args:
        dot_notation (str): dot notation of Class object

    Returns:
        Callable: target Class
    """
    print('\n')
    top_package = __name__.split('.')[0]
    import_path = f'{top_package}.{dot_notation}'
    package = importlib.import_module('.'.join(import_path.split('.')[:-1]))
    _class = modules.get_class(dot_notation=dot_notation)
    return _class

def get_details(configs:dict, addresses:Optional[dict] = None) -> dict:
    """
    Decode dictionary of configuration details to get np.ndarrays and tuples

    Args:
        configs (dict): dictionary of configuration details
        addresses (Optional[dict], optional): dictionary of registered addresses. Defaults to None.

    Returns:
        dict: dictionary of configuration details
    """
    addresses = {} if addresses is None else addresses
    for name, details in configs.items():
        settings = details.get('settings', {})
        
        for key,value in settings.items():
            if key == 'component_config':
                value = get_details(value, addresses=addresses)
            if type(value) == str:
                if key in ['cam_index', 'port'] and value.startswith('__'):
                    settings[key] = addresses.get(key, {}).get(settings[key], value)
            if type(value) == dict:
                if "tuple" in value:
                    settings[key] = tuple(value['tuple'])
                elif "array" in value:
                    settings[key] = np.array(value['array'])

        configs[name] = details
    return configs

def include_this_module(
    where: Optional[str] = None, 
    module_name: Optional[str] = None, 
    get_local_only: bool = True
):
    """
    Include the module py file that this function is called from

    Args:
        where (Optional[str], optional): location within structure to include module. Defaults to None.
        module_name (Optional[str], optional): dot notation name of module. Defaults to None.
        get_local_only (bool, optional): whether to only include objects defined in caller py file. Defaults to True.
    """
    module_doc = "< No documentation >"
    frm = inspect.stack()[1]
    current_mod = inspect.getmodule(frm[0])
    doc = inspect.getdoc(current_mod)
    module_doc = module_doc if doc is None else doc
    if module_name is None:
        module_name = current_mod.__name__
    
    objs = inspect.getmembers(sys.modules[module_name])
    __where__ = [obj for name,obj in objs if name == "__where__"]
    where = f"{__where__[0]}." if (len(__where__) and where is None) else where
    classes = [(nm,obj) for nm,obj in objs if inspect.isclass(obj)]
    functions = [(nm,obj) for nm,obj in objs if inspect.isfunction(obj)]
    objs = classes + functions
    if get_local_only:
        objs = [obj for obj in objs if obj[1].__module__ == module_name]
    
    for name,obj in objs:
        if name == inspect.stack()[0][3]:
            continue
        mod_name = obj.__module__ if where is None else where
        register(obj, '.'.join(mod_name.split('.')[:-1]), module_docs=module_doc)
    return

def load_components(config:dict) -> dict:
    """
    Load components of compound tools

    Args:
        config (dict): dictionary of configuration parameters

    Returns:
        dict: dictionary of component tools
    """
    components = {}
    for name, details in config.items():
        _module = details.get('module')
        if _module is None:
            continue
        dot_notation = [_module, details.get('class', '')]
        _class = get_class('.'.join(dot_notation))
        settings = details.get('settings', {})
        components[name] = _class(**settings)
    return components

def register(new_object:Callable, where:str, module_docs:Optional[str] = None):
    """
    Register the object into target location within structure

    Args:
        new_object (Callable): new Callable object (Class or function) to be registered
        where (str): location within structure to register the object in
        module_docs (Optional[str], optional): module documentation. Defaults to None.
    """
    module_docs = "< No documentation >" if module_docs is None else module_docs
    keys = where.split('.')
    temp = modules._modules
    for key in keys:
        if key in HOME_PACKAGES:
            continue
        if key not in temp:
            temp[key] = DottableDict()
        temp = temp[key]
    if "_doc_" not in temp:
        temp["_doc_"] = module_docs
    
    name = new_object.__name__
    if name in temp:
        overwrite = input(f"An object with the same name ({name}) already exists, Overwrite? [y/n]")
        if not overwrite or overwrite.lower()[0] == 'n':
            print(f"Skipping {name}...")
            return
    temp[new_object.__name__] = new_object
    return

def unregister(dot_notation:str):
    """
    Unregister an object from structure, using its dot notation reference

    Args:
        dot_notation (str): dot notation reference to target object
    """
    keys = dot_notation.split('.')
    keys, name = keys[:-1], keys[-1]
    temp = modules._modules
    for key in keys:
        if key in HOME_PACKAGES:
            continue
        temp = temp[key]
    temp.pop(name)
    
    # Clean up empty dictionaries
    def remove_empty_dicts(d: dict):
        """
        Purge empty dictionaries from nested dictionary

        Args:
            d (dict): dictionary to be purged
        """
        for k, v in list(d.items()):
            if isinstance(v, dict):
                remove_empty_dicts(v)
            if not v:
                del d[k]
        if list(d.keys()) == ['_doc_']:
            del d['_doc_']
    remove_empty_dicts(modules._modules)
    return

__where__ = "misc.Factory"
include_this_module(get_local_only=True)