import pytest
import logging

from controllably.core import safety
from controllably.core.safety import set_level, reset_level, guard, DEBUG, DELAY, SUPERVISED


@pytest.mark.parametrize("mode", [DEBUG, DELAY, SUPERVISED])
def test_set_level(mode):
    set_level(mode)
    assert safety.safety_mode == mode

def test_reset_level():
    set_level(DEBUG)
    assert safety.safety_mode == DEBUG
    reset_level()
    assert safety.safety_mode is None

def test_guard_debug_mode(caplog):
    @guard(DEBUG)
    def dummy_function():
        return "Executed"
    str_method = repr(dummy_function).split(' ')[1]
    with caplog.at_level(logging.DEBUG):
        result = dummy_function()
        assert result == "Executed"
        assert f"[DEBUG] {str_method}()" in caplog.text

def test_guard_delay_mode(caplog):
    @guard(DELAY)
    def dummy_function():
        return "Executed"
    str_method = repr(dummy_function).split(' ')[1]
    with caplog.at_level(logging.WARNING):
        result = dummy_function()
        assert result == "Executed"
        assert f"[DELAY] {str_method}()" in caplog.text
        assert f"Waiting for {DELAY} seconds" in caplog.text

def test_guard_supervised_mode(monkeypatch, caplog):
    @guard(SUPERVISED)
    def dummy_function():
        return "Executed"
    str_method = repr(dummy_function).split(' ')[1]
    monkeypatch.setattr('builtins.input', lambda _: None)
    with caplog.at_level(logging.WARNING):
        result = dummy_function()
        assert result == "Executed"
        assert f"[SUPERVISED] {str_method}()" in caplog.text
