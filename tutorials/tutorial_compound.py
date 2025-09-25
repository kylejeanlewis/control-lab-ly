# %% [markdown]
# # Compound Devices
# Compound devices are built by combining multiple simpler devices, allowing for more complex interactions and functionalities.
# The `Compound`, `Combined`, `Ensemble`, and `Multichannel` classes facilitate the creation and management of these compound devices.
# 
# First, we will import two example device classes, `PartOne` and `PartTwo`, from the `tutorial_plugins` module.
# We also import a sample device class `DeviceTemplate` and `PartTemplate` to be used later.

# %%
from tutorial_plugins import PartOne, PartTwo, DeviceTemplate, PartTemplate

# %% [markdown]
# ## Compound and Combined devices
# 
# `Compound` and `Combined` devices are used to group multiple device parts together.
# Each part can have its own connection details, or they can share a common device instance.
# These classes help manage the connection and interaction of the component parts.
# Create new subclasses from `Compound` or `Combined` if you want to add new methods or properties to the compound object.
#
# ### Compound class
# The `Compound` class allows you to group multiple device parts together, each with its own connection details.

# %%
from controllably.core.compound import Compound

parts = {'part1': PartOne(name='part1'), 'part2': PartTwo(name='part2')}
compound = Compound(parts=parts)
compound

# %%
compound.connection_details

# %% [markdown]
# With this way of initialization, the component devices are not connected automatically.
# You can check the connection status of the compound and its parts using the `is_connected` property.

# %%
print(f'{compound.is_connected=}')
print(f'{compound.parts.part1=}')
print(f'{compound.parts.part1.is_connected=}')
print(f'{compound.parts.part2=}')
print(f'{compound.parts.part2.is_connected=}')

# %% [markdown]
# You can connect the compound device using `connect()`, which will in turn connect all its parts.

# %%
compound.connect()
print(f'{compound.is_connected=}')
print(f'{compound.parts.part1=}')
print(f'{compound.parts.part1.is_connected=}')
print(f'{compound.parts.part2=}')
print(f'{compound.parts.part2.is_connected=}')

# %% [markdown]
# You can also initialize a `Compound` device from a configuration dictionary using the `fromConfig()` class method.
# This dictionary should specify the module, class, and settings for each part.
# This way of initialization is useful for loading device configurations from external files,
# and it also connects the component devices automatically.

# %% 
compound_config = {
    'details':{
        'part1':
            {
                'module': 'tutorial_plugins',
                'class': 'PartOne',
                'settings': {
                    'name': 'part1'
                }
            },
        'part2':
            {
                'module': 'tutorial_plugins',
                'class': 'PartTwo',
                'settings': {
                    'name': 'part2'
                }
            }
    }
}
compound_from_config = Compound.fromConfig(compound_config)
compound_from_config

# %% [markdown]
# ### Combined class
# Next,  we explore the `Combined` class, which is similar to `Compound` but allows all parts to share a common device instance.

# %%
from controllably.core.compound import Combined

parts = {'part1': PartOne(), 'part2': PartTwo()}
combined = Combined(parts=parts, device_type=DeviceTemplate, name='common_part')
combined

# %% [markdown]
# Similar to `Compound`, the parts of a `Combined` device are not connected automatically upon initialization.

# %%
print(f'{combined.is_connected=}')
combined.connect()
print(f'{combined.is_connected=}')

# %% [markdown]
# You can access the connection details and the shared device instance from both the `Combined` device and its parts.
# We can inspect and confirm that all parts share the same device instance.

# %%
print(f'{combined.connection_details=}')
print(f'{combined.parts.part1.connection_details=}')
print(f'{combined.parts.part2.connection_details=}')
print(f'{combined.device=}')
print(f'{combined.parts.part1.device=}')
print(f'{combined.parts.part2.device=}')

# %% [markdown]
# You can also initialize a `Combined` device from a configuration dictionary using the `fromConfig()` class method.
# This dictionary should specify the module, class, and settings for each part, as well as the common device type and name.
# Note that the device instance is created automatically before being shared among all parts, so the
# device settings are specified in the top level of the configuration dictionary. 
#
# Any settings specified for the individual parts for the device will be overridden by those of the common device.

# %%
combined_config = {
    'name': 'common_part',
    'device_type': DeviceTemplate,
    'details':{
        'part1':
            {
                'module': 'tutorial_plugins',
                'class': 'PartOne',
                'settings': {
                    'name': 'part1'
                }
            },
        'part2':
            {
                'module': 'tutorial_plugins',
                'class': 'PartTwo',
                'settings': {
                    'name': 'part2'
                }
            }
    }
}
combined_from_config = Combined.fromConfig(combined_config)
combined_from_config

