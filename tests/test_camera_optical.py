# %%
import init
from controllably.Control.GUI import ViewerPanel
from controllably.View.Optical import Optical

gui = ViewerPanel(Optical())
gui.runGUI()
me = gui.tool
# %%
me.__dict__