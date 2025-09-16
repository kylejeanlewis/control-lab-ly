# %%
from tutorial_plugins import PartOne, PartTwo

# %%
from controllably.core.compound import Compound

parts = {'part1': PartOne(name='part1'), 'part2': PartTwo(name='part2')}
compound = Compound(parts=parts)
compound

# %%
compound.connection_details

# %%
print(f'{compound.is_connected=}')
print(f'{compound.parts.part1=}')
print(f'{compound.parts.part1.is_connected=}')
print(f'{compound.parts.part2=}')
print(f'{compound.parts.part2.is_connected=}')

# %%
compound.connect()
print(f'{compound.is_connected=}')
print(f'{compound.parts.part1=}')
print(f'{compound.parts.part1.is_connected=}')
print(f'{compound.parts.part2=}')
print(f'{compound.parts.part2.is_connected=}')

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

# %%
from controllably.core.compound import Combined
from tutorial_plugins import DeviceTemplate

parts = {'part1': PartOne(), 'part2': PartTwo()}
combined = Combined(parts=parts, device_type=DeviceTemplate, name='common_part')
combined

# %%
print(f'{combined.connection_details=}')
print(f'{combined.parts.part1.connection_details=}')
print(f'{combined.parts.part2.connection_details=}')
print(f'{combined.device=}')
print(f'{combined.parts.part1.device=}')
print(f'{combined.parts.part2.device=}')

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

# %%
from controllably.core.compound import Ensemble
from tutorial_plugins import DeviceTemplate

Parallel_PartOne = Ensemble.factory(PartOne)

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

# %%
for chn in ensemble.channels.values():
    chn.device.verbose=True
ensemble_from_config.is_connected

# %%
ensemble.method3()

# %%
ensemble.method3(channel=[0,1])

# %%
ensemble.parallel('method3', channels=[0,1,2])

# %%
ensemble.method1(order=4, name='E', port='port')

# %%
def generate_kwargs(i,key,part):
    return {'order': i+1, 'name': f'Channel_{key}', 'port': part.device.name}
ensemble.parallel('method1', channels=[0,1,2], kwargs_generator=generate_kwargs)

# %%
from controllably.core.compound import Multichannel
from tutorial_plugins import DeviceTemplate

Multi_PartTwo = Multichannel.factory(PartTwo)

# %%
multichannel = Multi_PartTwo(
    channels=[0,1,2,3],
    details={'name': 'common_device'}
)
multichannel

# %%
multichannel.connect()

# %%
multichannel_config = {
    'channels': [0,1,2,3],
    'details': {
        'name': 'common_device'
    }
}
multichannel_from_config = Multi_PartTwo.fromConfig(multichannel_config)
multichannel_from_config

# %%
multichannel.device.verbose=True
multichannel.is_connected

# %%
multichannel.method4()

# %%
multichannel.method4(channel=[2,3])

# %%
multichannel.method4(channel=0)

# %%
multichannel.method2(order=6, name='F', port='port')

# %%
