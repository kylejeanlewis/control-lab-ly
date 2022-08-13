# %%
# -*- coding: utf-8 -*-
"""
Created on Fri 2022/03/18 09:00:00

@author: Chang Jie
"""
import PySimpleGUI as sg
print(f"Import: OK <{__name__}>")

WIDTH, HEIGHT = sg.Window.get_screen_size()
THEME = 'LightGreen'
BG_COLOR = '#d3dfda'
FONT = "Helvetica"
TITLE_SIZE = 12
TEXT_SIZE = 10

sg.theme(THEME)
sg.set_options(
    font=FONT,
    background_color=BG_COLOR,
    element_padding = (0,0)
    )

# %%
class Elements(object):
    """
    Generate basic UI elements such as buttons, paddings, sliders, radio buttons, and text.
    - theme: overall UI theme
    - font: text font
    - title_size: size of title text
    - text_size: size of body text
    - bg_color: background color
    """
    def __init__(self, theme=THEME, font=FONT, title_size=TITLE_SIZE, text_size=TEXT_SIZE, bg_color=BG_COLOR):
        self.theme = theme
        self.font = font
        self.title_size = title_size
        self.text_size = text_size
        self.bg_color = bg_color
        sg.theme(theme)
        sg.set_options(
            font=font,
            background_color=bg_color,
            element_padding = (0,0)
        )
        return
    
    def getB(self, label, size=(None,None), key=None):
        """
        Generate button object
        - label: text to be displayed on button
        - size: size of button
        - key: reference key to object
        
        Return: sg.Button object
        """
        return sg.Button(label, size=size, key=key, font=(self.font, self.text_size))

    def getC(self, label, size, key, default=False):
        """
        Generate checkbox object
        - label: text to be displayed on with checkbox
        - size: size of button
        - key: reference key to object
        - default: default value of checkbox (bool)
        
        Return: sg.Checkbox object
        """
        return sg.Checkbox(label, size=size, key=key, default=default, font=(self.font, self.text_size), background_color=self.bg_color)
    
    def getI(self, def_value, size, key, enable_events=None):
        """
        Generate input field object
        - def_value: default value to be displayed in field
        - size: size of field
        - key: reference key to object
        - enable_events: if True, changes to this element are immediately reported as an event
        
        Return: sg.Input object
        """
        return sg.Input(def_value, size=size, key=key, font=(self.font, self.text_size), enable_events=enable_events)

    def getP(self, size=(None,None)):
        """
        Generate padding
        - size: size of field

        Return: sg.Push object
        """
        ele = sg.Text('', size=size, background_color=self.bg_color)#, expand_x=True)
        try:
            ele = sg.Push(background_color=self.bg_color)
        except:
            pass
        return ele
    
    def getR(self, label, grp, key, size=(None,None), default=False, enable_events=False):
        """
        Generate radio button object
        - label: text to be displayed with radio button
        - grp: group of radio buttons object belong to
        - key: reference key to object
        - size: size of slider
        - default: whether object is the default upon starting GUI
        - enable_events: if True, changes to this element are immediately reported as an event
        
        Return: sg.Radio object
        """
        return sg.Radio(label, grp, size=size, font=(self.font, self.text_size), key=key, default=default, enable_events=enable_events)
    
    def getS(self, minmax, default, orientation, size, key):
        """
        Generate slider object
        - minmax: range of allowable values
        - default: default value upon starting GUI
        - orientation: orientation of slider ('h' / 'v')
        - size: size of slider
        - key: reference key to object
        
        Return: sg.Slider object
        """
        return sg.Slider(minmax, default, orientation=orientation, size=size, key=key, font=(self.font, self.text_size), background_color=self.bg_color)

    def getText(self, text, size=(None,None), just='left', bold=False, key=None):
        """
        Generate text box
        - text: text to be displayed
        - size: size of text box
        - just: justification of text ('left' / 'center' / 'right')
        - bold: whether to bold text
        - key: reference key to object
        
        Return: sg.Text obejct
        """
        font = (self.font, self.text_size, "bold") if bold else (self.font, self.text_size)
        return sg.Text(text, size=size, justification=just, font=font, background_color=self.bg_color, key=key)

    def getTitle(self, text, size=(None,None), just='left', bold=False, key=None):
        """
        Generate text box (with larger title text)
        - text: text to be displayed
        - size: size of text box
        - just: justification of text ('left' / 'center' / 'right')
        - bold: whether to bold text
        - key: reference key to object
        
        Return: sg.Text obejct
        """
        font = (self.font, self.title_size, "bold") if bold else (self.font, self.title_size)
        return sg.Text(text, size=size, justification=just, font=font, background_color=self.bg_color, key=key)
    

