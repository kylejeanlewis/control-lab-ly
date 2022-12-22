# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/30 10:30:00
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
import time

# Third party imports
import PySimpleGUI as sg # pip install PySimpleGUI
from PySimpleGUI import WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT

# Local application imports
print(f"Import: OK <{__name__}>")

WIDTH, HEIGHT = sg.Window.get_screen_size()
THEME = 'LightGreen'
TYPEFACE = "Helvetica"
FONT_SIZES = [14,12,10,8,6]

class Panel(object):
    def __init__(self, name='', theme=THEME, typeface=TYPEFACE, font_sizes=FONT_SIZES, group=None):
        """
        Panel class

        Args:
            name (str, optional): name of panel. Defaults to ''.
            theme (str, optional): name of theme. Defaults to THEME.
            typeface (str, optional): name of typeface. Defaults to TYPEFACE.
            font_sizes (list, optional): list of font sizes. Defaults to FONT_SIZES.
            group (str, optional): name of group. Defaults to None.
        """
        self.theme = theme
        self.typeface = typeface
        self.font_sizes = font_sizes
        self.name = name
        self.group = group
        
        self.window = None
        self.configure()
        
        self.flags = {}
        return
    
    @staticmethod
    def getButtons(labels:list, size, key_prefix, font:tuple, **kwargs):
        """
        Get list of panel buttons

        Args:
            labels (list): list of button labels
            size (int, or tuple): button width (,height)
            key_prefix (any): prefix of button key
            font (tuple): (typeface, font size)

        Returns:
            list: list of PySimpleGUI.Button objects
        """
        buttons = []
        specials = kwargs.pop('specials', {})
        for label in labels:
            key_string = label.replace('\n','')
            key = f"-{key_prefix}-{key_string}-" if key_prefix else f"-{key_string}-"
            kw = kwargs.copy()
            if label in specials.keys():
                for k,v in specials[label].items():
                    kw[k] = v
            buttons.append(sg.Button(label, size=size, key=key, font=font, **kw))
        return buttons
    
    def _mangle(self, string:str):
        """
        Mangle string with name of panel

        Args:
            string (str): string to be mangled

        Returns:
            str: mangled string
        """
        return f'-{self.name}{string}'
    
    def _pad(self):
        """
        Spacer / padding

        Returns:
            PySimpleGUI.Push: padding
        """
        ele = sg.Text('', size=(1,1))
        try:
            ele = sg.Push()
        except Exception as e:
            print(e)
        return ele
    
    def arrangeElements(self, elements:list, shape=(0,0), form=''):
        """
        Arrange elements in a horizontal / vertical / cross-shape pattern

        Args:
            elements (list): list of GUI elements
            shape (tuple, optional): shape of grid. Defaults to (0,0).
            form (str, optional): shape of pattern. Defaults to ''.

        Raises:
            Exception: Grid size must be large enough to accommodate all elements

        Returns:
            list: list of arranged GUI elements
        """
        arranged_elements = []
        if form in ['X', 'x', 'cross', '+']:
            h = elements[0]
            v = elements[1]
            if len(h) == 0:
                return self.arrangeElements(v, form='V')
            if len(v) == 0:
                return self.arrangeElements(h, form='H')
            h_keys = [b.Key for b in h]
            for ele in reversed(v):
                if ele.Key in h_keys:
                    arranged_elements.append([self._pad()]+ h +[self._pad()])
                else:
                    arranged_elements.append([self._pad(), ele, self._pad()])
        elif form in ['V', 'v', 'vertical', '|']:
            arranged_elements = [[self._pad(), ele, self._pad()] for ele in reversed(elements)]
        elif form in ['H', 'h', 'horizontal', '-', '_']:
            arranged_elements = [[self._pad()]+ elements +[self._pad()]]
        else: # arrange in grid
            rows, cols = shape
            num = len(elements)
            n = 0
            if not all(shape):
                if rows:
                    row = rows
                elif cols:
                    row = int(num/cols)
                else: # find the most compact arrangement 
                    root = 1
                    while True:
                        if root**2 > num:
                            break
                        root += 1
                    row = root
            elif rows*cols < num:
                raise Exception('Make sure grid size is able to fit the number of elements.')
            else:
                row = rows
            while n < num:
                l,u = n, min(n+row, num)
                arranged_elements.append([self._pad()]+ [elements[l:u]] +[self._pad()])
                n += row
        return arranged_elements
    
    def close(self):
        """
        Close window
        """
        return
    
    def configure(self, **kwargs):
        """
        Configure defaults
        """
        theme = self.theme if 'theme' not in kwargs.keys() else kwargs.pop('theme')
        font = (self.typeface, self.font_sizes[int(len(FONT_SIZES)/2)]) if 'font' not in kwargs.keys() else kwargs.pop('font')
        element_padding = (0,0) if 'element_padding' not in kwargs.keys() else kwargs.pop('element_padding')
        
        sg.theme(theme)
        sg.set_options(font=font, element_padding=element_padding, **kwargs)
        return
    
    def getLayout(self, title='Panel', title_font_level=0, **kwargs):
        """
        Get layout object

        Args:
            title (str, optional): title of layout. Defaults to 'Panel'.
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 0.

        Returns:
            PySimpleGUI.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level]) if 'font' not in kwargs.keys() else kwargs.pop('font')
        layout = [[
            sg.Text(title, 
                    font=font,
                    **kwargs)
        ]]
        # Build Layout here
        layout = sg.Column(layout, vertical_alignment='top')
        return layout
    
    def getWindow(self, title='Application', **kwargs):
        """
        Get window object

        Args:
            title (str, optional): title of window. Defaults to 'Application'.

        Returns:
            PySimpleGUI.Window: Window object
        """
        layout = [[self.getLayout()]]
        window = sg.Window(title, layout, enable_close_attempted_event=True, resizable=False, finalize=True, icon='icon.ico', **kwargs)
        self.window = window
        return window
    
    def listenEvents(self, event, values):
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        # Listen to events here
        return updates
    
    def loopGUI(self):
        """
        Loop GUI process
        """
        if type(self.window) == type(None):
            return
        while True:
            event, values = self.window.read(timeout=30)
            if event in ('Ok', WIN_CLOSED, WINDOW_CLOSE_ATTEMPTED_EVENT, None):
                self.window.close()
                break
            updates = self.listenEvents(event, values)
            for ele_key, kwargs in updates.items():
                self.window[ele_key].update(**kwargs)
        return
    
    def runGUI(self, title='Application', maximize=False):
        """
        Run the GUI loop

        Args:
            title (str, optional): title of window. Defaults to 'Application'.
            maximize (bool, optional): whether to maximise window. Defaults to False.
        """
        self.getWindow(title)
        self.window.Finalize()
        if maximize:
            self.window.Maximize()
        self.window.bring_to_front()
        self.loopGUI()
        self.window.close()
        self.close()
        return


class CompoundPanel(Panel):
    """
    Compound Panel class

    Args:
        ensemble (dict, optional): dictionary of individual sub-panels. Defaults to {}.
        theme (str, optional): name of theme. Defaults to THEME.
        typeface (str, optional): name of typeface. Defaults to TYPEFACE.
        font_sizes (list, optional): list of font sizes. Defaults to FONT_SIZES.
        group (str, optional): name of group. Defaults to None.
    """
    def __init__(self, ensemble={}, theme=THEME, typeface=TYPEFACE, font_sizes=FONT_SIZES, group=None):
        super().__init__(theme=theme, typeface=typeface, font_sizes=font_sizes, group=group)
        self.panels = {key: value[0](name= key, **value[1]) for key,value in ensemble.items()}
        return
    
    def close(self):
        """
        Close window
        """
        for panel in self.panels.values():
            panel.close()
        return
    
    def getLayout(self, title='Control Panel', title_font_level=0, **kwargs):
        """
        Get layout object

        Args:
            title (str, optional): title of layout. Defaults to 'Panel'.
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 0.

        Returns:
            PySimpleGUI.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level], 'bold')
        layout = super().getLayout(title, justification='center', font=font)
        
        tab_groups = {'main': []}
        for key, panel in self.panels.items():
            group = panel.group
            _layout = panel.getLayout(title_font_level=title_font_level+1)
            if not group:
                group = 'main'
            if group not in tab_groups.keys():
                tab_groups[group] = []
            tab_groups[group].append((key, _layout))
        
        panels = []
        excluded = ['main']
        for group, _layouts in tab_groups.items():
            if group == 'main':
                panels = panels + [_layout for _,_layout in _layouts]
                continue
            if len(_layouts) == 1:
                panels.append(_layouts[0][1])
                excluded.append(group)
            else:
                tabs = [sg.Tab(key, [[_layout]], expand_x=True) for key,_layout in tab_groups[group]]
                tab_group = sg.TabGroup([tabs], tab_location='bottomright', key=f'-{group}-TABS-', 
                                        expand_x=True, expand_y=True)
                tab_groups[group] = tab_group
        panels = panels + [element for group,element in tab_groups.items() if group not in excluded]
        panel_list = [panels[0]]
        for p in range(1, len(panels)):
            panel_list.append(sg.VerticalSeparator(color="#ffffff", pad=5))
            panel_list.append(panels[p])
        
        suite = sg.Column([panel_list], vertical_alignment='top')
        layout = [
            [layout],
            [suite]
        ]
        layout = sg.Column(layout, vertical_alignment='top')
        return layout
    
    def listenEvents(self, event, values):
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        for panel in self.panels.values():
            update = panel.listenEvents(event, values)
            updates.update(update)
        return updates