# %% [markdown]
# ## Ensemble and Multichannel classes
# The `Ensemble` and `Multichannel` classes are designed for managing multiple instances of a device part,
# either with individual device instances for each part (`Ensemble`) or a shared device instance among all parts (`Multichannel`).
# 
# ### Ensemble class
# The `Ensemble` class allows you to create multiple instances of a device part, each with its own connection details.
# This is useful for managing multiple similar devices that can be controlled independently as parallel channels.
# 
# Use the `Ensemble.factory()` method to create a new subclass of `Ensemble` for a specific device part class.

# %%
from controllably.core.compound import Ensemble

Parallel_PartOne = Ensemble.factory(PartOne)

# %% [markdown]
# We can then create an instance of this new subclass, specifying the channels and their respective connection details.

# %%
ensemble = Parallel_PartOne(
    channels=[0,1,2],
    details=[
        {'name': 'part1_channel_0'},
        {'name': 'part1_channel_1'},
        {'name': 'part1_channel_2'},
    ]
)
ensemble

# %%
ensemble.connect()

# %% [markdown]
# Similarly, you can also initialize an `Ensemble` device from a configuration dictionary using the `fromConfig()` class method.
# This dictionary should specify the channels and their respective details.
# Here, the devices are connected automatically upon initialization as well.

# %%
ensemble_config = {
    'channels': [0,1,2],
    'details': {
        0: {
            'settings': {
                'name': 'part1_channel_0'
            }
        },
        1: {
            'settings': {
                'name': 'part1_channel_1'
            }
        },
        2: {
            'settings': {
                'name': 'part1_channel_2'
            }
        }
    }
}
ensemble_from_config = Parallel_PartOne.fromConfig(ensemble_config)
ensemble_from_config

# %% [markdown]
# You can access the connection details and the device instances from both the `Ensemble` device and its channels.
# The connection status of the `Ensemble` instance checks if all its channels are connected.

# %%
for chn in ensemble.channels.values():
    chn.device.verbose=True
ensemble_from_config.is_connected

# %% [markdown]
# The created subclass `Parallel_PartOne` inherits all methods from the `PartOne` class.
# You can call these methods on the `Ensemble` instance, which will execute the method on all channels.

# %%
ensemble.method3()

# %% [markdown]
# You can also specify a subset of channels to execute the method on by passing a list of channel keys.

# %%
ensemble.method3(channel=[0,1])

# %% [markdown]
# You can also execute methods in parallel across all channels using the `parallel()` method.

# %%
ensemble.parallel('method3', channels=[0,1,2])

# %% [markdown]
# When calling methods on the `Ensemble` instance, you can pass arguments that will be forwarded to each channel's method.

# %%
ensemble.method1(order=4, name='E', port='port')

# %% [markdown]
# You can pass different arguments to each channel by providing a `kwargs_generator` function.

# %%
def generate_kwargs(i: int, key: int, part: PartTemplate):
    return {'order': i+1, 'name': f'Channel_{key}', 'port': getattr(part.device, 'name', 'name')}
ensemble.parallel('method1', channels=[0,1,2], kwargs_generator=generate_kwargs)

# %% [markdown]
# ### Multichannel class
# The `Multichannel` class is similar to `Ensemble`, but it allows all channels to share a common device instance.
# 
# Use the `Multichannel.factory()` method to create a new subclass of `Multichannel` for a specific device part class.

# %%
from controllably.core.compound import Multichannel

Multi_PartTwo = Multichannel.factory(PartTwo)

# %% [markdown]
# We can then create an instance of this new subclass, specifying the channels and the common connection details.

# %%
multichannel = Multi_PartTwo(
    channels=[0,1,2,3],
    details={'name': 'common_device'}
)
multichannel

# %%
multichannel.connect()

# %%
# Similarly, you can also initialize a `Multichannel` device from a configuration dictionary using the `fromConfig()` class method.
# %%
multichannel_config = {
    'channels': [0,1,2,3],
    'details': {
        'name': 'common_device'
    }
}
multichannel_from_config = Multi_PartTwo.fromConfig(multichannel_config)
multichannel_from_config

# %% [markdown]
# You can access the connection details and the shared device instance from both the `Multichannel` device and its channels.
# The connection status of the `Multichannel` instance checks if the shared device is connected.

# %%
multichannel.device.verbose=True
multichannel.is_connected

# %% [markdown]
# The created subclass `Multi_PartTwo` inherits all methods from the `PartTwo` class.
# You can call these methods on the `Multichannel` instance, which will execute the method on all channels.

# %%
multichannel.method4()

# %% [markdown]
# You can also specify a subset of channels to execute the method on by passing a list of channel keys.

# %%
multichannel.method4(channel=[2,3])

# %% [markdown]
# Like with the `Ensemble` class, you can also execute methods on a single channel.

# %%
multichannel.method4(channel=0)

# %% [markdown]
# When calling methods on the `Multichannel` instance, you can pass arguments that will be forwarded to each specified channel's method.

# %%
multichannel.method2(order=6, name='F', port='port')

# %%
