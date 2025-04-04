import pytest
import logging
from matplotlib import pyplot as plt
import numpy as np
from scipy.spatial.transform import Rotation

from controllably.core.position import (
    convert_to_position, get_transform, Position, Well, Labware, Slot, Deck, BoundingVolume, BoundingBox
)

@pytest.fixture
def position():
    return Position([1, 2, 3], Rotation=Rotation.from_euler('zyx', [4, 5, 6], degrees=True))

@pytest.mark.parametrize("value", [
    [1,2,3],
    [[1,2,3]],
    [[1,2,3],[4,5,6]],
    np.array([1,2,3]),
    np.array([[1,2,3],[4,5,6]])
])
def test_convert_to_position(value):
    pos = convert_to_position(value)
    if len(value) == 2:
        coords, rotation = value
    else:
        coords, rotation = value, [0,0,0]
    coords = np.array(coords).astype(np.float32)
    rotation = np.array(rotation).astype(np.float32)
    assert isinstance(pos, Position)
    assert np.allclose(pos.coordinates, coords)
    assert np.allclose(pos.rotation, rotation)
    
def test_convert_to_position_from_position(position):
    pos = convert_to_position(position)
    assert isinstance(pos, Position)
    assert np.allclose(pos.coordinates, position.coordinates)
    assert np.allclose(pos.rotation, position.rotation)

def test_get_transform_translate():
    initial_points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
    final_points = np.array([[1, 1, 1], [2, 1, 1], [1, 2, 1], [1, 1, 2]])
    transform, scale = get_transform(initial_points, final_points)
    assert isinstance(transform, Position)
    assert np.isclose(scale, 1.0)
    assert np.allclose(transform.coordinates, [1, 1, 1])
    assert np.allclose(transform.rotation, [0, 0, 0])

def test_get_transform_translate_rotate():
    initial_points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
    final_points = np.array([[2, 1, 1], [2, 2, 1], [1, 1, 1], [2, 1, 2]])
    transform, scale = get_transform(initial_points, final_points)
    assert isinstance(transform, Position)
    assert np.isclose(scale, 1.0)
    assert np.allclose(transform.coordinates, [2, 1, 1])
    assert np.allclose(transform.rotation, [90, 0, 0])
    
def test_get_transform_translate_rotate_scale():
    initial_points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
    final_points = np.array([[2, 1, 1], [2, 1.5, 1], [1.5, 1, 1], [2, 1, 1.5]])
    transform, scale = get_transform(initial_points, final_points)
    assert isinstance(transform, Position)
    assert np.isclose(scale, 0.5)
    assert np.allclose(transform.coordinates, [2, 1, 1])
    assert np.allclose(transform.rotation, [90, 0, 0])

def test_position():
    pos = Position([1, 2, 3], Rotation=Rotation.from_euler('zyx', [4, 5, 6], degrees=True))
    assert np.allclose(pos.coordinates, [1, 2, 3])
    assert np.allclose(pos.rotation, [4, 5, 6])

    pos_json = pos.toJSON()
    assert isinstance(pos_json, str)
    pos_from_json = Position.fromJSON(pos_json)
    assert pos == pos_from_json
    pos_json = pos.toJSON(scalar_first=True)
    assert isinstance(pos_json, str)
    pos_from_json = Position.fromJSON(pos_json)
    assert pos == pos_from_json
    
    with pytest.raises(ValueError):
        pos_json = pos.toJSON()
        pos_json = pos_json.replace('xyzw', 'abcd')
        pos_from_json = Position.fromJSON(pos_json)
    
    assert not (pos == pos.coordinates)
    assert str(pos) == "[1 2 3] | [4. 5. 6.] (euler)"
    assert repr(pos) == "[1 2 3]|[4. 5. 6.]"
    
def test_position_properties(position):
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
def test_position_rotation_types(position, rotation_type, rotation_method):
    position.rotation_type = rotation_type
    if rotation_type != 'unknown':
        assert position.rotation_type == rotation_type
        assert np.allclose(position.rotation, getattr(position.Rotation, rotation_method)())
    else:
        with pytest.raises(ValueError):
            position.rotation_type = rotation_type
            _ = position.rotation
    
