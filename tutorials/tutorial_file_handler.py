# %% [markdown]
# # Tutorial: File Handler
# 
# This tutorial demonstrates the usage of file handling utilities from the `controllably` library.

# %%
from pathlib import Path

from controllably.core.file_handler import (
    create_folder, 
    init, 
    read_config_file,
    readable_duration, 
    resolve_repo_filepath, 
    start_project_here,
    zip_files
)

# %% [markdown]
# The `read_config_file` function reads configuration files in multiple formats (YAML, JSON) and returns their contents as a dictionary.

# %%
read_config_file('library/configs/email_config.yaml')

# %%
read_config_file('library/layouts/layout.json')

# %% [markdown]
# The `readable_duration` function converts a duration in seconds into a human-readable format.

# %%
readable_duration(3661)

# %% [markdown]
# The `resolve_repo_filepath` function resolves a file path relative to the repository root.

# %%
resolve_repo_filepath('control-lab-ly/tutorials/library/layouts/layout.json')

# %% [markdown]
# The `zip_files` function compresses multiple files into a single ZIP archive.

# %%
zip_files([
    Path('library/configs/email_config.yaml'), 
    Path('library/layouts/layout.json')
], 'output/example.zip')

# %% [markdown]
# The `start_project_here` function initializes a new project structure at the specified location.

# %%
start_project_here('output/example_project')

# %% [markdown]
# The `create_folder` function creates a new folder using the current datetime at the specified path, and a subfolder can be specified.

# %%
create_folder('output', 'subfolder')

# %% [markdown]
# The `init` function initializes the controllably environment for the specified repository, 
# by adding it to the system path and setting up necessary configurations.

# %%
init('control-lab-ly')

# %%
from tutorials.output.example_project.library import plugins

# %%
