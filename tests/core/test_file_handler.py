import pytest
from datetime import datetime
import json
import os
from pathlib import Path
import sys

import yaml # pip install pyyaml

from ..context import controllably
from controllably.core.file_handler import (
    create_folder, init, read_config_file, readable_duration,
    resolve_repo_filepath, start_logging, start_project_here, zip_files, TEMP_ZIP)


def test_create_folder(tmp_path):
    base = Path(tmp_path / "base")
    sub = "sub"
    folder = create_folder(base, sub)
    assert folder == (base / datetime.now().strftime("%Y%m%d_%H%M") / sub)
    assert folder.exists()
    assert folder.is_dir()

def test_init(monkeypatch):
    repository_name = "control-lab-le"
    monkeypatch.setattr('sys.path', [])
    target_dir = init(repository_name)
    assert repository_name in target_dir
    assert target_dir in sys.path
    
def test_init_unknown_repo(monkeypatch):
    repository_name = "unknown"
    monkeypatch.setattr('sys.path', [])
    with pytest.raises(AssertionError, match=f"'unknown' not found"):
        _ = init(repository_name)

@pytest.mark.parametrize("file_type", ["json", "yaml", "txt"])
def test_read_config_file(file_type, tmp_path):
    config = {"key": "value"}
    config_file = tmp_path / f"config.{file_type}"
    with open(config_file, 'w') as f:
        if file_type == "json":
            json.dump(config, f)
        elif file_type == "yaml":
            yaml.dump(config, f)
        else:
            f.write(json.dumps(config))
    
    if file_type == "txt":
        with pytest.raises(ValueError, match='Unsupported file type: txt'):
            _ = read_config_file(config_file)
    else:
        result = read_config_file(config_file)
        assert result == config

def test_readable_duration():
    duration = 3661  # 1 hour, 1 minute, 1 second
    result = readable_duration(duration)
    assert result == "1h 01min 01sec"

@pytest.mark.parametrize("path", [
    Path().absolute() / "control-lab-le/some/file/path",
    "control-lab-le/some/file/path",
    "."
])
def test_resolve_repo_filepath(path):
    repo_name = "control-lab-le"
    root = os.getcwd().split(repo_name)[0]
    absolute_path = resolve_repo_filepath(path)
    assert absolute_path.is_absolute()
    path = Path(path)
    if path.is_absolute():
        assert absolute_path == path
    elif repo_name in path.parts:
        assert absolute_path == Path(f"{root}/{path}")
    else:
        assert absolute_path == Path().absolute()
    
@pytest.mark.parametrize("logging_config", [
    None,
    {"log_level": "DEBUG"},
])
def test_start_logging(logging_config, tmp_path):
    log_dir = tmp_path / "logs"
    log_file = "test.log"
    log_path = start_logging(log_dir, log_file, logging_config)
    if logging_config is None:
        assert isinstance(log_path, Path)
        assert log_path.exists()
        assert log_path.is_file()
        assert log_path == log_dir / log_file
    else:
        assert log_path is None

def test_start_project_here(caplog, monkeypatch, tmp_path):
    src = os.getcwd().split('control-lab-le')[0] + "control-lab-le/controllably"
    monkeypatch.setattr('importlib.resources.files', lambda _: Path(src))
    dst = tmp_path / "project"
    registry = dst / "tools/registry.yaml"
    start_project_here(dst)
    assert dst.exists()
    assert dst.is_dir()
    assert registry.exists()
    assert registry.is_file()
    assert f"New project created in: {dst}" in caplog.text
    start_project_here(dst)
    assert "Folder/file already exists" in caplog.text

def test_zip_files(tmp_path):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("content1")
    file2.write_text("content2")
    zip_path = zip_files([file1, file2], zip_filepath=tmp_path/TEMP_ZIP)
    assert zip_path.exists()
    assert zip_path.is_file()
