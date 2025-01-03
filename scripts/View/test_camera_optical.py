# %%
import init
from controllably.View.Optical import Optical

me = Optical(0, cam_size=(1280,720))
# me.view()
me.__dict__
# %%
me.disconnect()
# %%
from controllably.Control.GUI.Basic import ViewerPanel
gui = ViewerPanel(me)
gui.runGUI()
# %%
