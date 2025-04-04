import pytest
from datetime import datetime
import json
import os
from pathlib import Path
import sys

import yaml # pip install pyyaml

from controllably.core.file_handler import (
    create_folder, init, read_config_file, readable_duration,
    resolve_repo_filepath, start_logging, start_project_here, zip_files, TEMP_ZIP
)
    
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

def test_read_config_file_json(tmp_path):
    config = {"key": "value"}
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f)
    result = read_config_file(config_file)
    assert result == config

def test_read_config_file_yaml(tmp_path):
    config = {"key": "value"}
    config_file = tmp_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    result = read_config_file(config_file)
    assert result == config

def test_read_config_file_unknown_ext(tmp_path):
    config = {"key": "value"}
    txt_file = tmp_path / "file1.txt"
    txt_file.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='Unsupported file type: txt'):
        _ = read_config_file(txt_file)

def test_readable_duration():
    duration = 3661  # 1 hour, 1 minute, 1 second
    result = readable_duration(duration)
    assert result == "1h 01min 01sec"

def test_resolve_repo_filepath_relative():
    repo_name = "control-lab-le"
    relative_path = f"{repo_name}/some/file/path"
    root = os.getcwd().split(repo_name)[0]
    absolute_path = resolve_repo_filepath(relative_path)
    assert absolute_path.is_absolute()
    assert absolute_path == Path(f"{root}/{relative_path}")
    
def test_resolve_repo_filepath_absolute():
    relative_path = "control-lab-le/some/file/path"
    cwd = Path().absolute()
    absolute_path = resolve_repo_filepath(cwd / relative_path)
    assert absolute_path.is_absolute()
    assert absolute_path == cwd / relative_path
    
def test_resolve_repo_filepath_empty():
    relative_path = "."
    absolute_path = resolve_repo_filepath(relative_path)
    assert absolute_path.is_absolute()
    assert absolute_path == Path().absolute()

def test_start_logging(tmp_path):
    log_dir = tmp_path / "logs"
    log_file = "test.log"
    log_path = start_logging(log_dir, log_file)
    assert log_path.exists()
    assert log_path.is_file()
    assert log_path == log_dir / log_file

def test_start_logging_with_config(tmp_path):
    log_dir = tmp_path / "logs"
    log_file = "test.log"
    log_path = start_logging(log_dir, log_file, logging_config={"log_level": "DEBUG"})
    assert log_path is None

def test_start_project_here(tmp_path, monkeypatch, caplog):
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
