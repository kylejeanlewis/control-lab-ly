# %%
from routines import Controller

control = Controller('config/config.xlsx', position_check=False)
control.run_program()

# %%
