# -*- coding: utf-8 -*-
# Standard library imports
from dataclasses import dataclass
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Sequence

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.debug(f"Import: OK <{__name__}>")


@dataclass
class ModuleDirectory:
    ...
modules_dict = dict()
modules = ...

def create_configs():
    # """Create new tools configs folder"""
    # cwd = os.getcwd().replace('\\', '/')
    # src = f"{here}/templates/tools"
    # dst = f"{cwd}/tools"
    # if not os.path.exists(dst):
    #     print("Creating tools folder...\n")
    #     copytree(src=src, dst=dst)
    #     helper.get_node()
    # return
    ...

def create_named_tuple_from_dict(d:dict, type_name:str = 'Setup') -> tuple:
    # """
    # creating named tuple from dictionary

    # Args:
    #     d (dict): dictionary to be transformed
    #     type_name (str, optional): name of new namedtuple type. Defaults to 'Setup'.

    # Returns:
    #     tuple: named tuple from dictionary
    # """
    # field_list = []
    # object_list = []
    # for k,v in d.items():
    #     field_list.append(k)
    #     object_list.append(v)
    
    # named_tuple = namedtuple(type_name, field_list)
    # print(f"Objects created: {', '.join(field_list)}")
    # return named_tuple(*object_list)
    ...

def create_setup(setup_name:str|None = None):
    # """
    # Create new setup folder

    # Args:
    #     setup_name (str|None, optional): name of new setup. Defaults to None.
    # """
    # cwd = os.getcwd().replace('\\', '/')
    # if setup_name is None:
    #     setup_num = 1
    #     while True:
    #         setup_name = f'Setup{str(setup_num).zfill(2)}'
    #         if not os.path.exists(f"{cwd}/tools/{setup_name}"):
    #             break
    #         setup_num += 1
    # src = f"{here}/templates/setup"
    # cfg = f"{cwd}/tools"
    # dst = f"{cfg}/{setup_name}"
    # if not os.path.exists(cfg):
    #     create_configs()
    # if not os.path.exists(dst):
    #     print(f"Creating setup folder ({setup_name})...\n")
    #     copytree(src=src, dst=dst)
    #     helper.get_node()
    # return
    ...

def load_setup(config_file:str, registry_file:str|None = None, create_tuple:bool = True) -> dict|tuple:
    # """
    # Load and initialise setup

    # Args:
    #     config_file (str): config filename
    #     registry_file (str|None, optional): registry filename. Defaults to None.
    #     create_tuple (bool, optional): whether to return a named tuple, if not returns dictionary. Defaults to True.

    # Returns:
    #     Union[dict,tuple]: dictionary or named tuple of setup objects
    # """
    # config = helper.get_plans(config_file=config_file, registry_file=registry_file)
    # setup = factory.load_components(config=config)
    # shortcuts = config.get('SHORTCUTS',{})
    
    # for key,value in shortcuts.items():
    #     parent, child = value.split('.')
    #     tool = setup.get(parent)
    #     if tool is None:
    #         print(f"Tool does not exist ({parent})")
    #         continue
    #     if 'components' not in tool.__dict__:
    #         print(f"Tool ({parent}) does not have components")
    #         continue
    #     setup[key] = tool.components.get(child)
    # if create_tuple:
    #     return create_named_tuple_from_dict(setup)
    # return setup
    ...

def get_class(dot_notation:str) -> Callable:
    # """
    # Retrieve the relevant class from the sub-package

    # Args:
    #     dot_notation (str): dot notation of Class object

    # Returns:
    #     Callable: target Class
    # """
    # print('\n')
    # top_package = __name__.split('.')[0]
    # import_path = f'{top_package}.{dot_notation}'
    # package = importlib.import_module('.'.join(import_path.split('.')[:-1]))
    # _class = modules.get_class(dot_notation=dot_notation)
    # return _class
    ...

def get_details(configs:dict, addresses:dict|None = None) -> dict:
    # """
    # Decode dictionary of configuration details to get np.ndarrays and tuples

    # Args:
    #     configs (dict): dictionary of configuration details
    #     addresses (Optional[dict], optional): dictionary of registered addresses. Defaults to None.

    # Returns:
    #     dict: dictionary of configuration details
    # """
    # addresses = {} if addresses is None else addresses
    # for name, details in configs.items():
    #     settings = details.get('settings', {})
        
    #     for key,value in settings.items():
    #         if key == 'component_config':
    #             value = get_details(value, addresses=addresses)
    #         if type(value) == str:
    #             if key in ['cam_index', 'port'] and value.startswith('__'):
    #                 settings[key] = addresses.get(key, {}).get(settings[key], value)
    #         if type(value) == dict:
    #             if "tuple" in value:
    #                 settings[key] = tuple(value['tuple'])
    #             elif "array" in value:
    #                 settings[key] = np.array(value['array'])

    #     configs[name] = details
    # return configs
    ...

def get_method_names(obj:Callable) -> list[str]:
    """
    Get the names of the methods in Callable object (class/instance)

    Args:
        obj (Callable): object of interest

    Returns:
        list[str]: list of method names
    """
    return [attr for attr in dir(obj) if callable(getattr(obj, attr)) and not attr.startswith('__')]

