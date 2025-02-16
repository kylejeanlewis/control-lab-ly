# %%
import tkinter as tk

import test_init
from controllably.GUI import gui
from controllably.GUI import move_gui

# %%
import importlib
importlib.reload(gui)
importlib.reload(move_gui)

# %%
app = move_gui.MovePanel()
app.show()

# %%
root = tk.Tk()
left = tk.Frame(root)
right = tk.Frame(root)

left.grid(row=0, column=0)
right.grid(row=0, column=1)

lgui = app.addTo(left)
rgui = app.addTo(right)
root.mainloop()

# %%
from controllably.Move.Cartesian import Gantry
gantry = Gantry('COM0', limits=[[100,100,100],[-100,-100,-100]], simulation=True)

# %%
app.bindObject(gantry)
app.show()

# %%
