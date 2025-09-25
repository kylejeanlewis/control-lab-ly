# %% [markdown]
# # Initializing a Setup
# 
# In this tutorial, we demonstrate how to initialize a setup using the `tutorial_other` module. 
# This module contains a `setup` function that initializes and returns a setup object.

# %%
from tools import tutorial_other

setup = tutorial_other.setup()
setup

# %% [markdown]
# The `setup` function can be called multiple times, but it will always return the same setup object.

# %%
setup_again = tutorial_other.setup()
setup_again

# %%
print(f'{setup is setup_again=}')

# %%
