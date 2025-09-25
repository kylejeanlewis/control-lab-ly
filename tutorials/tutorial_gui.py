# %% [markdown]
# # Creating a GUI with Tkinter
# This tutorial demonstrates how to create a simple graphical user interface 
# (GUI) based on Tkinter, the standard Python library for GUI development.
#
# In this tutorial, we try to control a gantry, a liquid handler, and a camera.
# 
# First, we import the necessary modules and create instances of the devices we want to control.

# %%
from controllably.Move.Cartesian import Gantry
from controllably.Transfer.Liquid.Pump.TriContinent import TriContinent
from controllably.View.camera import Camera

gantry = Gantry('COM0', limits=[[100,100,100],[-100,-100,-100]], simulation=True)
pump = TriContinent('COM0', 5000, simulation=True, output_right=True, verbose=True)
cam = Camera(simulation=True)
cam.connect()

# %% [markdown]
# Next, we import the GUI components from the `controllably` package and create
# instances of the panels for each device.
# 
# There are two ways to create GUI that are bound to the devices:
# 1. Create the GUI panel first and then bind the device to it, using the `bindObject` method.
# 2. Create the GUI panel and pass the device as an argument to the constructor.
# 
# The first method is more flexible, as it allows you to create the GUI panel
# without having the device ready. The second method is more convenient, as it
# allows you to create the GUI panel and bind the device in one step.
# 
# Subsequently, you can use the `show` method to display the GUI panel.

# %% 
from controllably.examples.gui.tkinter import Panel, MovePanel, LiquidPanel, ViewPanel

# %%
move_app = MovePanel()
move_app.bindObject(gantry)
move_app.show()

# %%
liquid_app = LiquidPanel()
liquid_app.bindObject(pump)
liquid_app.show()

# %%
view_app = ViewPanel(cam)
view_app.show()

# %% [markdown]
# Finally, we create a main panel to hold all the individual panels and display it.
# This is achieved by using the generic `Panel` class and adding the individual panels to it 
# with the `addGrid` or `addPack` methods, with the desired panel as the first argument, followed by
# the appropriate keyword arguments. 
# 
# These methods correspond to the `grid` and `pack` geometry managers in Tkinter, respectively. 
# The `addGrid` method allows you to specify the row and column of each panel, 
# while the `addPack` method simply stacks the panels vertically. 
# 
# Refer to the [Tkinter documentation](https://docs.python.org/3/library/tkinter.html) 
# for more details on these geometry managers.

# %%
panel = Panel()
panel.addGrid(view_app, row=0, column=0, sticky="nsew")
panel.addGrid(move_app, row=0, column=1, sticky="nsew")
panel.addGrid(liquid_app, row=0, column=2, sticky='nsew')
panel.show()

# %%
from controllably.Transfer.Liquid.Pipette.Sartorius.sartorius import Sartorius
from controllably.Transfer.Liquid.Pipette.Sartorius.sartorius_api.sartorius_api import SartoriusDevice

pipette_device = SartoriusDevice('COM0', simulation=True, verbose=False)
pipette_device.getInfo(model='BRL1000')
pipette = Sartorius('COM0', simulation=True, device=pipette_device, verbose=True)

# %%
liquid_app.bindObject(pipette)
liquid_app.show()

# %%
