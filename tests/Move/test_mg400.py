import pytest
import time
from controllably.Move.Jointed.Dobot import MG400
from controllably.core.connection import match_current_ip_address
from controllably.core.position import convert_to_position

HOST = '192.109.209.8'

pytestmark = pytest.mark.skipif((not match_current_ip_address(HOST)), reason="Requires connection to local lab network")

@pytest.fixture(scope="session")
def mg400():
    mg = MG400(**{
        'host': HOST,
        'home_position': [[300,0,75],[0,0,0]],
        'calibrated_offset': [[0,0,0],[0,0,0]],
        'scale': 1.0,
        'tool_offset': [[0,0,0],[0,0,0]],
        'safe_height': 75,
        'verbose': True,
        'simulation': True,
    })
    return mg

def test_move(mg400):
    """Test M1Pro movement commands"""
    # Move to home position
    mg400.home()
    assert mg400.position == convert_to_position([[300,0,75],[0,0,0]])
    
    # Move by a specific axis 
    mg400.move('z',-10)
    assert mg400.position == convert_to_position([[300,0,65],[0,0,0]])
    mg400.home()
    
    # Move by a specific offset
    mg400.moveBy((10,10,-10))
    assert mg400.position == convert_to_position([[310,10,65],[0,0,0]])
    mg400.home()
    
    # Move at a safe height
    mg400.safeMoveTo((290,-10,55))
    assert mg400.position == convert_to_position([[290,-10,55],[0,0,0]])
    
    # Move to a safe height
    mg400.moveToSafeHeight()
    assert mg400.position == convert_to_position([[290,-10,75],[0,0,0]])
    
    # Move to a specific position
    mg400.moveTo((310,10,65))
    assert mg400.position == convert_to_position([[310,10,65],[0,0,0]])
    mg400.home()
    
    # Move to a specific position in robot coordinates
    mg400.moveTo((300,0,75), robot=True)
    assert mg400.position == convert_to_position([[300,0,75],[0,0,0]])
    mg400.home()

def test_move_at_speed(mg400):
    """Test M1Pro movement commands"""
    # Move to home position
    mg400.home()
    assert mg400.position == convert_to_position([[300,0,75],[0,0,0]])
    
    # Move by a specific axis 
    mg400.move('z',-10, speed_factor=0.1)
    assert mg400.position == convert_to_position([[300,0,65],[0,0,0]])
    mg400.home()
    
    # Move by a specific offset
    mg400.moveBy((10,10,-10), speed_factor=0.3)
    assert mg400.position == convert_to_position([[310,10,65],[0,0,0]])
    mg400.home()
    
    # Move at a safe height
    mg400.safeMoveTo((290,-10,55),speed_factor_lateral=0.7,speed_factor_up=0.9, speed_factor_down=0.5)
    assert mg400.position == convert_to_position([[290,-10,55],[0,0,0]])
    
    # Move to a safe height
    mg400.moveToSafeHeight(speed_factor=0.3)
    assert mg400.position == convert_to_position([[290,-10,75],[0,0,0]])
    
    # Move to a specific position
    mg400.moveTo((310,10,65), speed_factor=0.1)
    assert mg400.position == convert_to_position([[310,10,65],[0,0,0]])
    mg400.home()
    
    # Move to a specific position in robot coordinates
    mg400.moveTo((300,0,75), robot=True)
    assert mg400.position == convert_to_position([[300,0,75],[0,0,0]])
    mg400.home()

def test_rotate(mg400):
    mg400.home()
    assert mg400.position == convert_to_position([[300,0,75],[0,0,0]])
    
    # Rotate by a specific axis 
    mg400.rotate('c',-90)
    assert mg400.position == convert_to_position([[300,0,75],[-90,0,0]])
    
    # Rotate by a specific offset
    mg400.rotateBy((45,0,0))
    assert mg400.position == convert_to_position([[300,0,75],[-45,0,0]])
    # mg400.home()
    
    # Rotate to a specific position
    mg400.rotateTo((45,0,0))
    time.sleep(1)
    assert mg400.position == convert_to_position([[300,0,75],[45,0,0]])
    mg400.home()
    
    # Move to a specific position in robot coordinates
    mg400.rotateTo((45,0,0), robot=True)
    time.sleep(1)
    assert mg400.position == convert_to_position([[300,0,75],[45,0,0]])
    mg400.home()

def test_rotate_at_speed(mg400):
    mg400.home()
    assert mg400.position == convert_to_position([[300,0,75],[0,0,0]])
    
    # Rotate by a specific axis 
    mg400.rotate('c',-90, speed_factor=0.5)
    assert mg400.position == convert_to_position([[300,0,75],[-90,0,0]])
    
    # Rotate by a specific offset
    mg400.rotateBy((45,0,0), speed_factor=0.7)
    assert mg400.position == convert_to_position([[300,0,75],[-45,0,0]])
    # mg400.home()
    
    # Rotate to a specific position
    mg400.rotateTo((45,0,0), speed_factor=0.9)
    time.sleep(1)
    assert mg400.position == convert_to_position([[300,0,75],[45,0,0]])
    mg400.home()
    
    # Move to a specific position in robot coordinates
    mg400.rotateTo((45,0,0), robot=True)
    time.sleep(1)
    assert mg400.position == convert_to_position([[300,0,75],[45,0,0]])
    mg400.home()
    
def test_reset(mg400):
    mg400.reset()