def test_position_equality(position):
    pos2 = Position([1, 2, 3], Rotation=Rotation.from_euler('zyx', [4, 5, 6], degrees=True))
    assert position == pos2
    
def test_position_apply_translation(position):
    pos2 = Position([7, 8, 9])
    init_rotation = position.Rotation
    pos2.apply(position)
    assert np.allclose(position.coordinates, (8,10,12))
    assert np.allclose(position.Rotation.as_quat(), init_rotation.as_quat())

def test_position_apply_translation_rotation(position):
    pos2 = Position([7, 8, 9], Rotation=Rotation.from_euler('zyx', [10, 11, 12], degrees=True))
    init_rotation = position.Rotation
    rotation = Rotation.from_euler('zyx', [10, 11, 12], degrees=True)
    pos2.apply(position)
    assert np.allclose(position.coordinates, (8,10,12))
    assert np.allclose(position.Rotation.as_quat(), (rotation*init_rotation).as_quat())
    
def test_position_invert(position):
    inv_pos = position.invert()
    assert np.allclose(inv_pos.coordinates, (-1, -2, -3))
    assert np.allclose(inv_pos.Rotation.as_quat(), position.Rotation.inv().as_quat()) 

def test_position_orientate(position):
    init_rotation = position.Rotation
    rotation = Rotation.from_euler('zyx', [7, 8, 9], degrees=True)
    new_position = position.orientate(rotation, inplace=False)
    assert np.allclose(position.Rotation.as_quat(), init_rotation.as_quat())
    assert np.allclose(new_position.Rotation.as_quat(), (rotation*init_rotation).as_quat())
    
    position.orientate(rotation)
    assert np.allclose(position.coordinates, (1,2,3))
    assert np.allclose(position.Rotation.as_quat(), (rotation*init_rotation).as_quat())
    
def test_position_translate(position):
    init_coordinates = position.coordinates
    new_position = position.translate([7, 8, 9], inplace=False)
    assert np.allclose(position.coordinates, init_coordinates)
    assert np.allclose(new_position.coordinates, (8,10,12))
    
    position.translate([7, 8, 9])
    assert np.allclose(position.coordinates, (8,10,12))


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


@pytest.fixture
def main_deck():
    deck_file_main = 'control-lab-le/tests/core/examples/layout_main.json'
    return Deck.fromFile(deck_file_main)

@pytest.fixture
def sub_deck(main_deck):
    return main_deck.zones['zone_A']

def test_main_deck(main_deck):
    assert main_deck.name == 'Example Layout (main)'
    assert main_deck.parent is None
    assert main_deck.reference == Position()
    assert np.allclose(main_deck.offset, (450,300,0))
    assert np.allclose(main_deck.center, (450,300,0))
    assert np.allclose(main_deck.dimensions, (900,600,0))
    assert len(main_deck.slots) == 1
    assert len(main_deck.zones) == 1
    assert 'zone_A' in main_deck.zones
    assert 'zone_A' in main_deck.slots
    assert main_deck.on.zone_A == main_deck.zones['zone_A']
    all_positions = main_deck.getAllPositions()
    assert len(all_positions) == 2
    assert np.allclose(all_positions['self'], (450,300,0))
    assert np.allclose(all_positions['zone_A']['self'], (750,300,0))
    assert len(main_deck.exclusion_zone) == 2
    assert main_deck.isExcluded((749.175,375.875,52.95))
    assert not main_deck.isExcluded((0,0,0))

