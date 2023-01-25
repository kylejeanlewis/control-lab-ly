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
import pkgutil

# Local application imports
print(f"Import: OK <{__name__}>")

def read_json(json_file:str, package:str = None):
    if package is not None:
        jsn = pkgutil.get_data(package, json_file).decode('utf-8')
    else:
        with open(json_file) as file:
            jsn = file.read()
    return json.loads(jsn)


class Well(object):
    def __init__(self, labware_info:dict, name:str, details:dict):
        self.details = details  # depth,totalLiquidVolume,shape,diameter,x,y,z
        self.labware_info = labware_info
        self.name = name
        self.reference_point = self.labware_info.get('reference_point', (0,0,0))
        pass
    
    def __repr__(self) -> str:
        return f"{self.name} in {self.labware_info.get('name','')} at Slot {self.labware_info.get('slot','')}" 
    
    @property
    def center(self):
        return tuple(map(sum, zip(self.reference_point, self.offset)))
    
    @property
    def offset(self):
        x = self.details.get('x', 0)
        y = self.details.get('y', 0)
        z = self.details.get('z', 0)
        return x,y,z
    
    @property
    def bottom(self):
        return self.center
    @property
    def middle(self):
        depth = self.details.get('depth', 0)
        return tuple(map(sum, zip(self.center, (0,0,depth/2))))
    @property
    def top(self):
        depth = self.details.get('depth', 0)
        return tuple(map(sum, zip(self.center, (0,0,depth))))


class Labware(object):
    def __init__(self, slot:str, bottom_left_coordinates:tuple, labware_file:str, package:str = None):
        self.details = self._read_json(json_file=labware_file, package=package)
        self.name = self.details.get('metadata',{}).get('displayName', '')
        self.reference_point = bottom_left_coordinates
        self.slot = slot
        self._wells = {}
        self.load_wells()
        pass
    
    def __repr__(self) -> str:
        return f"{self.name} at Slot {self.slot}" 
    
    @property
    def info(self):
        return {'name':self.name, 'reference_point':self.reference_point, 'slot':self.slot}
    
    @property
    def center(self):
        dimensions = self.details.get('dimensions',{})
        x = dimensions.get('xDimension', 0)
        y = dimensions.get('yDimension', 0)
        z = dimensions.get('zDimension', 0)
        return tuple(map(sum, zip(self.reference_point, (x/2,y/2,z))))
    
    @property
    def columns(self):
        columns_list = self.columns_list
        return {str(c+1): columns_list[c] for c in range(len(columns_list))}
    @property
    def columns_list(self):
        return self.details.get('ordering', [[]])
    
    @property
    def rows(self):
        first_column = self.details.get('ordering', [[]])[0]
        rows_list = self.rows_list
        return {w[0]: rows_list[r] for r,w in enumerate(first_column)}
    @property
    def rows_list(self):
        columns = self.columns_list
        return [list(z) for z in zip(*columns)]
       
    @property
    def wells(self):
        return self._wells
    @property
    def wells_list(self):
        return [self._wells[well] for well in self.details.get('wells',{})]
    
    def _read_json(self, json_file:str, package:str = None):
        return read_json(json_file, package)
    
    def get_well(self, name:str):
        return self.wells.get(name)
    
    def load_wells(self):
        wells = self.details.get('wells',{})
        for well in wells:
            self._wells[well] = Well(labware_info=self.info, name=well, details=wells[well])
        return


class Deck(object):
    def __init__(self, layout_file:str = None, package:str = None):
        self.details = {}
        self._slots = {}
        self.load_layout(layout_file=layout_file, package=package)
        pass
    
    def __repr__(self) -> str:
        labwares = [''] + [repr(labware) for labware in self.slots.values()]
        labware_string = '\n'.join(labwares)
        return f"Deck with labwares:{labware_string}" 
    
    @property
    def slots(self):
        return self._slots
    
    def _read_json(self, json_file:str, package:str = None):
        return read_json(json_file, package)
    
    def get_slot(self, index):
        return self._slots.get(str(index))
    
    def load_labware(self, slot, labware_file:str, package:str = None):
        bottom_left_coordinates = tuple(self.details.get('reference_points',{}).get(str(slot)))
        self._slots[str(slot)] = Labware(slot=str(slot), bottom_left_coordinates=bottom_left_coordinates, labware_file=labware_file, package=package)
        return
    
    def load_layout(self, layout_file:str, package:str = None, labware_package:str = None):
        if layout_file is None:
            return
        self.details = self._read_json(json_file=layout_file, package=package)
        slots = self.details.get('slots', {})
        for slot,labware_file in slots.items():
            self.load_labware(slot=slot, labware_file=labware_file, package=labware_package)
        return
