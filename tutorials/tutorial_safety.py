# %%
from controllably.core import safety
from controllably.core.safety import set_level, reset_level, guard

# %%
print(f'{safety.safety_mode=}')

@guard(mode = safety.SUPERVISED)
def risky_function():
    print("Risky function executed!")
    return

@guard(mode = safety.DELAY)
def delayed_function():
    print("Delayed function executed!")
    return

@guard(mode = safety.DEBUG)
def normal_function():
    print("Normal function executed!")
    return

# %%
normal_function()

# %%
delayed_function()

# %%
risky_function()

# %%
set_level(safety.DELAY)
print(f'{safety.safety_mode=}')

@guard(mode = safety.SUPERVISED)
def risky_function():
    print("Risky function executed!")
    return

@guard(mode = safety.DELAY)
def delayed_function():
    print("Delayed function executed!")
    return

@guard(mode = safety.DEBUG)
def normal_function():
    print("Normal function executed!")
    return

# %%
normal_function()

# %%
delayed_function()

# %%
risky_function()

# %%
set_level(safety.SUPERVISED)
print(f'{safety.safety_mode=}')

@guard(mode = safety.SUPERVISED)
def risky_function():
    print("Risky function executed!")
    return

@guard(mode = safety.DELAY)
def delayed_function():
    print("Delayed function executed!")
    return

@guard(mode = safety.DEBUG)
def normal_function():
    print("Normal function executed!")
    return

# %%
normal_function()

# %%
delayed_function()

# %%
risky_function()

# %%
reset_level()
print(f'{safety.safety_mode=}')

# %%
