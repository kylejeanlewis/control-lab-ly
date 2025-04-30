import pytest
import time
from controllably.Move.Cartesian import Gantry
from controllably.core.connection import get_ports
from controllably.core.position import convert_to_position

PORT = 'COM5'

pytestmark = pytest.mark.skipif((PORT not in get_ports()), reason="Requires serial connection to device")

@pytest.fixture(scope="session")
def gantry():
    gnt = Gantry(**{
        'port': PORT,
        'limits': [[0,-480,-195.5],[180,0,0]],
        'home_position': [[300,0,75],[0,0,0]],
        'calibrated_offset': [[-206, 468.75,197.7],[-90,0,0]],
        'scale': 1.0,
        'safe_height': -1,
        'verbose': True,
        'simulation': True,
    })
    return gnt

def test_move(gantry):
    """Test M1Pro movement commands"""
    # Move to home position
    gantry.home()
    assert gantry.robot_position == convert_to_position([[0,0,0],[0,0,0]])
    assert gantry.position == convert_to_position([[495.54935632,81.65413615,262.2],[0,0,0]])
    
    # Move by a specific axis 
    gantry.move('z',-10)
    assert gantry.robot_position == convert_to_position([[0,0,-10],[0,0,0]])
    assert gantry.position == convert_to_position([[495.54935632,81.65413615,252.2],[0,0,0]])
    gantry.home()
    
    # Move by a specific offset
    gantry.moveBy((10,10,-10))
    assert gantry.robot_position == convert_to_position([[10,10,-10],[0,0,0]])
    assert gantry.position == convert_to_position([[505.54935678,91.65413059,252.2],[0,0,0]])
    gantry.home()
    
    # Move at a safe height
    gantry.safeMoveTo((700,100,240))
    assert gantry.robot_position == convert_to_position([[284.810211,204.70932,217.800003],[0,0,0]])
    assert gantry.position == convert_to_position([[699.99999792,99.99999497,240.000003],[0,0,0]])
    
    # Move to a safe height
    gantry.moveToSafeHeight()
    assert gantry.robot_position == convert_to_position([[284.810211,204.70932,240],[0,0,0]])
    assert gantry.position == convert_to_position([[699.99999792,99.99999497,262.2],[0,0,0]])
    
    # Move to a specific position
    gantry.moveTo((750,120,220))
    assert gantry.robot_position == convert_to_position([[265.583893,255.011902,197.800003],[0,0,0]])
    assert gantry.position == convert_to_position([[750.00000628,120.00000055,220.000003],[0,0,0]])
    gantry.home()
    
    # Move to a specific position in robot coordinates
    gantry.moveTo((300, 0, 230), robot=True)
    assert gantry.robot_position == convert_to_position([[300,0,230],[0,0,0]])
    assert gantry.position == convert_to_position([[495.54935632,81.65413615,252.2],[0,0,0]])
    gantry.home()

def test_move_at_speed(gantry):
    """Test M1Pro movement commands"""
    # Move to home position
    gantry.home()
    assert gantry.robot_position == convert_to_position([[300,0,240],[0,0,0]])
    assert gantry.position == convert_to_position([[495.54935632,81.65413615,262.2],[0,0,0]])
    
    # Move by a specific axis 
    gantry.move('z',-10, speed_factor=0.1)
    assert gantry.robot_position == convert_to_position([[300,0,230],[0,0,0]])
    assert gantry.position == convert_to_position([[495.54935632,81.65413615,252.2],[0,0,0]])
    gantry.home()
    
    # Move by a specific offset
    gantry.moveBy((10,10,-10), speed_factor=0.3)
    assert gantry.robot_position == convert_to_position([[290.155457,10.153072,230],[0,0,0]])
    assert gantry.position == convert_to_position([[505.54935678,91.65413059,252.2],[0,0,0]])
    gantry.home()
    
    # Move at a safe height
    gantry.safeMoveTo((700,100,240),speed_factor_lateral=0.7,speed_factor_up=0.9, speed_factor_down=0.5)
    assert gantry.robot_position == convert_to_position([[284.810211,204.70932,217.800003],[0,0,0]])
    assert gantry.position == convert_to_position([[699.99999792,99.99999497,240.000003],[0,0,0]])
    
    # Move to a safe height
    gantry.moveToSafeHeight(speed_factor=0.3)
    assert gantry.robot_position == convert_to_position([[284.810211,204.70932,240],[0,0,0]])
    assert gantry.position == convert_to_position([[699.99999792,99.99999497,262.2],[0,0,0]])
    
    # Move to a specific position
    gantry.moveTo((750,120,220), speed_factor=0.1)
    assert gantry.robot_position == convert_to_position([[265.583893,255.011902,197.800003],[0,0,0]])
    assert gantry.position == convert_to_position([[750.00000628,120.00000055,220.000003],[0,0,0]])
    gantry.home()
    
    # Move to a specific position in robot coordinates
    gantry.moveTo((300, 0, 230), robot=True)
    assert gantry.robot_position == convert_to_position([[300,0,230],[0,0,0]])
    assert gantry.position == convert_to_position([[495.54935632,81.65413615,252.2],[0,0,0]])
    gantry.home()
  