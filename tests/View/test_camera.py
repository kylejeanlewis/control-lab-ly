import pytest
import time
import cv2
from controllably.View import Camera
from controllably.core import init

cap = cv2.VideoCapture(0)
is_opened = cap.isOpened()
cap.release()
pytestmark = pytest.mark.skipif((not is_opened), reason="Requires connection to camera")

@pytest.fixture(scope="session")
def camera():
    cam = Camera(**{
        'connection_details': {
            'feed_source': 0,
            'feed_api': None
        }
    })
    cam.connect()
    return cam

def test_camera(camera):
    camera.connect()
    assert camera.is_connected
    camera.disconnect()
    assert not camera.is_connected
    
def test_get_frame(camera):
    camera.connect()
    assert camera.is_connected
    ret, frame = camera.getFrame(True)
    assert ret
    assert ret == (frame is not None)
    assert camera.frame_size == frame.shape[-2::-1]
    camera.clear()
    camera.disconnect()
    assert not camera.is_connected

def test_stream(camera):
    camera.connect()
    assert camera.is_connected
    assert len(camera.buffer) == 0
    camera.startStream()
    time.sleep(2)
    assert camera.stream_event.is_set()
    camera.stopStream()
    assert len(camera.buffer) > 0
    assert not camera.stream_event.is_set()
    camera.clear()
    camera.disconnect()
    assert not camera.is_connected

def test_save_frame(camera, tmp_path):
    camera.connect()
    assert camera.is_connected
    ret, frame = camera.getFrame(True)
    assert ret
    camera.saveFrame(frame, tmp_path / "test_frame.jpg")
    assert (tmp_path / "test_frame.jpg").exists()
    saved_frame = camera.loadImageFile(tmp_path / "test_frame.jpg")
    assert saved_frame is not None
    assert saved_frame.shape == frame.shape
    camera.clear()
    camera.disconnect()
    assert not camera.is_connected

def test_save_frames_to_video(camera, tmp_path):
    camera.connect()
    assert camera.is_connected
    filepath = tmp_path / "test_video.mp4"
    camera.startStream()
    assert camera.stream_event.is_set()
    time.sleep(2)
    camera.stopStream()
    assert not camera.stream_event.is_set()
    frames = [im for im,_ in camera.buffer]
    camera.saveFramesToVideo(frames, camera.frame_rate, filepath)
    assert filepath.exists()
    camera.clear()
    camera.disconnect()
    assert not camera.is_connected
