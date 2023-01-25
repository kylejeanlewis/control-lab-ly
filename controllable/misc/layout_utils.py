# %% -*- coding: utf-8 -*-
"""
Adapted from @Pablo's labware code

Created: Tue 2023/01/25 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import json
import numpy as np
import os
import pkgutil

# Local application imports
print(f"Import: OK <{__name__}>")

class Deck(object):
    def __init__(self, deck_file:str, layout_file:str = None, package:str = None):
        self.details = self._read_json(json_file=deck_file, package=package)
        self._slots = {}
        self.load_layout(layout_file=layout_file, package=package)
        pass
    
    def __repr__(self) -> str:
        pass
    
    @property
    def slots(self):
        return self._slots
    
    def _read_json(self, json_file:str, package:str = None):
        if package is not None:
            jsn = pkgutil.get_data(package, json_file).decode('utf-8')
        else:
            with open(json_file) as file:
                jsn = file.read()
        return json.loads(jsn)
    
    def get_slot(self, index):
        return self._slots.get(index)
    
    def load_labware(self, slot, labware_file:str):
        top_left_coordinate = self.details.get(slot)
        self._slots[slot] = Labware(top_left_coordinate=top_left_coordinate, labware_file=labware_file)
        return
    
    def load_layout(self, layout_file:str, package:str = None):
        if layout_file is None:
            return
        layout = self._read_json()
        return

 
class Labware(object):
    def __init__(self, top_left_coordinate:tuple, labware_file:str, package:str = None):
        self.details = self._read_json(json_file=labware_file, package=package)
        self.reference_point = top_left_coordinate
        self._wells = {}
        pass
    
    def __repr__(self) -> str:
        pass
    
    @property
    def centre(self):
        dimensions = self.details.get('dimensions',{})
        x = dimensions.get('xDimension', 0)
        y = dimensions.get('yDimension', 0)
        z = dimensions.get('zDimension', 0)
        coordinates = np.array(self.reference_point) + np.array((x/2,-y/2,z))
        return tuple(coordinates)
    
    @property
    def columns(self):
        return self.details.get('ordering', [[]])
    
    @property
    def rows(self):
        columns = self.columns
        list(zip(*columns))
        return 
    
    @property
    def wells(self):
        return self._wells
    
    def _read_json(self, json_file:str, package:str = None):
        if package is not None:
            jsn = pkgutil.get_data(package, json_file).decode('utf-8')
        else:
            with open(json_file) as file:
                jsn = file.read()
        return json.loads(jsn)
    
    def get_column(self, name:str = None, index:int = None):
        return
    
    def get_row(self, name:str = None, index:int = None):
        return
    
    def get_well(self, name:str = None, index:tuple = None):
        return
    
    def load_wells(self):
        wells = self.details.get('wells',{})
        for well in wells:
            self._wells[well] = Well(wells[well], self.reference_point)
        return


class Well(object):
    def __init__(self, details, reference_point):
        self.details = details  # depth,totalLiquidVolume,shape,diameter,x,y,z
        self.reference_point = reference_point
        pass
    
    def __repr__(self) -> str:
        pass
    
    @property
    def top(self):
        return
    
    @property
    def middle(self):
        return
    
    @property
    def bottom(self):
        return