import pytest
import logging

from controllably.core import safety
from controllably.core.safety import set_level, reset_level, guard


@pytest.mark.parametrize("mode", ["DEBUG", "DELAY", "SUPERVISED"])
def test_set_level(mode):
    value = getattr(safety, mode)
    set_level(value)
    assert safety.safety_mode == value

@pytest.mark.parametrize("mode", ["DEBUG", "DELAY", "SUPERVISED"])
def test_reset_level(mode):
    value = getattr(safety, mode)
    set_level(value)
    assert safety.safety_mode == value
    reset_level()
    assert safety.safety_mode is None

@pytest.mark.parametrize("mode", ["DEBUG", "DELAY", "SUPERVISED"])
def test_guard(mode, caplog, monkeypatch):
    value = getattr(safety, mode)
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
