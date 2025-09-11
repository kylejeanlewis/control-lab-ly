# %%
from datetime import datetime

from controllably.core.logging import (
    get_git_info, get_package_info, log_version_info, start_logging
)

# %%
log_file = f'example_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log'
start_logging(log_dir='logs', log_file=log_file)

# %%
get_git_info()

# %%
get_package_info('control-lab-ly')

# %%
log_version_info()

# %%