def include_this_module(
    where: str|None = None, 
    module_name: str|None = None, 
    get_local_only: bool = True
):
    # """
    # Include the module py file that this function is called from

    # Args:
    #     where (str|None, optional): location within structure to include module. Defaults to None.
    #     module_name (str|None, optional): dot notation name of module. Defaults to None.
    #     get_local_only (bool, optional): whether to only include objects defined in caller py file. Defaults to True.
    # """
    # module_doc = "< No documentation >"
    # frm = inspect.stack()[1]
    # current_mod = inspect.getmodule(frm[0])
    # doc = inspect.getdoc(current_mod)
    # module_doc = module_doc if doc is None else doc
    # if module_name is None:
    #     module_name = current_mod.__name__
    
    # objs = inspect.getmembers(sys.modules[module_name])
    # __where__ = [obj for name,obj in objs if name == "__where__"]
    # where = f"{__where__[0]}." if (len(__where__) and where is None) else where
    # classes = [(nm,obj) for nm,obj in objs if inspect.isclass(obj)]
    # functions = [(nm,obj) for nm,obj in objs if inspect.isfunction(obj)]
    # objs = classes + functions
    # if get_local_only:
    #     objs = [obj for obj in objs if obj[1].__module__ == module_name]
    
    # for name,obj in objs:
    #     if name == inspect.stack()[0][3]:
    #         continue
    #     mod_name = obj.__module__ if where is None else where
    #     register(obj, '.'.join(mod_name.split('.')[:-1]), module_docs=module_doc)
    # return
    ...

def load_components(config:dict) -> dict:
    # """
    # Load components of compound tools

    # Args:
    #     config (dict): dictionary of configuration parameters

    # Returns:
    #     dict: dictionary of component tools
    # """
    # components = {}
    # for name, details in config.items():
    #     _module = details.get('module')
    #     if _module is None:
    #         continue
    #     dot_notation = [_module, details.get('class', '')]
    #     _class = get_class('.'.join(dot_notation))
    #     settings = details.get('settings', {})
    #     components[name] = _class(**settings)
    # return components
    ...

def register(new_object:Callable, where:str, module_docs:str|None = None):
    # """
    # Register the object into target location within structure

    # Args:
    #     new_object (Callable): new Callable object (Class or function) to be registered
    #     where (str): location within structure to register the object in
    #     module_docs (str|None, optional): module documentation. Defaults to None.
    # """
    # module_docs = "< No documentation >" if module_docs is None else module_docs
    # keys = where.split('.')
    # temp = modules._modules
    # for key in keys:
    #     if key in HOME_PACKAGES:
    #         continue
    #     if key not in temp:
    #         temp[key] = DottableDict()
    #     temp = temp[key]
    # if "_doc_" not in temp:
    #     temp["_doc_"] = module_docs
    
    # name = new_object.__name__
    # if name in temp:
    #     overwrite = input(f"An object with the same name ({name}) already exists, Overwrite? [y/n]")
    #     if not overwrite or overwrite.lower()[0] == 'n':
    #         print(f"Skipping {name}...")
    #         return
    # temp[new_object.__name__] = new_object
    # return
    ...

def unregister(dot_notation:str):
    # """
    # Unregister an object from structure, using its dot notation reference

    # Args:
    #     dot_notation (str): dot notation reference to target object
    # """
    # keys = dot_notation.split('.')
    # keys, name = keys[:-1], keys[-1]
    # temp = modules._modules
    # for key in keys:
    #     if key in HOME_PACKAGES:
    #         continue
    #     temp = temp[key]
    # temp.pop(name)
    
    # # Clean up empty dictionaries
    # def remove_empty_dicts(d: dict):
    #     """
    #     Purge empty dictionaries from nested dictionary

    #     Args:
    #         d (dict): dictionary to be purged
    #     """
    #     for k, v in list(d.items()):
    #         if isinstance(v, dict):
    #             remove_empty_dicts(v)
    #         if not v:
    #             del d[k]
    #     if list(d.keys()) == ['_doc_']:
    #         del d['_doc_']
    # remove_empty_dicts(modules._modules)
    # return
    ...

def zip_kwargs_to_dict(primary_key:str, kwargs:dict) -> dict:
    """
    Checks and zips multiple keyword arguments of lists into dictionary
    
    Args:
        primary_keyword (str): primary keyword to be used as key
    
    Kwargs:
        key, list[...]: {keyword, list of values} pairs

    Raises:
        Exception: Ensure the lengths of inputs are the same

    Returns:
        dict: dictionary of (primary keyword, kwargs)
    """
    length = len(kwargs[primary_key])
    for key, value in kwargs.items():
        if isinstance(value, Sequence):
            continue
        if isinstance(value, set):
            kwargs[key] = list(value)
            continue
        kwargs[key] = [value]*length
    keys = list(kwargs.keys())
    assert all(len(kwargs[key]) == length for key in keys), f"Ensure the lengths of these inputs are the same: {', '.join(keys)}"
    primary_values = kwargs.pop(primary_key)
    other_values = [v for v in zip(*kwargs.values())]
    sub_dicts = [dict(zip(keys[1:], values)) for values in other_values]
    new_dict = dict(zip(primary_values, sub_dicts))
    return new_dict