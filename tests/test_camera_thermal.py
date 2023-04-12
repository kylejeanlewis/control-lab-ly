# %%
import init
from controllably.Control.GUI import ViewerPanel
from controllably.View.Thermal import Thermal

gui = ViewerPanel(Thermal('192.168.1.111')) # FIXME: unable to connect
gui.runGUI()
me = gui.tool
me.__dict__