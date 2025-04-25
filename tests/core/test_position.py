import pytest
from copy import deepcopy
import logging
import os
from pathlib import Path

from matplotlib import pyplot as plt
import numpy as np
from scipy.spatial.transform import Rotation

from ..context import controllably
from controllably.core.position import (
    convert_to_position, get_transform, Position, Well, Labware, Slot, Deck, BoundingVolume, BoundingBox)

_position = Position([1, 2, 3], Rotation=Rotation.from_euler('zyx', [4, 5, 6], degrees=True))
HERE = Path(__file__).parent.absolute()

@pytest.fixture
def position():
    return deepcopy(_position)

@pytest.mark.parametrize("value", [
    [1,2,3],
    [[1,2,3]],
    [[1,2,3],[4,5,6]],
    np.array([1,2,3]),
    np.array([[1,2,3],[4,5,6]]),
    _position
])
def test_convert_to_position(value):
    pos = convert_to_position(value)
    assert isinstance(pos, Position)
    
    if isinstance(value, Position):
        assert np.allclose(pos.coordinates, value.coordinates)
        assert np.allclose(pos.rotation, value.rotation)
    else:
        if len(value) == 2:
            coords, rotation = value
        else:
            coords, rotation = value, [0,0,0]
        coords = np.array(coords).astype(np.float32)
        rotation = np.array(rotation).astype(np.float32)
        assert np.allclose(pos.coordinates, coords)
        assert np.allclose(pos.rotation, rotation)

@pytest.mark.parametrize("final, scale_, coord_, rot_", [
    ([[1, 1, 1], [2, 1, 1], [1, 2, 1], [1, 1, 2]], 1.0, [1, 1, 1], [0, 0, 0]),
    ([[2, 1, 1], [2, 2, 1], [1, 1, 1], [2, 1, 2]], 1.0, [2, 1, 1], [90, 0, 0]),
    ([[2, 1, 1], [2, 1.5, 1], [1.5, 1, 1], [2, 1, 1.5]], 0.5, [2, 1, 1], [90, 0, 0])
])
def test_get_transform(final, scale_, coord_, rot_):
    initial_points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
    final_points = np.array(final)
    transform, scale = get_transform(initial_points, final_points)
    assert isinstance(transform, Position)
    assert np.isclose(scale, scale_)
    assert np.allclose(transform.coordinates, coord_)
    assert np.allclose(transform.rotation, rot_)


