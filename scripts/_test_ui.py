# %%
import tkinter as tk

import test_init
from controllably.GUI import gui
from controllably.GUI import move_gui
from controllably.GUI import transfer_gui
from controllably.GUI import view_gui

# %%
import importlib
importlib.reload(gui)
importlib.reload(move_gui)
importlib.reload(transfer_gui)
importlib.reload(view_gui)

# %%
panel = gui.Panel()
panel.show()

# %%
move_app = move_gui.MovePanel()
move_app.show()

# %%
liquid_app = transfer_gui.LiquidPanel()
liquid_app.show()

# %%
panel.clearPanels()
panel.addGrid(move_app, row=0, column=0)
panel.addGrid(liquid_app, row=0, column=1)
panel.show()

# %%
from controllably.Move.Cartesian import Gantry
gantry = Gantry('COM0', limits=[[100,100,100],[-100,-100,-100]], simulation=True)

# %%
move_app.bindObject(gantry)
move_app.show()

# %%
from controllably.Transfer.Liquid.Pumps.TriContinent.tricontinent import TriContinent
from controllably.Transfer.Liquid.Pumps.TriContinent.tricontinent_api.tricontinent_api import TriContinentDevice
pump_device = TriContinentDevice('COM0', simulation=True, verbose=True)
pump_device.connect()
pump_device.getInfo()
pump = TriContinent('COM0', 5000, simulation=True, device=pump_device, verbose=True)

# %%
liquid_app.bindObject(pump)
liquid_app.show()

# %%
from controllably.Transfer.Liquid.Sartorius.sartorius import Sartorius
from controllably.Transfer.Liquid.Sartorius.sartorius_api.sartorius_api import SartoriusDevice
pipette_device = SartoriusDevice('COM0', simulation=True, verbose=True)
pipette_device.connect()
pipette_device.getInfo(model='BRL1000')
pipette = Sartorius('COM0', simulation=True, device=pipette_device, verbose=True)

# %%
liquid_app.bindObject(pipette)
liquid_app.show()

# %%
from controllably.Make.Mixture.QInstruments.orbital_shaker_utils import _BioShake
shake = _BioShake('COM0', simulation=True)

# %%
from controllably.View.camera import Camera
cam = Camera()
cam.connect()

# %%
view_app = view_gui.ViewPanel(cam)
view_app.show()

# %%
import tkinter as tk
from PIL import Image, ImageTk

root = tk.Tk()
canvas = tk.Canvas(root, width=1920, height=1080)
canvas.pack()

# Load an image using PIL
image_pil = Image.fromarray(cam.getFrame()[1])
image_tk = ImageTk.PhotoImage(image_pil)

# Display the image on the canvas
canvas.create_image((200, 150), image=image_tk, anchor=tk.CENTER)

# Keep a reference to the image (important!)
canvas.image = image_tk #avoid garbage collection.

root.mainloop()
# %%
import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import threading
import time

class VideoPlayer:
    def __init__(self, window, video_source=0):
        self.window = window
        self.window.title("OpenCV Video Feed")

        self.video_source = video_source
        self.vid = cv2.VideoCapture(self.video_source)

        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.canvas = tk.Canvas(window, width=self.width, height=self.height)
        self.canvas.pack()

        self.btn_snapshot = ttk.Button(window, text="Snapshot", command=self.snapshot)
        self.btn_snapshot.pack(anchor=tk.CENTER, padx=5, pady=10)

        self.delay = 15  # milliseconds
        self.update()

        self.window.mainloop()

    def snapshot(self):
        ret, frame = self.vid.read()
        if ret:
            cv2.imwrite("snapshot-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg", cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    def update(self):
        ret, frame = self.vid.read()
        if ret:
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.window.after(self.delay, self.update)

    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

def main():
    root = tk.Tk()
    VideoPlayer(root)

if __name__ == "__main__":
    main()
# %%