# %%
class Modules(Elements):
    """
    Child class of Elements.
    Generate functional modules from elements.
    - theme: overall UI theme
    - font: text font
    - title_size: size of title text
    - text_size: size of body text
    - bg_color: background color
    """
    def __init__(self, theme=THEME, font=FONT, title_size=TITLE_SIZE, text_size=TEXT_SIZE, bg_color=BG_COLOR):
        super().__init__(theme, font, title_size, text_size, bg_color)
        return

    def getCamera(self):
        """
        Get camera module with title and current XYZ labels
        Return: sg.Column object
        """
        module = [
            [self.getTitle("Webcam", (64,1), 'center', bold=True)],
            [sg.Image(filename='', key='-IMAGE-', enable_events=True)]
        ]
        return sg.Column(module, background_color=self.bg_color)
    
    def getControl(self, itemsH=[], itemsV=[], padding=(None,None)):
        """
        Get movement control module in different linear or cross configurations
        - itemsH: items in horizontal alignment
        - itemsV: items in vertical alignment
        - padding: amount of padding to add
        
        Return: list
        """
        module = []
        if len(itemsV) != 0:
            for item in itemsV:
                if item != None:
                    module.append([self.getP(padding), item, self.getP(padding)])
                elif len(itemsH) != 0:
                    module.append([self.getP()] + itemsH + [self.getP()])
        elif len(itemsH) != 0:
            module = [self.getP()] + itemsH + [self.getP()]
        return module
    def getXYControl(self):
        """
        Get XY-control module (cross-configuration)
        Return: sg.Column object
        """
        overall_size = int(64/8*7)
        size_B = (int(overall_size/7), 2)
        module = [
            [self.getText("X/Y axis", (overall_size, 1), 'left', bold=True)]
        ]
        x_buttons = [ 
            self.getB("X-10", size_B), self.getB("X-1", size_B), self.getB("X-0.1", size_B), 
            sg.Button("<XY>", size=size_B, font=(self.font, self.text_size), button_color=('#000000', '#ffffff')), 
            self.getB("X+0.1", size_B), self.getB("X+1", size_B), self.getB("X+10", size_B)
        ]
        y_buttons = [
            self.getB("Y+10", size_B), self.getB("Y+1", size_B), self.getB("Y+0.1", size_B), None,
            self.getB("Y-0.1", size_B), self.getB("Y-1", size_B), self.getB("Y-10", size_B)
        ]
        module = module + self.getControl(x_buttons, y_buttons, padding=(size_B[0]*3+4, 2))
        return sg.Column(module, background_color=self.bg_color)
    def getXControl(self):
        """
        Get X-control module (linear, horizontal configuration)
        Return sg.Column object
        """
        overall_size = int(64/8)
        size_B = (overall_size, 2)
        module = [
            [self.getText("X axis", (overall_size,1), 'left', bold=True)]
        ]
        x_buttons = [
            self.getB("X+10", size_B), self.getB("X+1", size_B), self.getB("X+0.1", size_B),
            sg.Button("<X>", size=size_B, font=(FONT, self.text_size), button_color=('#000000', '#ffffff')),
            self.getB("X-0.1", size_B), self.getB("X-1", size_B), self.getB("X-10", size_B)
        ]
        module = module + [self.getControl(itemsH=x_buttons)]
        return sg.Column(module, background_color=self.bg_color)
    def getZControl(self):
        """
        Get Z-control module (linear, vertical configuration)
        Return sg.Column object
        """
        overall_size = int(64/8)
        size_B = (overall_size, 2)
        module = [
            [self.getText("Z axis", (overall_size,1), 'left', bold=True)]
        ]
        z_buttons = [
            self.getB("Z+10", size_B), self.getB("Z+1", size_B), self.getB("Z+0.1", size_B),
            sg.Button("<Z>", size=size_B, font=(FONT, self.text_size), button_color=('#000000', '#ffffff')),
            self.getB("Z-0.1", size_B), self.getB("Z-1", size_B), self.getB("Z-10", size_B)
        ]
        module = module + self.getControl(itemsV=z_buttons)
        return sg.Column(module, background_color=self.bg_color)
    def getXYZControls(self):
        """
        Get XYz-control module (cross-configuration + linear, vertical)
        Return: sg.Column object
        """
        module = [
            [self.getTitle("XYZ Position Control", (64,1), 'center', bold=True)], 
            [self.getXYControl(), self.getZControl()],
            [self.getTitle("", (64,1))]
            ]
        return sg.Column(module, background_color=self.bg_color)
    def getPositions(self):
        """
        Get XYZ-position indicator module
        Return: sg.Column object
        """
        overall_size = 64
        size = (int(overall_size/8), 1)
        module = [
            [self.getText("Current Position", (overall_size,1), bold=True)], 
            [self.getText("X:  ", size, 'right'), self.getI(0, size, '-X-CURRENT-'),
            self.getText("Y:  ", size, 'right'), self.getI(0, size, '-Y-CURRENT-'),
            self.getText("Z:  ", size, 'right'), self.getI(0, size, '-Z-CURRENT-'),
            self.getB('Go To', size), self.getB('Reset', size)]
        ]
        return sg.Column(module, background_color=self.bg_color)

    def getFile(self, name, initial_file=''):
        """
        Get file selector module
        - name: name of field
        - initial_file: default file to display

        Return: sg.Column object
        """
        initial_folder = '/'.join(initial_file.split('/')[:-1]) if len(initial_file) else None
        module = [
            [self.getP()],
            [self.getText(f"Choose {name.lower()} location: ", (20,1), just='right'), 
            self.getI(initial_file, (36,1), f"-{name.upper()} FILE-", enable_events=True), 
            sg.FileBrowse(size=(8,1), font=(self.font, self.text_size), key=f"-{name.upper()} BROWSE-", initial_folder=initial_folder)]
        ]
        return sg.Column(module, background_color=self.bg_color)
    def getFolder(self, name, initial_folder=''):
        """
        Get file selector module
        - name: name of field
        - initial_file: default folder to display
        
        Return: sg.Column object
        """
        module = [
            [self.getP()],
            [self.getText(f"Choose {name.lower()} location: ", (20,1)), 
            self.getI(initial_folder, (36,1), f"-{name.upper()} FOLDER-", enable_events=True),
            sg.FolderBrowse(size=(8,1), font=(self.font, self.text_size), key=f"-{name.upper()} BROWSE-", initial_folder=initial_folder)]
        ]
        return sg.Column(module, background_color=self.bg_color)

    def getKeithley(self, name, default_address=0):
        """
        Get Keithley control module
        - name: name of Keithley
        - default_address: default address of Keithley to be displayed upon starting GUI

        Return: sg.Column object
        """
        overall_size = 64
        size = (int(overall_size/6), 1)
        name = name.title()
        module = [
            [self.getText(f"{name} Settings", (overall_size,1), bold=True)],
            [self.getP(), self.getText('IP Address:  ', size, 'right'), self.getI(default_address, size, f'--{name[0]}-ADDRESS--'), 
            self.getText('# Readings:  ', size, 'right'), self.getI(5, size, f'-{name[0]}-NUMREAD-'), 
            self.getText('Buffer Size:  ', size, 'right'), self.getI(100, size, f'-{name[0]}-BUFFERSIZE-'), self.getP()]
        ]
        return sg.Column(module, background_color=self.bg_color)
    def getKeithleyParams(self, name, default_address=0, default_values=(0,0,0)):
        """
        Get Keithley parameters module
        - name: name of Keithley
        - default_address: default address of Keithley to be displayed upon starting GUI
        - default_values: default parameters of measurement to be displayed upon starting GUI

        Return: sg.Column object
        """
        overall_size = 64
        size = (int(overall_size/8), 1)
        name = name.title()
        module = [
            [self.getText(f"{name} Parameters", (overall_size,1), bold=True)],
            [self.getP(), self.getText('Address:  ', size, 'right'), self.getI(default_address, size, f'-{name[0]}-ADDRESS-'), 
            self.getText('Start:  ', size, 'right'), self.getI(default_values[0], size, f'-{name[0]}-START-'), 
            self.getText('Stop:  ', size, 'right'), self.getI(default_values[1], size, f'-{name[0]}-STOP-'), 
            self.getText('Step:  ', size, 'right'), self.getI(default_values[2], size, f'-{name[0]}-STEP-'), self.getP()]
        ]
        return sg.Column(module, background_color=self.bg_color)
    
    def getMacros(self, fn_labels=['fn1', 'fn2', 'fn3']):
        """
        Get Macro buttons module
        - fn_labels: labels for the three function buttons
        
        Return: sg.Column object
        """
        overall_size = 64
        size_B = (int(overall_size/6), 2)
        fn_keys = [s.replace(' ', '').upper() for s in fn_labels]
        module = [
            [self.getTitle("Macro", (overall_size, 1), 'center', bold=True)],
            [self.getP((12,1)), self.getB("Default View", size_B), self.getB("Probe", size_B), 
            self.getB("Cam", size_B), self.getB("Calibrate", size_B), self.getP((12,1))],
            [self.getP((12,1)), self.getB("Set View", size_B), self.getB(f"{fn_labels[0]}", size_B, f'-{fn_keys[0].upper()}-'), 
            self.getB(f"{fn_labels[1]}", size_B, f'-{fn_keys[1].upper()}-'), self.getB(f"{fn_labels[2]}", size_B, f'-{fn_keys[2].upper()}-'), self.getP((12,1))]
        ]
        return sg.Column(module, background_color=self.bg_color)

    def getOpenCV(self):
        """
        Get Open CV control module
        Return: sg.Column object
        """
        overall_size = 64
        size_R = (int(overall_size/8), 1)
        size_S = (40,10)
        module = [
            [self.getTitle("OpenCV Haar Cascade", (overall_size, 1), 'center', bold=True)],
            [self.getText("Brightness  ", (20,0), 'right'), self.getS((0,100), 0, 'h', size_S, "-BRIGHTNESS SLIDER-")],
            [self.getText("Contrast  ", (20,0), 'right'), self.getS((0,5), 1, 'h', size_S, "-CONTRAST SLIDER-")],
            
            [self.getText("Gaussian Blurring Kernel", (overall_size, 0), bold=True)],
            [self.getP(), self.getR('Disable', 'Radio1', "-KERNEL DISABLE-", size_R, default=True), self.getR('3x3', 'Radio1', "-3x3 KERNEL SIZE-", size_R),
            self.getR('5x5', 'Radio1', "-5x5 KERNEL SIZE-", size_R), self.getR('9x9', 'Radio1', "-9x9 KERNEL SIZE-", size_R), self.getP()],
            
            [self.getText("Device Detection (Haar Cascade & Contour Detection)", (50, 1), bold=True),
            self.getC("Pause detection", (14,1), "-PAUSE DETECT-", default=True)],
            [self.getText("Scale Factor  ", (20,0), 'right'), self.getS((50,1000), 525, 'h', size_S, "-SCALE SLIDER-")], 
            [self.getText("Min Neighbour  ", (20,0), 'right'), self.getS((0,20), 10, 'h', size_S, "-NEIGHBOR SLIDER-")],
            [self.getText("BG Noise Removal  ", (20,1), 'right'), self.getS((0,5), 0, 'h', size_S, "-OPENING SLIDER-")], 
            [self.getText("FG Noise Removal  ", (20,1), 'right'), self.getS((0,5), 0, 'h', size_S, "-CLOSING SLIDER-")]
        ]
        return sg.Column(module, background_color=self.bg_color)