class TestPosition:
    def test_init(self, position):
        assert isinstance(position, Position)
        assert np.allclose(position.coordinates, [1, 2, 3])
        assert np.allclose(position.rotation, [4, 5, 6])

    def test_str_repr(self, position):
        assert str(position) == "[1 2 3] | [4. 5. 6.] (euler)"
        assert repr(position) == "[1 2 3]|[4. 5. 6.]"
        
    def test_to_from_json(self, position):
        assert isinstance(position, Position)
        json_str = position.toJSON()
        assert isinstance(json_str, str)
        pos_from_json = Position.fromJSON(json_str)
        assert position == pos_from_json
        
        json_str_scalar_first = position.toJSON(scalar_first=True)
        assert isinstance(json_str_scalar_first, str)
        pos_from_json_scalar_first = Position.fromJSON(json_str_scalar_first)
        assert position == pos_from_json_scalar_first
        
        with pytest.raises(ValueError):
            json_str: str = position.toJSON()
            assert isinstance(json_str, str)
            pos_from_json = Position.fromJSON(json_str.replace('xyzw', 'abcd'))
        
    def test_properties(self, position):
        assert isinstance(position, Position)
        assert np.isclose(position.x, 1)
        assert np.isclose(position.y, 2)
        assert np.isclose(position.z, 3)
        assert np.isclose(position.a, 6)
        assert np.isclose(position.b, 5)
        assert np.isclose(position.c, 4)
        
        position.coordinates = (10,20,30)
        assert np.allclose(position.coordinates, [10, 20, 30])
        with pytest.raises(AssertionError):
            position.coordinates = (10,20)
        
        position.rotation = Rotation.from_euler('zyx', [12, 13, 14], degrees=True)
        assert np.allclose(position.rotation, [12, 13, 14])
        with pytest.raises(AssertionError):
            position.rotation = [12, 13]
        assert np.allclose(position.rot_matrix, position.Rotation.as_matrix())

    @pytest.mark.parametrize("rotation_type, rotation_method", [
        ('quaternion', 'as_quat'),
        ('matrix', 'as_matrix'),
        ('angle_axis', 'as_rotvec'),
        ('mrp', 'as_mrp'),
        ('unknown', None)
    ])
    def test_rotation_types(self, rotation_type, rotation_method, position):
        assert isinstance(position, Position)
        position.rotation_type = rotation_type
        if rotation_type != 'unknown':
            assert position.rotation_type == rotation_type
            assert np.allclose(position.rotation, getattr(position.Rotation, rotation_method)())
        else:
            with pytest.raises(ValueError):
                position.rotation_type = rotation_type
                _ = position.rotation
    
    def test_eq(self, position):
        other = Position([1, 2, 3], Rotation=Rotation.from_euler('zyx', [4, 5, 6], degrees=True))
        assert position == other
    
    @pytest.mark.parametrize("other", [
        Position([7, 8, 9]),
        Position([7, 8, 9], Rotation=Rotation.from_euler('zyx', [10, 11, 12], degrees=True))
    ])
    def test_apply(self, other, position):
        assert isinstance(position, Position)
        init_rotation = position.Rotation
        rotation = Rotation.from_euler('zyx', [10, 11, 12], degrees=True)
        final_rotation = rotation * init_rotation if any(other.rotation) else init_rotation
        other.apply(position)
        assert np.allclose(position.coordinates, (8,10,12))
        assert np.allclose(position.Rotation.as_quat(), (final_rotation).as_quat())
        
    def test_invert(self, position):
        assert isinstance(position, Position)
        inv_pos = position.invert()
        assert np.allclose(inv_pos.coordinates, (-1, -2, -3))
        assert np.allclose(inv_pos.Rotation.as_quat(), position.Rotation.inv().as_quat()) 

    def test_orientate(self, position):
        assert isinstance(position, Position)
        init_rotation = position.Rotation
        rotation = Rotation.from_euler('zyx', [7, 8, 9], degrees=True)
        new_position = position.orientate(rotation, inplace=False)
        assert np.allclose(position.Rotation.as_quat(), init_rotation.as_quat())
        assert np.allclose(new_position.Rotation.as_quat(), (rotation*init_rotation).as_quat())
        
        position.orientate(rotation)
        assert np.allclose(position.coordinates, (1,2,3))
        assert np.allclose(position.Rotation.as_quat(), (rotation*init_rotation).as_quat())
        
    def test_translate(self, position):
        assert isinstance(position, Position)
        init_coordinates = position.coordinates
        new_position = position.translate([7, 8, 9], inplace=False)
        assert np.allclose(position.coordinates, init_coordinates)
        assert np.allclose(new_position.coordinates, (8,10,12))
        
        position.translate([7, 8, 9])
        assert np.allclose(position.coordinates, (8,10,12))


@pytest.fixture
def main_deck(monkeypatch):
    monkeypatch.setattr('os.getcwd', lambda : str(HERE))
    deck_file_main = 'control-lab-le/tests/core/examples/layout_main.json'
    return Deck.fromFile(deck_file_main)

@pytest.fixture
def sub_deck(main_deck):
    return main_deck.zones['zone_A']


