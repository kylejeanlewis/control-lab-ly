# %% [markdown]
# # Safety Levels
#
# This tutorial demonstrates how to use safety levels in the `controllably` library to manage the execution of functions based on their safety requirements.

# %%
from controllably.core.logging import start_logging
from controllably.core.safety import get_safety_level, set_safety_level, reset_safety_level, guard, SafetyLevel

start_logging('output')

# %% [markdown]
# ## Define functions with different safety levels
# 
# We define three functions, each with a different safety levels: `SUPERVISED`, `DELAY`, and `DEBUG`.

# %%
@guard(mode = SafetyLevel.SUPERVISED)
def risky_function():
    print("Risky function executed!")
    return

@guard(mode = SafetyLevel.DELAY)
def delayed_function():
    print("Delayed function executed!")
    return

@guard(mode = SafetyLevel.DEBUG)
def normal_function():
    print("Normal function executed!")
    return

# %% [markdown]
# The default safety level is `None`, which respects the individual function settings,
# and logs the function calls according to their own safety levels.

# %%
print(f'{get_safety_level()=}')
normal_function()
delayed_function()
risky_function()

# %% [markdown]
# Now, we will change the global safety level to see how it affects the execution of the functions.
# When set to `DELAY`, all functions will wait for 3 seconds before executing.
#
# Functions labelled as `SUPERVISED` will still require user confirmation before execution.

# %%
set_safety_level(SafetyLevel.DELAY)
print(f'{get_safety_level()=}')
normal_function()
delayed_function()
risky_function()

# %% [markdown]
# Specific safety levels can also be set using integer values. 
# Here, we set the safety level to `2`, which is treated as a delay of 2 seconds.

# %%
set_safety_level(2)
print(f'{get_safety_level()=}')
normal_function()
delayed_function()
risky_function()

# %% [markdown]
# Setting the safety level to `DEBUG` will log the function calls without any delay or supervision.
# Functions labelled as `DELAY` and `SUPERVISED` will still respect their own safety levels.

# %%
set_safety_level(SafetyLevel.DEBUG)
print(f'{get_safety_level()=}')
normal_function()
delayed_function()
risky_function()

# %% [markdown]
# Finally, setting the safety level to `SUPERVISED` will require user confirmation 
# for all functions before execution.

# %%
set_safety_level(SafetyLevel.SUPERVISED)
print(f'{get_safety_level()=}')
normal_function()
delayed_function()
risky_function()

# %% [markdown]
# Resetting the safety level to `None` will revert to the default behavior,
# where each function respects its own safety level.

# %%
reset_safety_level()
print(f'{get_safety_level()=}')
normal_function()
delayed_function()
risky_function()

# %%
