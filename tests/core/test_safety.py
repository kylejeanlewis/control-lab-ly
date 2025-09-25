import pytest
import logging

from ..context import controllably
from controllably.core import safety
from controllably.core.safety import (
    get_safety_level, set_safety_level, reset_safety_level, guard, SafetyLevel
)


@pytest.mark.parametrize("mode", ["DEBUG", "DELAY", "SUPERVISED"])
def test_set_safety_level(mode):
    value = getattr(SafetyLevel, mode)
    set_safety_level(value)
    assert get_safety_level() == value

@pytest.mark.parametrize("mode", ["DEBUG", "DELAY", "SUPERVISED"])
def test_reset_safety_level(mode):
    value = getattr(SafetyLevel, mode)
    set_safety_level(value)
    assert get_safety_level() == value
    reset_safety_level()
    assert get_safety_level() is None

@pytest.mark.parametrize("mode", ["DEBUG", "DELAY", "SUPERVISED"])
def test_guard(mode, caplog, monkeypatch):
    value = getattr(SafetyLevel, mode)
    @guard(value)
    def dummy_function():
        return "Executed"
    
    str_method = repr(dummy_function).split(' ')[1]
    log_level = logging.DEBUG if mode == "DEBUG" else logging.WARNING
    if mode == "SUPERVISED":
        monkeypatch.setattr('builtins.input', lambda _: None)
    
    with caplog.at_level(log_level):
        result = dummy_function()
        assert result == "Executed"
        assert f"[{mode}] {str_method}()" in caplog.text
        if mode == "DELAY":
            assert f"Waiting for {value} seconds" in caplog.text