class TestDeck:
    def test_init(self, main_deck):
        assert isinstance(main_deck, Deck)
        assert main_deck.name == 'Example Layout (main)'
        assert main_deck.parent is None
        assert main_deck.reference == Position()
        assert np.allclose(main_deck.offset, (450,300,0))
        assert np.allclose(main_deck.center, (450,300,0))
        assert np.allclose(main_deck.dimensions, (900,600,0))
        
    def test_slots_and_zones(self, main_deck):
        assert isinstance(main_deck, Deck)
        assert len(main_deck.slots) == 1
        assert len(main_deck.zones) == 1
        assert 'zone_A' in main_deck.zones
        assert 'zone_A' in main_deck.slots
        assert main_deck.on.zone_A == main_deck.zones['zone_A']
    
    def test_get_all_positions(self, main_deck):
        assert isinstance(main_deck, Deck)
        all_positions = main_deck.getAllPositions()
        assert len(all_positions) == 2
        assert np.allclose(all_positions['self'], (450,300,0))
        assert np.allclose(all_positions['zone_A']['self'], (750,300,0))
        
    def test_exclusion_zone(self, main_deck):
        assert isinstance(main_deck, Deck)
        assert len(main_deck.exclusion_zone) == 2
        assert main_deck.isExcluded((749.175,375.875,52.95))
        assert not main_deck.isExcluded((0,0,0))
        
    def test_zone(self, sub_deck):
        assert isinstance(sub_deck, Deck)
        assert sub_deck.name == 'zone_A'
        assert isinstance(sub_deck.parent, Deck)
        assert sub_deck.parent.name == 'Example Layout (main)'
        assert sub_deck.reference == Position()
        assert sub_deck.bottom_left_corner == Position([600,600,0], Rotation=Rotation.from_euler('zyx', [-90, 0, 0], degrees=True))
        assert np.allclose(sub_deck.offset, (300,150,0))
        assert np.allclose(sub_deck.center, (750,300,0))
        assert np.allclose(sub_deck.dimensions, (300,-600,0))
        assert len(sub_deck.exclusion_zone) == 2
        
    def test_slot(self, sub_deck):
        assert isinstance(sub_deck, Deck)
        assert len(sub_deck.slots) == 7
        assert len(sub_deck.zones) == 0
        assert 'slot_04' in sub_deck.slots
        assert sub_deck.at.slot_04 == sub_deck.slots['slot_04']
        assert sub_deck.getSlot(4) == sub_deck.slots['slot_04']
        assert 'zone_A comprising:' in str(sub_deck)
        assert len(str(sub_deck).strip().split('\n')) == len(sub_deck.slots) + 1
        assert len(repr(sub_deck).strip().split('\n')) == len(sub_deck.slots) + 1
        
    def test_labware(self, sub_deck):
        assert isinstance(sub_deck, Deck)
        assert isinstance(sub_deck.slots['slot_04'].loaded_labware, Labware)
        assert sub_deck.slots['slot_01'].loaded_labware is None
        sub_deck.transferLabware(sub_deck.at.slot_04, sub_deck.at.slot_01)
        assert isinstance(sub_deck.slots['slot_01'].loaded_labware, Labware)
        assert sub_deck.slots['slot_04'].loaded_labware is None
        
        this_labware = sub_deck.removeLabware(sub_deck.slots['slot_01'])
        assert sub_deck.slots['slot_05'].loaded_labware is None
        sub_deck.loadLabware(sub_deck.slots['slot_01'], this_labware)
        assert isinstance(sub_deck.slots['slot_01'].loaded_labware, Labware)
        
    def test_recursive(self, caplog, monkeypatch):
        monkeypatch.setattr('os.getcwd', lambda : str(HERE))
        deck_file_main = 'control-lab-le/tests/core/examples/layout_recursive_1.json'
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                _ = Deck.fromFile(deck_file_main)
            assert "Nested deck lineage:" in caplog.text


@pytest.fixture
def slot_empty(sub_deck):
    return sub_deck.slots['slot_01']


