# %% [markdown]
# # Using the Factory Module
# 
# The factory module provides a set of functions to facilitate dynamic creation and configuration of objects based on specified parameters. 
# This tutorial demonstrates how to use these functions effectively.

# %%
import pprint

from controllably.core.factory import (
    get_class,
    create,
    create_from_config,
    load_parts,
    dict_to_named_tuple,
    parse_configs,
    get_plans,
    load_setup_from_files,
    get_setup
)

# %% [markdown]
# ## Basic Usage
# 
# `get_class` retrieves a class from a specified module.

# %%
DeviceTemplateClass = get_class('tutorial_plugins','DeviceTemplate')
DeviceTemplateClass

# %% [markdown]
# `create` instantiates an object of a given class with specified parameters.

# %%
device_instance = create(DeviceTemplateClass, name="ExamplePart")
device_instance

# %% [markdown]
# `create_from_config` creates an object based on a configuration dictionary.

# %%
config = {
    'device_type': DeviceTemplateClass,
    'name': 'ConfiguredPart'
}
device_from_config = create_from_config(config)
device_from_config

# %% [markdown]
# `load_parts` loads multiple parts into a dictionary of instantiated objects based on a configuration dictionary.

# %%
part_configs = {
    'part1': {
        'module': 'tutorial_plugins',
        'class': 'DeviceTemplate',
        'name': 'Part1'
    },
    'part2': {
        'module': 'tutorial_plugins',
        'class': 'DeviceTemplate',
        'name': 'Part1'
    }
}
loaded_parts = load_parts(part_configs)
pprint.pprint(loaded_parts)

# %% [markdown]
# `dict_to_named_tuple` converts a dictionary to a named tuple for easier access.

# %%
named_tuple = dict_to_named_tuple(loaded_parts, 'setup')
named_tuple

# %% [markdown]
# `parse_configs` replaces placeholders in configuration dictionaries with actual values from an addresses dictionary.
# This is useful for managing configurations that depend on external parameters.
# It also supports referencing other configuration files, using the file path and configuration name.

# %%
addresses = {
    'port':{
        '__part_one__': 'COM1',
        '__part_two__': 'COM2'
    },
    'cam_index':{
        '__part_1__': 1,
        '__part_2__': 2
    }
}
configs = {
    'part_one': {
        'module': 'controllably.core.device',
        'class': 'SerialDevice',
        'settings': {
            'port': '__part_one__',
        }
    },
    'part_two': {
        'module': 'tutorial_plugins',
        'class': 'DeviceTemplate',
        'settings': {
            'port': '__part_two__',
        }
    },
    'part_1': {
        'module': 'controllable.View',
        'class': 'Camera',
        'settings': {
            'cam_index': '__part_1__'
        }
    },
    'part_2': {
        'module': 'controllable.View',
        'class': 'Camera',
        'settings': {
            'cam_index': '__part_2__'
        }
    },
    'referenced_device': {
        'config_file': 'control-lab-ly/tutorials/tools/tutorial_setup/config.yaml',
        'config_name': 'simple_tool'
    }
}
parsed_configs = parse_configs(configs, addresses)
pprint.pprint(parsed_configs)

# %% [markdown]
# `get_plans` generates a plan for setting up devices based on configurations and a registry.

# %%
from controllably.core.connection import get_node
registry = {
    'machine_id':
        {
            get_node(): addresses
        }
}
pprint.pprint(registry)

# %%
plans = get_plans(configs=configs, registry=registry)
pprint.pprint(plans)

# %% [markdown]
# `load_setup_from_files` loads a complete setup from configuration and registry files, 
# returning either a named tuple or a dictionary.

# %%
setup_namedtuple = load_setup_from_files(
    config_file = 'tools/tutorial_setup/config.yaml',
    registry_file = 'tools/registry.yaml'
)
setup_namedtuple

# %%
setup_dict = load_setup_from_files(
    config_file = 'tools/tutorial_setup/config.yaml',
    registry_file = 'tools/registry.yaml',
    create_tuple = False
)
pprint.pprint(setup_dict)

# %% [markdown]
# `get_setup` combines the above functionalities to load and instantiate a complete setup,
# returning it as a named tuple of a specified type.
# This is particularly useful for creating structured setups with predefined types.
# Here, we define a `Platform` dataclass to represent the structure of our setup.

# %%
from dataclasses import dataclass

from controllably.core.compound import Compound
from tutorial_plugins import DeviceTemplate, PartOne, PartTwo

@dataclass
class Platform:
    simple_tool: DeviceTemplate
    compound_tool: Compound
    part_one: PartOne
    part_two: PartTwo

# %%
new_setup = get_setup(
    config_file = 'tools/tutorial_setup/config.yaml',
    registry_file = 'tools/registry.yaml',
    platform_type = Platform
)

# %% [markdown]
# ## Miscellaneous Functions
# 
# `get_imported_modules` lists currently imported modules, of interest for debugging or introspection.
# It defaults to the `controllably` package and `library` (to inspect user-defined plugins) 
# but can be directed to any specified package.

# %%
from controllably.core.factory import (
    get_imported_modules,
    get_method_names
)

# %%
imported_modules = get_imported_modules()
pprint.pprint(imported_modules)

# %% [markdown]
# `get_method_names` retrieves the names of methods defined in a given class.

# %%
my_methods = get_method_names(DeviceTemplate)
my_methods

# %%