# %%
class Builder(Modules):
    """
    Child class of Modules.
    Generate layouts from modules.
    - theme: overall UI theme
    - font: text font
    - title_size: size of title text
    - text_size: size of body text
    - bg_color: background color
    """
    def __init__(self, theme=THEME, font=FONT, title_size=TITLE_SIZE, text_size=TEXT_SIZE, bg_color=BG_COLOR):
        super().__init__(theme, font, title_size, text_size, bg_color)
        self.layouts = {}
        self.layout = []
        return
    
    def addCollapsable(self, name, items, alignV=None, visible=True):
        """
        Add a new collapsable layout to collection
        - name: name of the new layout
        - items: elements or columns to be added into the layout
        - alignV: vertial alignment of items
        - visible: whether layout is visible
        """
        layout = items
        self.layouts[name] = sg.pin(sg.Column(layout, vertical_alignment=alignV, key=name, visible=visible))
        return

    def addLayout(self, name, items, alignV=None, visible=True):
        """
        Add a new layout to collection
        - name: name of the new layout
        - items: elements or columns to be added into the layout
        - alignV: vertial alignment of items
        - visible: whether layout is visible
        """
        if name == '-FINAL-':
            self.layout = items
            return
        layout = items
        self.layouts[name] = sg.Column(layout, vertical_alignment=alignV, key=name, visible=visible)
        return

    def getWindow(self, gui_name):
        """
        Generate a GUI window from the final layout stored
        - gui_name: name of window to be displayed

        Return: sg.Window object
        """
        window = sg.Window(gui_name, self.layout, enable_close_attempted_event=True, resizable=True, finalize=True)
        return window