class TestSlot:
    def test_init(self, slot_empty):
        assert isinstance(slot_empty, Slot)
        assert slot_empty.name == 'slot_01'
        assert isinstance(slot_empty.parent, Deck)
        assert slot_empty.parent.name == 'zone_A'
        assert slot_empty.reference == Position([600,600,0], Rotation=Rotation.from_euler('zyx', [-90, 0, 0], degrees=True))
        assert slot_empty.bottom_left_corner == Position([606.5,439.5,0], Rotation=Rotation.from_euler('zyx', [-90, 0, 0], degrees=True))
        assert np.allclose(slot_empty.offset, (63.88,42.74,0))
        assert np.allclose(slot_empty.center, (649.24,375.62,0))
        assert np.allclose(slot_empty.dimensions, (85.48,-127.76,0))
        assert np.allclose(slot_empty.fromCenter((10,20,30)), (659.24,395.62,30))
        assert len(slot_empty.details) in (4,5)
        
    def test_str_repr(self, slot_empty):
        assert isinstance(slot_empty, Slot)
        assert '[Vacant]' in str(slot_empty)
        assert '<- Vacant' in repr(slot_empty)
        
    def test_load_labware_from_configs(self, slot_empty):
        assert isinstance(slot_empty, Slot)
        slot_empty.loadLabwareFromConfigs(slot_empty.parent.slots['slot_04'].loaded_labware.details)
        assert isinstance(slot_empty.loaded_labware, Labware)


@pytest.fixture
def slot_loaded(sub_deck):
    return sub_deck.slots['slot_04']

@pytest.fixture
def labware(slot_loaded):
    return slot_loaded.loaded_labware

@pytest.fixture
def labware_stackable(slot_empty, monkeypatch):
    monkeypatch.setattr('os.getcwd', lambda : str(HERE))
    labware_file = 'control-lab-le/tests/core/examples/labware_wellplate.json'
    slot_empty.loadLabwareFromFile(labware_file)
    return slot_empty.loaded_labware

class TestLabware:
    def test_init(self, labware):
        assert isinstance(labware, Labware)
        assert labware.name == 'Eppendorf Motion 96 Tip Rack 1000 uL' 
        assert isinstance(labware.parent, Slot)
        assert labware.parent.name == 'slot_04'
        assert labware.reference == Position([706.5,439.5,0], Rotation=Rotation.from_euler('zyx', [-90, 0, 0], degrees=True))
        assert labware.bottom_left_corner == Position([706.5,439.5,0], Rotation=Rotation.from_euler('zyx', [-90, 0, 0], degrees=True))
        assert np.allclose(labware.offset, (63.625,42.675,52.95))
        assert np.allclose(labware.center, (749.175,375.875,52.95))
        assert np.allclose(labware.top, (749.175,375.875,105.9))
        assert np.allclose(labware.dimensions, (85.35,-127.25,105.9))
        assert labware.columns == {i:[f'{r}{i}' for r in 'ABCDEFGH'] for i in range(1,13)}
        assert labware.rows == {r:[f'{r}{i}' for i in range(1,13)] for r in 'ABCDEFGH'}
        assert not labware.is_stackable
        assert labware.is_tiprack
        assert 'A1' in labware.wells
        assert labware.at.A1 == labware.wells['A1']
    
    def test_str_repr(self, labware):
        assert isinstance(labware, Labware)
        assert labware.parent.name in str(labware)
        assert labware.parent.name in repr(labware)
    
    def test_exclusion_zone(self, labware):
        assert isinstance(labware, Labware)
        assert (749.175,375.875,52.95) in labware.exclusion_zone
        assert (749.175,375.875,52.95) in labware.parent.exclusion_zone
        
    def test_from_top(self, labware):
        assert isinstance(labware, Labware)
        assert np.allclose(labware.fromTop((10,20,30)), (759.175,395.875,135.9))
        
    def test_list_wells(self, labware):
        assert isinstance(labware, Labware)
        assert labware.listWells('col') == [labware.getWell(w) for w in labware.details['wells']]
        assert labware.listWells('row') == [labware.getWell(labware.details['ordering'][i][r]) for r in range(0,8) for i in range(0,12)]
        with pytest.raises(ValueError):
            labware.listWells('unknown')
            
    def test_list_columns_rows(self, labware):
        assert isinstance(labware, Labware)
        assert labware.listColumns() == [[f'{r}{i}' for r in 'ABCDEFGH'] for i in range(1,13)]
        assert labware.listRows() == [[f'{r}{i}' for i in range(1,13)] for r in 'ABCDEFGH']
        

