from controllably import load_setup         # pip install control-lab-ly

HERE = '/'.join(__file__.split('\\')[:-1])
CONFIGS = '/'.join(HERE.split('/')[:-1])

CONFIG_FILE = f"{HERE}/config.yaml"
LAYOUT_FILE = f"{HERE}/layout.json"
REGISTRY_FILE = f"{CONFIGS}/registry.yaml"

SETUP = load_setup(config_file=CONFIG_FILE, registry_file=REGISTRY_FILE)
"""NOTE: importing SETUP gives the same instance wherever you import it"""