# %% [markdown]
# # Tutorial: Logging with controllably
#
# This tutorial demonstrates how to set up and use logging features in the `controllably` package.

# %%
from datetime import datetime

from controllably.core.logging import (
    get_git_info, get_package_info, log_version_info, start_logging
)

# %% [markdown]
# ## Setting Up Logging
# To start logging, we need to specify a directory and a log file name. The log file name can include a timestamp for uniqueness.
# A logging configuration file or dictionary can also be provided, but here we will use the default settings.

# %%
log_file = f'example_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log'
start_logging(log_dir='output/logs', log_file=log_file)

# %% [markdown]
# Get the current Git information and package version details.

# %%
get_git_info()

# %%
get_package_info('control-lab-ly')

# %% [markdown]
# Log information about the git and package versions.

# %%
log_version_info()

# %%