class TestLabwareStackable:
    def test_init(self, labware_stackable):
        assert isinstance(labware_stackable, Labware)
        assert labware_stackable.is_stackable
        base_slot = labware_stackable.parent
        assert isinstance(base_slot, Slot)
        
        slot_above = labware_stackable.slot_above
        assert isinstance(slot_above, Slot)
        assert slot_above.name == 'slot_01_a'
        assert isinstance(base_slot.slot_above, Slot)
        assert base_slot.slot_above == slot_above
        assert slot_above.slot_below == base_slot
        
    def test_remove_labware(self, labware_stackable):
        assert isinstance(labware_stackable, Labware)
        slot_above = labware_stackable.slot_above
        assert isinstance(slot_above, Slot)
        base_slot = labware_stackable.parent
        assert isinstance(base_slot, Slot)
        
        slot_above.loadLabwareFromConfigs(labware_stackable.details)
        assert isinstance(slot_above.loaded_labware, Labware)
        with pytest.raises(AssertionError, match="Another Labware is stacked above"):
            base_slot.removeLabware()
        slot_above.removeLabware()
        
        labware_stackable = base_slot.removeLabware()
        assert base_slot.loaded_labware is None
        assert base_slot.slot_above is None
        labware_stackable.is_stackable = False
        assert labware_stackable.slot_above is None
        
    def test_load_labware_from_configs_bad(self, labware_stackable):
        assert isinstance(labware_stackable, Labware)
        base_slot = labware_stackable.parent
        assert isinstance(base_slot, Slot)
        bad_details = labware_stackable.details
        bad_details.pop('slotAbove')
        with pytest.raises(AssertionError, match="No details for Slot above"):
            base_slot.loadLabwareFromConfigs(bad_details)


@pytest.fixture
def well_circular(labware):
    return labware.getWell('A1')

@pytest.fixture
def well_rectangular(labware):
    details = {
        'x': 1, 'y': 2, 'z': 3, 'shape': 'rectangular', 
        'depth': 4, 'totalLiquidVolume': 5, 'xDimension': 6, 'yDimension': 7
    }
    return Well(name='A1', _details=details, parent=labware)


