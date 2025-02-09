# %%
import threading
import tkinter as tk

import test_init
from controllably.core.control import Controller, JSONInterpreter, start_client

# %% Client-server version
if __name__ == "__main__":
    host = "127.0.0.1"  # Or "localhost"
    port = 12345       # Choose a free port (above 1024 is recommended)
    ui = Controller('view', JSONInterpreter())
    
    # Start client in a separate thread
    ui_thread = threading.Thread(target=start_client, args=(host, port, ui))
    ui_thread.daemon = True  # Allow the main thread to exit even if the server is running
    ui_thread.start()
    
# %% Hub-spoke version
if __name__ == "__main__":
    host = "127.0.0.1"  # Or "localhost"
    port = 12345       # Choose a free port (above 1024 is recommended)
    ui = Controller('view', JSONInterpreter())
    
    # Start client in a separate thread
    ui_thread = threading.Thread(target=start_client, args=(host, port, ui, True))
    ui_thread.daemon = True  # Allow the main thread to exit even if the server is running
    ui_thread.start()
    
# %%
ui.getMethods(private=True)

# %%
methods = ui.getMethods(private=False)

# %%
command = dict(
    subject_id = list(methods.keys())[0],
    method = 'qsize'
)
ui.transmitRequest(command)

# %%
ui.data_buffer

# %%
command = dict(
    subject_id = list(methods.keys())[0],
    method = 'get_nowait'
)
ui.transmitRequest(command)

# %%
ui.data_buffer

# %%
def destroy():
    global root
    root.quit()
    root.destroy()
    return


class MoveGUI:
    def __init__(self, master:tk.Tk, controller: Controller, tool_id: int|str):
        self.controller = controller
        self.tool_id = tool_id
        self.master = master
        master.title("Robot Control D-Pad")

        # Initialize axis values
        self.x = 0
        self.y = 0
        self.z = 0
        self.a = 0  # Rotation around z-axis (yaw)
        self.b = 0  # Rotation around y-axis (pitch)
        self.c = 0  # Rotation around x-axis (roll)
        self.addLayout()
        return
    
    def updateValues(self):
         self.status_label.config(text=f"Robot Status: x={self.x}, y={self.y}, z={self.z}, a={self.a}, b={self.b}, c={self.c}")

    def sendCommand(self, command: dict):
        # In a real application, you would replace this with your 
        # actual robot communication code (e.g., using sockets, serial, etc.).
        print(f"Sending command: x={self.x}, y={self.y}, z={self.z}, a={self.a}, b={self.b}, c={self.c}")
        request = dict(subject_id=self.tool_id)
        request.update(command)
        self.controller.transmitRequest(request)
        return
    
    def addLayout(self):
        global root
        # Create frames for organization
        translation_frame = tk.Frame(self.master)
        translation_frame.grid(row=0, column=0, padx=10, pady=10)

        rotation_frame = tk.Frame(self.master)
        rotation_frame.grid(row=0, column=1, padx=10, pady=10)

        # Translation Controls
        tk.Label(translation_frame, text="Translation").grid(row=0, column=0, columnspan=3)
        tk.Button(translation_frame, text="Backward (Y+)", command=lambda: self.move(axis='y',value=1)).grid(row=1, column=1)
        tk.Button(translation_frame, text="Left (X-)", command=lambda: self.move(axis='x',value=-1)).grid(row=2, column=0)
        tk.Button(translation_frame, text="Right (X+)", command=lambda: self.move(axis='x',value=1)).grid(row=2, column=2)
        tk.Button(translation_frame, text="Forward (Y-)", command=lambda: self.move(axis='y',value=-1)).grid(row=3, column=1)
        tk.Button(translation_frame, text="Up (Z+)", command=lambda: self.move(axis='z',value=1)).grid(row=4, column=1)  # Added Z-axis
        tk.Button(translation_frame, text="Down (Z-)", command=lambda: self.move(axis='z',value=-1)).grid(row=5, column=1)  # Added Z-axis

        # Rotation Controls
        tk.Label(rotation_frame, text="Rotation").grid(row=0, column=0, columnspan=3)
        tk.Button(rotation_frame, text="Yaw CW (A+)", command=lambda: self.rotate(axis='a',value=1)).grid(row=1, column=1)
        tk.Button(rotation_frame, text="Yaw CCW (A-)", command=lambda: self.rotate(axis='a',value=-1)).grid(row=2, column=1)
        tk.Button(rotation_frame, text="Pitch Up (B+)", command=lambda: self.rotate(axis='b',value=1)).grid(row=3, column=1) # Pitch
        tk.Button(rotation_frame, text="Pitch Down (B-)", command=lambda: self.rotate(axis='b',value=-1)).grid(row=4, column=1) # Pitch
        tk.Button(rotation_frame, text="Roll CW (C+)", command=lambda: self.rotate(axis='c',value=1)).grid(row=5, column=1) # Yaw
        tk.Button(rotation_frame, text="Roll CCW (C-)", command=lambda: self.rotate(axis='c',value=-1)).grid(row=6, column=1) # Yaw

        # Status Display
        self.status_label = tk.Label(self.master, text="Robot Status: x=0, y=0, z=0, a=0, b=0, c=0")
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(10,0))  # Span across both columns
        tk.Button(self.master, text='Terminate', command=destroy).grid(row=2, column=0, columnspan=2, pady=(10,0)) 
        return

    def move(self, axis:str, value:int|float):
        assert axis in 'xyz', 'Provide one of x,y,z axis'
        if axis == 'x':
            self.x += value
        elif axis == 'y':
            self.y += value
        elif axis == 'z':
            self.z += value
        else:
            return
        command = dict(
            method = 'move',
            args = (axis, value)
        )
        self.sendCommand(command) # Simulate sending to robot
        self.updateValues()

    def rotate(self, axis:str, value:int|float):
        assert axis in 'abc', 'Provide one of a,b,c axis'
        if axis == 'a':
            self.a += value
        elif axis == 'b':
            self.b += value
        elif axis == 'c':
            self.c += value
        else:
            return
        command = dict(
            method = 'rotate',
            args = (axis, value)
        )
        self.sendCommand(command) # Simulate sending to robot
        self.updateValues()

# %%
root = tk.Tk()
gui = MoveGUI(root, ui, '2315389997888')

# %%
root.mainloop()

# %%
