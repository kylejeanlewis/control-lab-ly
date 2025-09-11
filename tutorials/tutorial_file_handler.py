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

# %%
read_config_file('library/configs/email_config.yaml')

# %%
read_config_file('library/layouts/layout.json')

# %%
readable_duration(3661)

# %%
resolve_repo_filepath('control-lab-ly/tutorials/library/layouts/layout.json')

# %%
zip_files([
    Path('library/configs/email_config.yaml'), 
    Path('library/layouts/layout.json')
], 'output/example.zip')

# %%
start_project_here('output/example_project')

# %%
create_folder('output', 'subfolder')

# %%
init('control-lab-ly')

# %%
from tutorials.output.example_project.library import plugins

# %%
