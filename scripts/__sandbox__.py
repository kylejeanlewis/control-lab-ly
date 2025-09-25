# %%
import cv2
import matplotlib.pyplot as plt

from controllably.View.camera import Camera
from controllably.View.Thermal.Flir.ax8 import AX8

# %%
cam = Camera()
cam.connect()

_,frame = cam.getFrame()
plt.imshow(frame)

# %%
cam.show()

# %%
therm = AX8('192.168.1.110')
therm.connect()

_,frame = therm.getFrame()
plt.imshow(frame)

# %%
