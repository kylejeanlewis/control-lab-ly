# %% [markdown]
# create, create_from_config
# get_class, load_parts
# parse_configs, get_plans
# dict_to_named_tuple, load_setup_from_files
# get_setup

# get_imported_modules
# get_method_names

# %% [markdown]
# # Using the Factory Module

# %%
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
# %%
DeviceTemplate = get_class('tutorial_plugins','DeviceTemplate')

# %%
device_instance = create(DeviceTemplate, name="ExamplePart")
device_instance

# %%
config = {
    'device_type': DeviceTemplate,
    'name': 'ConfiguredPart'
}
device_from_config = create_from_config(config)
device_from_config

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
loaded_parts

# %%
named_tuple = dict_to_named_tuple(loaded_parts, 'setup')
named_tuple

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
    }
}
parsed_configs = parse_configs(configs, addresses)
parsed_configs

# %%
from controllably.core.factory import (
    get_imported_modules,
    get_method_names
)

# %%
imported_modules = get_imported_modules()
imported_modules

# %%
my_methods = get_method_names(DeviceTemplate)
my_methods

# %%
