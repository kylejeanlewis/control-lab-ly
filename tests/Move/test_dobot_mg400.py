# %%
from .. import init
from controllably.Move.Jointed.Dobot import MG400
from controllably.Control.GUI.Basic import MoverPanel
from controllably.Transfer.Substrate.Dobot import TwoJawGrip

gui = MoverPanel(MG400('192.168.2.6'), axes='XYZa')
# gui.runGUI()
me = gui.tool
me.__dict__
# %%
me.home()
# %%
me.moveTo((200,200,0))
# %%
me.moveBy((50,50,50))
# %%
me.move('z',-80)
# %%
me.safeMoveTo((200,200,-20), ascent_speed=20, descent_speed=50)
# %%
me.home()
# %%
me.rotateBy((50,0,0))
# %%
me.rotateTo((-50,0,0))
# %%
me.home()
# %%
me.toggleAttachment(True, TwoJawGrip)
# %%
me.attachment.drop()
# %%
me.attachment.grab()
# %%
