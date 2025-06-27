import pytest
import time
from controllably.Move.Jointed.Dobot import M1Pro
from controllably.core.connection import match_current_ip_address
from controllably.core.position import convert_to_position

HOST = '192.109.209.21'

pytestmark = pytest.mark.skipif((not match_current_ip_address(HOST)), reason="Requires connection to local lab network")

@pytest.fixture(scope="session")
def m1pro():
    mp = M1Pro(**{
        'host': HOST,
        'home_position': [[300,0,240],[-33,0,0]],
        'calibrated_offset': [[-374,496.75,254.2],[-89.11611149,0,0]],
        'scale': 1.0,
        'tool_offset': [[0,0,-232],[122.11611149,0,0]],
        'safe_height': 240,
        'verbose': True,
        'simulation': True,
    })
    return mp

def test_move(m1pro):
    """Test M1Pro movement commands"""
    # Move to home position
    m1pro.home()
    assert m1pro.robot_position == convert_to_position([[300,0,240],[-33,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,262.2],[0,0,0]])
    
    # Move by a specific axis 
    m1pro.move('z',-10)
    assert m1pro.robot_position == convert_to_position([[300,0,230],[-33,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,252.2],[0,0,0]])
    m1pro.home()
    
    # Move by a specific offset
    m1pro.moveBy((10,10,-10))
    assert m1pro.robot_position == convert_to_position([[290.155457,10.153072,230],[-33,0,0]])
    assert m1pro.position == convert_to_position([[505.54935678,91.65413059,252.2],[0,0,0]])
    m1pro.home()
    
    # Move at a safe height
    m1pro.safeMoveTo((700,100,240))
    assert m1pro.robot_position == convert_to_position([[284.810211,204.70932,217.800003],[-33,0,0]])
    assert m1pro.position == convert_to_position([[699.99999792,99.99999497,240.000003],[0,0,0]])
    
    # Move to a safe height
    m1pro.moveToSafeHeight()
    assert m1pro.robot_position == convert_to_position([[284.810211,204.70932,240],[-33,0,0]])
    assert m1pro.position == convert_to_position([[699.99999792,99.99999497,262.2],[0,0,0]])
    
    # Move to a specific position
    m1pro.moveTo((750,120,220))
    assert m1pro.robot_position == convert_to_position([[265.583893,255.011902,197.800003],[-33,0,0]])
    assert m1pro.position == convert_to_position([[750.00000628,120.00000055,220.000003],[0,0,0]])
    m1pro.home()
    
    # Move to a specific position in robot coordinates
    m1pro.moveTo((300, 0, 230), robot=True)
    assert m1pro.robot_position == convert_to_position([[300,0,230],[-33,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,252.2],[0,0,0]])
    m1pro.home()

def test_move_at_speed(m1pro):
    """Test M1Pro movement commands"""
    # Move to home position
    m1pro.home()
    assert m1pro.robot_position == convert_to_position([[300,0,240],[-33,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,262.2],[0,0,0]])
    
    # Move by a specific axis 
    m1pro.move('z',-10, speed_factor=0.1)
    assert m1pro.robot_position == convert_to_position([[300,0,230],[-33,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,252.2],[0,0,0]])
    m1pro.home()
    
    # Move by a specific offset
    m1pro.moveBy((10,10,-10), speed_factor=0.3)
    assert m1pro.robot_position == convert_to_position([[290.155457,10.153072,230],[-33,0,0]])
    assert m1pro.position == convert_to_position([[505.54935678,91.65413059,252.2],[0,0,0]])
    m1pro.home()
    
    # Move at a safe height
    m1pro.safeMoveTo((700,100,240),speed_factor_lateral=0.7,speed_factor_up=0.9, speed_factor_down=0.5)
    assert m1pro.robot_position == convert_to_position([[284.810211,204.70932,217.800003],[-33,0,0]])
    assert m1pro.position == convert_to_position([[699.99999792,99.99999497,240.000003],[0,0,0]])
    
    # Move to a safe height
    m1pro.moveToSafeHeight(speed_factor=0.3)
    assert m1pro.robot_position == convert_to_position([[284.810211,204.70932,240],[-33,0,0]])
    assert m1pro.position == convert_to_position([[699.99999792,99.99999497,262.2],[0,0,0]])
    
    # Move to a specific position
    m1pro.moveTo((750,120,220), speed_factor=0.1)
    assert m1pro.robot_position == convert_to_position([[265.583893,255.011902,197.800003],[-33,0,0]])
    assert m1pro.position == convert_to_position([[750.00000628,120.00000055,220.000003],[0,0,0]])
    m1pro.home()
    
    # Move to a specific position in robot coordinates
    m1pro.moveTo((300, 0, 230), robot=True)
    assert m1pro.robot_position == convert_to_position([[300,0,230],[-33,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,252.2],[0,0,0]])
    m1pro.home()

def test_rotate(m1pro):
    m1pro.home()
    assert m1pro.robot_position == convert_to_position([[300,0,240],[-33,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,262.2],[0,0,0]])
    
    # Rotate by a specific axis 
    m1pro.rotate('c',-90)
    assert m1pro.robot_position == convert_to_position([[300,0,240],[-123,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,262.2],[-90,0,0]])
    
    # Rotate by a specific offset
    m1pro.rotateBy((45,0,0))
    assert m1pro.robot_position == convert_to_position([[300,0,240],[-78,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,262.2],[-45,0,0]])
    # m1pro.home()
    
    # Rotate to a specific position
    m1pro.rotateTo((45,0,0))
    time.sleep(1)
    assert m1pro.robot_position == convert_to_position([[300,0,240],[12,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,262.2],[45,0,0]])
    m1pro.home()
    
    # Move to a specific position in robot coordinates
    m1pro.rotateTo((45,0,0), robot=True)
    time.sleep(1)
    assert m1pro.robot_position == convert_to_position([[300,0,240],[45,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,262.2],[78,0,0]])
    m1pro.home()

def test_rotate_at_speed(m1pro):
    m1pro.home()
    assert m1pro.robot_position == convert_to_position([[300,0,240],[-33,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,262.2],[0,0,0]])
    
    # Rotate by a specific axis 
    m1pro.rotate('c',-90, speed_factor=0.5)
    assert m1pro.robot_position == convert_to_position([[300,0,240],[-123,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,262.2],[-90,0,0]])
    
    # Rotate by a specific offset
    m1pro.rotateBy((45,0,0), speed_factor=0.7)
    assert m1pro.robot_position == convert_to_position([[300,0,240],[-78,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,262.2],[-45,0,0]])
    # m1pro.home()
    
    # Rotate to a specific position
    m1pro.rotateTo((45,0,0), speed_factor=0.9)
    time.sleep(1)
    assert m1pro.robot_position == convert_to_position([[300,0,240],[12,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,262.2],[45,0,0]])
    m1pro.home()
    
    # Move to a specific position in robot coordinates
    m1pro.rotateTo((45,0,0), robot=True)
    time.sleep(1)
    assert m1pro.robot_position == convert_to_position([[300,0,240],[45,0,0]])
    assert m1pro.position == convert_to_position([[495.54935632,81.65413615,262.2],[78,0,0]])
    m1pro.home()
    
def test_reset(m1pro):
    m1pro.reset()