class TestWell:
    def test_init(self, well_circular):
        assert isinstance(well_circular, Well)
        assert well_circular.name == 'A1'
        assert isinstance(well_circular.parent, Labware)
        assert well_circular.parent.name == 'Eppendorf Motion 96 Tip Rack 1000 uL' 
        assert well_circular.reference == Position([706.5,439.5,0], Rotation=Rotation.from_euler('zyx', [-90, 0, 0], degrees=True))
        
    def test_str_repr(self, well_rectangular):
        assert isinstance(well_rectangular, Well)
        assert str(well_rectangular.parent) in str(well_rectangular)
        assert repr(well_rectangular.parent) in repr(well_rectangular)
    
    def test_circular(self, well_circular):
        assert isinstance(well_circular, Well)
        assert np.allclose(well_circular.offset, (14.5,73.15,9))
        assert np.allclose(well_circular.center, (779.65,425.0,9))
        assert np.allclose(well_circular.bottom, (779.65,425.0,9))
        assert np.allclose(well_circular.middle, (779.65,425.0,57.45))
        assert np.allclose(well_circular.top, (779.65,425.0,105.9))
        
        assert well_circular.depth == 96.9
        assert well_circular.volume == 0
        assert well_circular.capacity == 1000
        assert well_circular.dimensions == (6,)
        assert well_circular.base_area == np.pi * 3**2
        assert well_circular.level == 0
        assert well_circular.shape == 'circular'
        fig, ax = plt.subplots()
        assert isinstance(well_circular._draw(ax), plt.Circle)

    def test_rectangular(self, well_rectangular):
        assert isinstance(well_rectangular, Well)
        assert np.allclose(well_rectangular.offset, (1,2,3))
        assert np.allclose(well_rectangular.center, (708.5,438.5,3))
        assert np.allclose(well_rectangular.bottom, (708.5,438.5,3))
        assert np.allclose(well_rectangular.middle, (708.5,438.5,5))
        assert np.allclose(well_rectangular.top, (708.5,438.5,7))
        assert len(well_rectangular.details) == 8
        
        assert well_rectangular.depth == 4
        assert well_rectangular.volume == 0
        assert well_rectangular.capacity == 5
        assert well_rectangular.dimensions == (6,7)
        assert well_rectangular.base_area == 42
        assert well_rectangular.level == 0
        assert well_rectangular.shape == 'rectangular'
        fig, ax = plt.subplots()
        assert isinstance(well_rectangular._draw(ax), plt.Rectangle)

    def test_from_bottom_middle_top(self, well_circular):
        assert isinstance(well_circular, Well)
        assert np.allclose(well_circular.fromBottom((10,20,30)), (789.65,445.0,39))
        assert np.allclose(well_circular.fromMiddle((10,20,30)), (789.65,445.0,87.45))
        assert np.allclose(well_circular.fromTop((10,20,30)), (789.65,445.0,135.9))

    def test_level(self, well_rectangular):
        assert isinstance(well_rectangular, Well)
        well_rectangular.volume = 10
        assert well_rectangular.volume == 10
        assert well_rectangular.level == 10 / well_rectangular.base_area

    def test_errors(self, labware, caplog):
        details = {
            'x': 1, 'y': 2, 'z': 3, 'shape': 'unknown', 
            'depth': 4, 'totalLiquidVolume': 5, 'xDimension': 6, 'yDimension': 7
        }
        with caplog.at_level(logging.ERROR):
            well = Well(name='A1', _details=details, parent=labware)
            assert 'Invalid shape: unknown' in caplog.text
        with caplog.at_level(logging.ERROR):
            fig, ax = plt.subplots()
            _ = well._draw(ax)
            assert 'Invalid shape: unknown' in caplog.text.strip().split('\n')[-1]
        with pytest.raises(AssertionError):
            with caplog.at_level(logging.ERROR):
                _ = well.base_area


def test_bounding_volume():
    func = {'sphere': lambda p: np.linalg.norm(p) <= 1}
    volume = BoundingVolume(parametric_function=func)
    assert volume.contains([0, 0, 0])
    assert not volume.contains([2, 2, 2])
    assert [0,0,0] in volume
    assert [2,2,2] not in volume

def test_bounding_box():
    reference = Position([0, 0, 0])
    dimensions = [1, 1, 1]
    buffer = [[0, 0, 0], [0, 0, 0]]
    box = BoundingBox(reference=reference, dimensions=dimensions, buffer=buffer)
    assert box.contains([0.5, 0.5, 0.5])
    assert not box.contains([1.5, 1.5, 1.5])


class TestDrawing:
    def test_deck(self, main_deck):
        fig, ax = main_deck.show()
        assert isinstance(fig, plt.Figure)
        assert isinstance(ax, plt.Axes)

    def test_labware(self, labware):
        fig, ax = labware.show()
        assert isinstance(fig, plt.Figure)
        assert isinstance(ax, plt.Axes)

    def test_labware_stackable(self, labware):
        stack = labware.parent.parent.slots['slot_02'].loaded_labware
        stack.slot_above.loadLabwareFromConfigs(stack.details)
        fig, ax = stack.show()
        assert isinstance(fig, plt.Figure)
        assert isinstance(ax, plt.Axes)