class Popups(Elements):
    """
    Child class of Elements.
    Generate Popups from modules.
    - theme: overall UI theme
    - font: text font
    - title_size: size of title text
    - text_size: size of body text
    - bg_color: background color
    """
    def __init__(self, theme=THEME, font=FONT, title_size=TITLE_SIZE, text_size=TEXT_SIZE, bg_color=BG_COLOR):
        super().__init__(theme, font, title_size, text_size, bg_color)
        return

    def combo(self, options=[], text='', key=''):
        """
        Create new popup with combo selection
        - values: list of values to choose from
        """
        lines = text.split("\n")
        w = max([len(line) for line in lines])
        h = len(lines)
        layout = [
            [self.getText(text, (w+2, h))],
            [sg.Combo(options, options[0], key=key, size=(20,1), 
                font=(self.font, self.text_size), background_color=self.bg_color)],
            [self.getB('OK', (10, 1))]
        ]
        window = sg.Window('Select', layout, finalize=True, modal=True, resizable=True)
        selected_option = options[0]
        while True:
            event, values = window.read(timeout=20)
            if event in ('OK', sg.WIN_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, None):
                selected_option = values[key]
                print(f'Selected: {selected_option}')
                break
        window.close()
        return selected_option

    def combo_plus_input(self, options=[], text=['',''], key=['','']):
        """
        Create new popup with combo selection
        - values: list of values to choose from
        """
        lines0 = text[0].split("\n")
        w0 = max([len(line) for line in lines0])
        h0 = len(lines0)
        lines1 = text[1].split("\n")
        w1 = max([len(line) for line in lines1])
        h1 = len(lines1)
        layout = [
            [self.getText(text[0], (w0+2, h0))],
            [sg.Combo(options, options[0], key=key[0], size=(20,1), 
                font=(self.font, self.text_size), background_color=self.bg_color)],
            [self.getText(text[1], (w1+2, h1))],
            [self.getI('', (20,1), key[1])],
            [self.getB('OK', (10, 1))]
        ]
        window = sg.Window('Select', layout, finalize=True, modal=True, resizable=True)
        selected_option = options[0]
        while True:
            event, values = window.read(timeout=20)
            if event in ('OK', sg.WIN_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, None):
                selected_option = values[key[0]]
                input_text = values[key[1]]
                if selected_option == options[0]:
                    if len(input_text):
                        selected_option = input_text
                    else:
                        selected_option = 'Unknown'
                print(f'Selected: {selected_option}')
                break
        window.close()
        return selected_option


    def draw_rectangle(self, img='draw.png',  data=None, img_size=(400,400)):
        """
        Create new popup to draw rectangles on image
        Adapted from https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Graph_Drag_Rectangle.py
        - img: filename of image
        - data: encoded image data
        - img_size: size of image
        """
        layout = [[sg.Graph(
            canvas_size=img_size,
            graph_bottom_left=(0, 0),
            graph_top_right=img_size,
            key="-GRAPH-",
            change_submits=True,  # mouse click events
            background_color=self.bg_color,
            drag_submits=True), ],
            [sg.Text(key='info', size=(60, 1))]]

        window = sg.Window("draw rect on image", layout, finalize=True)
        # get the graph element for ease of use later
        graph = window["-GRAPH-"]  # type: sg.Graph

        try:
            graph.draw_image(img, location=(0,img_size[1]))
        except:
            graph.draw_image(data=data, location=(0,img_size[1]))
        dragging = False
        start_point = end_point = prior_rect = None

        while True:
            event, values = window.read()

            if event == sg.WIN_CLOSED:
                break  # exit

            if event == "-GRAPH-":  # if there's a "Graph" event, then it's a mouse
                x, y = values["-GRAPH-"]
                if not dragging:
                    start_point = (x, y)
                    dragging = True
                else:
                    end_point = (x, y)
                if prior_rect:
                    graph.delete_figure(prior_rect)
                if None not in (start_point, end_point):
                    prior_rect = graph.draw_rectangle(start_point, end_point, line_color='red')

            elif event.endswith('+UP'):  # The drawing has ended because mouse up
                info = window["info"]
                info.update(value=f"grabbed rectangle from {start_point} to {end_point}")
                start_point, end_point = None, None  # enable grabbing a new rect
                dragging = False

            else:
                # print("unhandled event", event, values)
                pass
        return

    def draw_rectangles(self, img='draw.png', data=None, img_size=(400,400)):
        """
        Create new popup to draw rectangles on image
        Adapted from https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Graph_Drawing_And_Dragging_Figures.py
        - img: filename of image
        - data: encoded image data
        - img_size: size of image
        """
        col = [[self.getText('Choose what clicking a figure does')],
            [self.getR('Draw Rectangles', 1, '-RECT-', (20,1), default=True, enable_events=True)],
            [self.getR('Erase all', 1, '-CLEAR-', (20,1), enable_events=True)],
            [self.getB('Save & Close', (10,1), '-SAVE-')],
            ]

        layout = [[sg.Graph(
                    canvas_size=img_size,
                    graph_bottom_left=(0, 0),
                    graph_top_right=img_size,
                    key="-GRAPH-",
                    enable_events=True,
                    background_color=self.bg_color,
                    drag_submits=True,
                    right_click_menu=[[],['Erase item',]]
                    ), sg.Col(col, key='-COL-') ],
                [self.getText('',(60, 1), key='-INFO-')]]

        window = sg.Window("Manually Annotate Targets", layout, finalize=True, modal=True)

        # get the graph element for ease of use later
        graph = window["-GRAPH-"]  # type: sg.Graph
        try:
            graph.draw_image(data=data, location=(0,img_size[1]))
        except:
            graph.draw_image(img, location=(0,img_size[1]))

        dragging = False
        start_point = end_point = prior_rect = None
        
        positions = []
        while True:
            event, values = window.read()
            if event in (sg.WIN_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, None):
                positions = {}
                break
            if event == '-SAVE-':
                break

            elif not event.startswith('-GRAPH-'):
                graph.set_cursor(cursor='left_ptr')

            if event == "-GRAPH-":
                x, y = values["-GRAPH-"]
                if not dragging:
                    start_point = (x, y)
                    dragging = True
                    drag_figures = graph.get_figures_at_location((x,y))[1:]
                    lastxy = x,y
                else:
                    end_point = (x, y)
                if prior_rect:
                    graph.delete_figure(prior_rect)
                delta_x, delta_y = x - lastxy[0], y - lastxy[1]
                lastxy = x,y
                if None not in (start_point, end_point):
                    if values['-RECT-']:
                        prior_rect = graph.draw_rectangle(start_point, end_point, fill_color=None, line_color='green')
                        
                    elif values['-CLEAR-']:
                        positions = []
                        graph.erase()
                        try:
                            graph.draw_image(data=data, location=(0,img_size[1]))
                        except:
                            graph.draw_image(img, location=(0,img_size[1]))
                    
                window["-INFO-"].update(value=f"mouse {values['-GRAPH-']}")
            elif event.endswith('+UP'):  # The drawing has ended because mouse up
                window["-INFO-"].update(value=f"grabbed rectangle from {start_point} to {end_point}")
                if values['-RECT-'] and start_point and end_point:
                    start_point = (start_point[0], img_size[1]-start_point[1])
                    end_point = (end_point[0], img_size[1]-end_point[1])
                    rect = {
                        0: min(start_point[0], end_point[0]), 
                        1: min(start_point[1], end_point[1]), 
                        2: abs(start_point[0] - end_point[0]), 
                        3: abs(start_point[1] - end_point[1])}
                    positions.append(rect)
                    point_x = (end_point[0] + start_point[0])/2
                    point_y = img_size[1] - (end_point[1] + start_point[1])/2
                    graph.draw_point((point_x, point_y), size=5, color='red')
                start_point, end_point = None, None  # enable grabbing a new rect
                dragging = False
                prior_rect = None
            elif event.endswith('+RIGHT+'):  # Right click
                window["-INFO-"].update(value=f"Right clicked location {values['-GRAPH-']}")
            elif event.endswith('+MOTION+'):  # Right click
                window["-INFO-"].update(value=f"mouse freely moving {values['-GRAPH-']}")
        window.close()
        return positions

    def listbox(self, options=[], text='', key=''):
        """
        Create new popup with combo selection
        - values: list of values to choose from
        """
        lines = text.split("\n")
        w = max([len(line) for line in lines])
        h = len(lines)
        layout = [
            [self.getText(text, (w+2, h))],
            [sg.Listbox(options, options, sg.LISTBOX_SELECT_MODE_MULTIPLE, 
                enable_events=False, key=key, size=(20, len(options)),
                font=(self.font, self.text_size), background_color=self.bg_color)],
            [self.getB('OK', (10, 1))]
        ]
        window = sg.Window('Select', layout, finalize=True, modal=True, resizable=True)
        selected_options = options
        while True:
            event, values = window.read(timeout=20)
            if event in ('OK', sg.WIN_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, None):
                selected_options = values[key]
                print(f'Selected: {selected_options}')
                break
        window.close()
        return selected_options

    def notif(self, text='OK'):
        """
        Create new popup with alert
        - text: notification popup to display
        """
        lines = text.split("\n")
        w = max([len(line) for line in lines])
        h = len(lines)
        window = sg.Window(f'Note', [[self.getText(text, (w+2, h), 'center')], [self.getB('OK', (w+2, h))]], finalize=True, modal=True)
        while True:
            event, values = window.read(timeout=20)
            if event in ('OK', sg.WIN_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, None):
                break
        window.close()
        return
    


# %%