class MeasurerPanel(Panel):
    """
    Measurer Panel class

    Args:
        measurer (obj): Measurer object
        name (str, optional): name of panel. Defaults to 'MEASURE'.
        theme (str, optional): name of theme. Defaults to THEME.
        typeface (str, optional): name of typeface. Defaults to TYPEFACE.
        font_sizes (list, optional): list of font sizes. Defaults to FONT_SIZES.
        group (str, optional): name of group. Defaults to 'measurer'.
    """
    def __init__(self, measurer, name='MEASURE', theme=THEME, typeface=TYPEFACE, font_sizes=FONT_SIZES, group='measurer'):
        super().__init__(name=name, theme=theme, typeface=typeface, font_sizes=font_sizes, group=group)
        self.measurer = measurer
        return
    
    def close(self):
        """
        Close window
        """
        return super().close()
    
    def getLayout(self, title='Panel', title_font_level=0, **kwargs):
        """
        Get layout object

        Args:
            title (str, optional): title of layout. Defaults to 'Panel'.
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 0.

        Returns:
            PySimpleGUI.Column: Column object
        """
        return super().getLayout(title, title_font_level, **kwargs)
    
    def listenEvents(self, event, values):
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        return super().listenEvents(event, values)


class MoverPanel(Panel):
    """
    Mover Panel class

    Args:
        mover (obj): Mover object
        name (str, optional): name of panel. Defaults to 'MOVE'.
        theme (str, optional): name of theme. Defaults to THEME.
        typeface (str, optional): name of typeface. Defaults to TYPEFACE.
        font_sizes (list, optional): list of font sizes. Defaults to FONT_SIZES.
        group (str, optional): name of group. Defaults to 'mover'.
        axes (list, optional): list of degrees of freedom/axes. Defaults to ['X','Y','Z','a','b','g'].
    """
    def __init__(self, mover, name='MOVE', theme=THEME, typeface=TYPEFACE, font_sizes=FONT_SIZES, group='mover', axes=['X','Y','Z','a','b','g']):
        super().__init__(name=name, theme=theme, typeface=typeface, font_sizes=font_sizes, group=group)
        self.axes = axes
        self.buttons = {}
        self.mover = mover
        self.flags['update_position'] = True
        return
        
    def getLayout(self, title_font_level=1, **kwargs):
        """
        Get layout object

        Args:
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 1.

        Returns:
            PySimpleGUI.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout(f'{self.name} Control', justification='center', font=font)
        
        # yaw (alpha, about z-axis), pitch (beta, about x-axis), roll (gamma, about y-axis)
        axes = ['X','Y','Z','a','b','g']
        increments = ['-10','-1','-0.1',0,'+0.1','+1','+10']
        center_buttons = ['home']*2 + ['safe'] + ['zero']*3
        font = (self.typeface, self.font_sizes[title_font_level+1])
        color_codes = {
            'X':None, 'Y':None, 'Z':None,
            # 'X':'#bbbbff', 'Y':'#bbffbb', 'Z':'#ffbbbb',
            'a':'#ffffbb', 'b':'#ffbbff', 'g':'#bbffff'
        }
        tooltips = {
            'X':None, 'Y':None, 'Z':None,
            'a':'Rotation (in degrees) about Z-axis', 
            'b':'Rotation (in degrees) about Y-axis', 
            'g':'Rotation (in degrees) about X-axis'
        }
        labels = {axis: [] for axis in axes}
        elements = {}
        input_fields = []
        
        for axis,center in zip(axes, center_buttons):
            specials = {}
            bg_color = color_codes[axis]
            column = sg.Column([[sg.Text(axis, font=font)], 
                                [sg.Input(0, size=(5,2), key=self._mangle(f'-{axis}-VALUE-'), 
                                          tooltip=tooltips[axis],
                                          font=font, background_color=bg_color)]],
                               justification='center', pad=10, visible=(axis in self.axes))
            input_fields.append(column)
            
            if axis in ['a','b','g']:
                orientation = 'v' if axis=='g' else 'h'
                size = (15,20) if axis=='g' else (36,20)
                slider = sg.Slider((-180,180), 0, orientation=orientation, size=size, key=self._mangle(f'-{axis}-SLIDER-'), 
                                   resolution=1, enable_events=True, disable_number_display=True, 
                                   font=font, trough_color=bg_color, visible=(axis in self.axes),
                                   tooltip=tooltips[axis]
                                   )
                elements[axis] = [[self._pad(), slider, self._pad()]]
                continue
            
            if axis not in self.axes:
                elements[axis] = []
                continue
            
            for inc in increments:
                label = f'{axis}\n{inc}' if inc else center
                labels[axis].append(label)
                key = self._mangle(f"-{label}-") if self.name else f"-{label}-"
                self.buttons[key.replace('\n','')] = (axis, float(inc))
            specials[center] = dict(button_color=('#000000', '#ffffff'))
            elements[axis] = self.getButtons(labels[axis], (5,2), self.name, font, specials=specials)
        
        layout = [
            [layout],
            [self._pad()],
            [
                sg.Column([[sg.Column(elements['b'], justification='right')],
                           [self._pad()],
                           [sg.Column(self.arrangeElements(elements['Z'], form='V')),
                            sg.Column(self.arrangeElements([elements['X'], elements['Y']], form='X'))],
                           [self._pad()],
                           [sg.Column(elements['a'], justification='right')]]), 
                sg.Column(elements['g'])
            ],
            [self._pad()],
            input_fields,
            [self._pad()],
            [sg.Column([self.getButtons(['Go','Clear','Reset'], (5,2), self.name, font)], justification='center')],
            [self._pad()]
        ]
        layout = sg.Column(layout, vertical_alignment='top')
        return layout
    
    def listenEvents(self, event, values):
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        position = list(sum(self.mover.getWorkspacePosition(), ()))
        cache_position = position.copy()
        if event in [self._mangle(f'-{e}-') for e in ('safe', 'home', 'Go', 'Clear', 'Reset')]:
            self.flags['update_position'] = True
            
        # 1. Home
        if event == self._mangle(f'-home-'):
            self.mover.home()
        
        # 2. Safe
        if event == self._mangle(f'-safe-'):
            try:
                coord = position[:2] + [self.mover.heights['safe']]
            except AttributeError:
                coord = self.mover.home_position
            if self.mover.coordinates[2] >= coord[2]:
                print('Already cleared safe height. Staying put...')
            else:
                orientation = position[-3:]
                self.mover.moveTo(coord, orientation)
            
        # 3. XYZ buttons
        if event in self.buttons.keys():
            axis, displacement = self.buttons[event]
            self.mover.move(axis, displacement)
            self.flags['update_position'] = True
            position = list(sum(self.mover.getWorkspacePosition(), ()))
            
        # 4. abg sliders
        if event in [self._mangle(f'-{axis}-SLIDER-') for axis in ['a','b','g']]:
            orientation = [float(values[self._mangle(f'-{axis}-SLIDER-')]) for axis in ['a','b','g']]
            self.mover.rotateTo(orientation)
            self.flags['update_position'] = True
            position = list(sum(self.mover.getWorkspacePosition(), ()))
            
        # 5. Go to position
        if event == self._mangle(f'-Go-'):
            coord = [float(values[self._mangle(f'-{axis}-VALUE-')]) for axis in ['X','Y','Z']]
            orientation = [float(values[self._mangle(f'-{axis}-VALUE-')]) for axis in ['a','b','g']]
            self.mover.moveTo(coord, orientation)
            position = list(sum(self.mover.getWorkspacePosition(), ()))
        
        # 6. Reset mover
        if event == self._mangle(f'-Reset-'):
            self.mover.reset()
            position = cache_position
        
        # 7. Update position
        updates = {}
        if self.flags['update_position']:
            for i,axis in enumerate(['X','Y','Z','a','b','g']):
                updates[self._mangle(f'-{axis}-VALUE-')] = dict(value=position[i])
                if axis in ['a','b','g']:
                    updates[self._mangle(f'-{axis}-SLIDER-')] = dict(value=position[i])
        self.flags['update_position'] = False
        return updates


class ViewerPanel(Panel):
    """
    Viewer Panel class

    Args:
        viewer (obj): Viewer object
        name (str, optional): name of panel. Defaults to 'VIEW'.
        theme (str, optional): name of theme. Defaults to THEME.
        typeface (str, optional): name of typeface. Defaults to TYPEFACE.
        font_sizes (list, optional): list of font sizes. Defaults to FONT_SIZES.
        group (str, optional): name of group. Defaults to 'viewer'.
    """
    def __init__(self, viewer, name='VIEW', theme=THEME, typeface=TYPEFACE, font_sizes=FONT_SIZES, group='viewer'):
        super().__init__(name=name, theme=theme, typeface=typeface, font_sizes=font_sizes, group=group)
        self.viewer = viewer
        self.display_box = self._mangle('-IMAGE-')
        
        self.flags['update_display'] = True
        self._last_read_time = time.time()
        return
    
    def close(self):
        """
        Close window
        """
        self.viewer.close()
        return
        
    def getLayout(self, title_font_level=1, **kwargs):
        """
        Get layout object

        Args:
            title_font_level (int, optional): index of font size from levels in font_sizes. Defaults to 1.

        Returns:
            PySimpleGUI.Column: Column object
        """
        font = (self.typeface, self.font_sizes[title_font_level])
        layout = super().getLayout(f'{self.name} Control', justification='center', font=font)
        layout = [
            [layout],
            [sg.Image(filename='', key=self.display_box, enable_events=True)]
        ]
        layout = sg.Column(layout, vertical_alignment='top')
        return layout
    
    def listenEvents(self, event, values):
        """
        Listen to events and act on values

        Args:
            event (str): event triggered
            values (dict): dictionary of values from window

        Returns:
            dict: dictionary of updates
        """
        updates = {}
        if self.flags['update_display']:
            frame_interval = time.time() - self._last_read_time
            fps = round(1/frame_interval, 2)
            ret, image = self.viewer.getImage()
            self._last_read_time = time.time()
            image = image.addText(f'FPS: {fps}', position=(0,image.frame.shape[0]-5), inplace=False)
            updates[self.display_box] = dict(data=image.encode())
        return updates

class LoaderPanel(Panel):
    """
    Loader Panel class

    Args:
        name (str, optional): name of panel. Defaults to ''.
        theme (str, optional): name of theme. Defaults to THEME.
        typeface (str, optional): name of typeface. Defaults to TYPEFACE.
        font_sizes (list, optional): list of font sizes. Defaults to FONT_SIZES.
        group (str, optional): name of group. Defaults to None.
    """
    def __init__(self, name='', theme=THEME, typeface=TYPEFACE, font_sizes=FONT_SIZES, group=None):
        super().__init__(name, theme, typeface, font_sizes, group)
        return
    
    