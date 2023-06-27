# %%
import init
from controllably.Control.GUI.Basic import ViewerPanel
from controllably.View.Optical import Optical

gui = ViewerPanel(Optical(0))
gui.runGUI()
me = gui.tool
me.__dict__
# %%