def test_sub_deck(sub_deck):
    assert sub_deck.name == 'zone_A'
    assert isinstance(sub_deck.parent, Deck)
    assert sub_deck.parent.name == 'Example Layout (main)'
    assert sub_deck.reference == Position()
    assert sub_deck.bottom_left_corner == Position([600,600,0], Rotation=Rotation.from_euler('zyx', [-90, 0, 0], degrees=True))
    assert np.allclose(sub_deck.offset, (300,150,0))
    assert np.allclose(sub_deck.center, (750,300,0))
    assert np.allclose(sub_deck.dimensions, (300,-600,0))
    assert len(sub_deck.slots) == 7
    assert len(sub_deck.zones) == 0
    assert 'slot_04' in sub_deck.slots
    assert sub_deck.at.slot_04 == sub_deck.slots['slot_04']
    assert sub_deck.getSlot(4) == sub_deck.slots['slot_04']
    assert 'zone_A comprising:' in str(sub_deck)
    assert len(str(sub_deck).strip().split('\n')) == len(sub_deck.slots) + 1
    assert len(repr(sub_deck).strip().split('\n')) == len(sub_deck.slots) + 1
    assert isinstance(sub_deck.slots['slot_04'].loaded_labware, Labware)
    
    assert sub_deck.slots['slot_01'].loaded_labware is None
    sub_deck.transferLabware(sub_deck.at.slot_04, sub_deck.at.slot_01)
    assert isinstance(sub_deck.slots['slot_01'].loaded_labware, Labware)
    assert sub_deck.slots['slot_04'].loaded_labware is None
    
    this_labware = sub_deck.removeLabware(sub_deck.slots['slot_01'])
    assert sub_deck.slots['slot_05'].loaded_labware is None
    sub_deck.loadLabware(sub_deck.slots['slot_01'], this_labware)
    assert isinstance(sub_deck.slots['slot_01'].loaded_labware, Labware)
    
    assert len(sub_deck.exclusion_zone) == 2
    
def test_deck_recursive(caplog):
    deck_file_main = 'control-lab-le/tests/core/examples/layout_recursive_1.json'
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError):
            _ = Deck.fromFile(deck_file_main)
        assert "Nested deck lineage:" in caplog.text

@pytest.fixture
def slot_loaded(sub_deck):
    return sub_deck.slots['slot_04']

@pytest.fixture
def slot_empty(sub_deck):
    return sub_deck.slots['slot_01']

def test_slot(slot_empty):
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
    assert '[Vacant]' in str(slot_empty)
    assert '<- Vacant' in repr(slot_empty)
    
    slot_empty.loadLabwareFromConfigs(slot_empty.parent.slots['slot_04'].loaded_labware.details)
    assert isinstance(slot_empty.loaded_labware, Labware)

@pytest.fixture
def labware(slot_loaded):
    return slot_loaded.loaded_labware

def test_labware(labware:Labware):
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
    assert np.allclose(labware.fromTop((10,20,30)), (759.175,395.875,135.9))
    assert labware.listColumns() == [[f'{r}{i}' for r in 'ABCDEFGH'] for i in range(1,13)]
    assert labware.listRows() == [[f'{r}{i}' for i in range(1,13)] for r in 'ABCDEFGH']
    assert labware.listWells('col') == [labware.getWell(w) for w in labware.details['wells']]
    assert labware.listWells('row') == [labware.getWell(labware.details['ordering'][i][r]) for r in range(0,8) for i in range(0,12)]
    with pytest.raises(ValueError):
        labware.listWells('unknown')
    assert labware.parent.name in str(labware)
    assert labware.parent.name in repr(labware)
    assert (749.175,375.875,52.95) in labware.exclusion_zone
    assert (749.175,375.875,52.95) in labware.parent.exclusion_zone

