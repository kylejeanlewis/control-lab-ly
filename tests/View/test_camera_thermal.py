# %%
import init
from controllably.Control.GUI.Basic import ViewerPanel
from controllably.View.Thermal import Thermal

me = Thermal('192.168.1.111')
gui = ViewerPanel(me) # FIXME: unable to connect
gui.runGUI()
me.__dict__