# %% [markdown]
# # Email Notification Example
#
# This example demonstrates how to use the `EmailNotifier` class from the `controllably` 
# library to send email notifications with attachments.

# %%
from datetime import datetime
from pathlib import Path

from controllably.core.file_handler import read_config_file
from controllably.core.notification import EmailNotifier

# %% [markdown]
# ## Configuration
# Refer to the configuration files in `library/configs/email_config.yaml`
# for examples of how to set up the email notifier.

# %%
email_config_file = Path('library/configs/email_config.yaml')
email_config_file_no_key = Path('library/configs/email_config_no_key.yaml')
filepaths_to_attach = [email_config_file, email_config_file_no_key]

# %%
read_config_file(email_config_file)

# %% [markdown]
# Use the `EmailNotifier` class to send an email with attachments, 
# with a context manager to ensure proper resource management.

# %%
with EmailNotifier.fromFile(email_config_file) as emailer:
    attachment_paths = filepaths_to_attach
    text_fields = dict(
        experiment = "Test Experiment",
        timestamp = datetime.now()
    )
    print(f'{emailer._app_password=}')
    
    try:
        emailer.notify(placeholders=text_fields, attachments=attachment_paths)
    except Exception as e:
        print("\nNotification failed. Check your email configuration and internet connection.")
        print(e)

# %% [markdown]
# When no app password filepath is provided in the configuration file,
# the notifier will prompt for the password filepath at runtime.
# 
# *Input* `library/configs/.key` *when prompted.*

# %%
configs = read_config_file(email_config_file_no_key)
configs['credentials']

# %%
with EmailNotifier.fromFile(email_config_file_no_key) as emailer:
    attachment_paths = filepaths_to_attach
    text_fields = dict(
        experiment = "Test Experiment",
        timestamp = datetime.now()
    )
    print(f'{emailer._app_password=}')
    
    try:
        emailer.notify(placeholders=text_fields, attachments=attachment_paths)
    except Exception as e:
        print("\nNotification failed. Check your email configuration and internet connection.")
        print(e)

# %% [markdown]
# A different decoder can be set for decoding the app password file, using the `setDecoder()` method.
#
# The default decoder (`'base64'`) uses `base64.b64decode()`, then converts the bytes to string.
# 
# Here, we set a simple ASCII decoder that just converts from bytes to plain text for demonstration purposes.
# 
# *Input* `library/configs/plaintext.key` *when prompted.*

# %%
with EmailNotifier.fromFile(email_config_file_no_key) as emailer:
    attachment_paths = filepaths_to_attach
    text_fields = dict(
        experiment = "Test Experiment",
        timestamp = datetime.now()
    )
    print(f'{emailer._app_password=}')
    
    print(f'Initial decoder: {emailer.decoder}')
    emailer.setDecoder('insecure', lambda x:x.decode('ascii'))
    print(f'Selected decoder: {emailer.decoder}')
    
    try:
        emailer.notify(placeholders=text_fields, attachments=attachment_paths)
    except Exception as e:
        print("\nNotification failed. Check your email configuration and internet connection.")
        print(e)

# %%
