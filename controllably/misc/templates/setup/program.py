# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/01 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports

# Local application imports
from controllably import Helper, load_setup     # pip install control-lab-ly
print(f"Import: OK <{__name__}>")

BINDINGS = {
    '__name__': '__device_name__.__component__'
}
REPO = '__repo_name__'
here = '/'.join(__file__.split('\\')[:-1])
parent = '/'.join(here.split('/')[:-1])
root = here.split(REPO)[0]

config_file = f"{here}/config.yaml"
layout_file = f"{here}/layout.json"
registry_file = f"{parent}/registry.yaml"

layout_dict = Helper.read_json(layout_file)
for slot in layout_dict['slots'].values():
    slot['filepath'] = f"{root}{slot['filepath']}"

def modify_setup(setup:dict):
    """
    Function to modify the setup upon initialization

    Args:
        setup (dict): dictionary of name, object pairs

    Returns:
        dict: modified setup dictionary
    """
    # setup['setup'].loadDeck(layout_dict=layout_dict)
    return setup


SETUP = load_setup(config_file=config_file, registry_file=registry_file, bindings=BINDINGS, modify_func=modify_setup)
"""NOTE: importing SETUP gives the same instance wherever you import it"""
