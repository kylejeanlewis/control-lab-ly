# %%
import init
from controllably.Control.GUI.Basic import ViewerPanel
from controllably.View.Optical import Optical

me = Optical(0)
gui = ViewerPanel(me)
gui.runGUI()
me.__dict__
# %%