def test_stackable_labware(slot_empty):
    slot_empty.loadLabwareFromFile('control-lab-le/tests/core/examples/labware_wellplate.json')
    stack = slot_empty.loaded_labware
    assert isinstance(stack, Labware)
    assert stack.is_stackable
    assert isinstance(stack.slot_above, Slot)
    slot_above = stack.slot_above
    assert slot_above.name == 'slot_01_a'
    assert isinstance(slot_empty.slot_above, Slot)
    assert slot_empty.slot_above == slot_above
    assert slot_above.slot_below == slot_empty
    
    slot_above.loadLabwareFromConfigs(stack.details)
    assert isinstance(slot_above.loaded_labware, Labware)
    with pytest.raises(AssertionError, match="Another Labware is stacked above"):
        slot_empty.removeLabware()
    slot_above.removeLabware()
    
    stack = slot_empty.removeLabware()
    assert slot_empty.loaded_labware is None
    assert slot_empty.slot_above is None
    stack.is_stackable = False
    assert stack.slot_above is None
    
    bad_details = stack.details
    bad_details.pop('slotAbove')
    with pytest.raises(AssertionError, match="No details for Slot above"):
        slot_empty.loadLabwareFromConfigs(bad_details)

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

def test_well_circular(well_circular):
    assert well_circular.name == 'A1'
    assert isinstance(well_circular.parent, Labware)
    assert well_circular.parent.name == 'Eppendorf Motion 96 Tip Rack 1000 uL' 
    assert well_circular.reference == Position([706.5,439.5,0], Rotation=Rotation.from_euler('zyx', [-90, 0, 0], degrees=True))
    assert np.allclose(well_circular.offset, (14.5,73.15,9))
    assert np.allclose(well_circular.center, (779.65,425.0,9))
    assert np.allclose(well_circular.bottom, (779.65,425.0,9))
    assert np.allclose(well_circular.middle, (779.65,425.0,57.45))
    assert np.allclose(well_circular.top, (779.65,425.0,105.9))
    assert well_circular.shape == 'circular'
    assert well_circular.depth == 96.9
    assert well_circular.volume == 0
    assert well_circular.capacity == 1000
    assert well_circular.dimensions == (6,)
    assert well_circular.base_area == np.pi * 3**2
    assert well_circular.level == 0
    well_circular.volume = 10
    assert well_circular.volume == 10
    assert well_circular.level == 10 / well_circular.base_area
    assert np.allclose(well_circular.fromBottom((10,20,30)), (789.65,445.0,39))
    assert np.allclose(well_circular.fromMiddle((10,20,30)), (789.65,445.0,87.45))
    assert np.allclose(well_circular.fromTop((10,20,30)), (789.65,445.0,135.9))

def test_well_rectangular(well_rectangular):
    assert np.allclose(well_rectangular.offset, (1,2,3))
    assert np.allclose(well_rectangular.center, (708.5,438.5,3))
    assert np.allclose(well_rectangular.bottom, (708.5,438.5,3))
    assert np.allclose(well_rectangular.middle, (708.5,438.5,5))
    assert np.allclose(well_rectangular.top, (708.5,438.5,7))
    assert len(well_rectangular.details) == 8
    assert well_rectangular.shape == 'rectangular'
    assert well_rectangular.volume == 0
    assert well_rectangular.capacity == 5
    assert well_rectangular.dimensions == (6,7)
    assert well_rectangular.base_area == 42
    assert well_rectangular.level == 0
    well_rectangular.volume = 10
    assert well_rectangular.volume == 10
    assert well_rectangular.level == 10 / well_rectangular.base_area
    assert str(well_rectangular.parent) in str(well_rectangular)
    assert repr(well_rectangular.parent) in repr(well_rectangular)
    fig, ax = plt.subplots()
    assert isinstance(well_rectangular._draw(ax), plt.Rectangle)

def test_well_unknown(labware, caplog):
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
    

def test_drawing_deck(main_deck):
    fig, ax = main_deck.show()
    assert isinstance(fig, plt.Figure)
    assert isinstance(ax, plt.Axes)

def test_drawing_labware(labware):
    fig, ax = labware.show()
    assert isinstance(fig, plt.Figure)
    assert isinstance(ax, plt.Axes)

def test_drawing_labware_stackable(labware):
    stack = labware.parent.parent.slots['slot_02'].loaded_labware
    stack.slot_above.loadLabwareFromConfigs(stack.details)
    fig, ax = stack.show()
    assert isinstance(fig, plt.Figure)
    assert isinstance(ax, plt.Axes)
