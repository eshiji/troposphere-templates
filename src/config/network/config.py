from .default import config as default_config
from .dev import config as dev_config
from .prd import config as prd_config
from .env import config as envs


environment = envs["env"]
environment_config = None

if environment == 'development' or environment == 'dev':
    environment_config = dev_config
if environment == 'production' or environment == 'prd':
    environment_config = prod_config

# Merge dictionaries
config = {**default_config, **envs, **environment_config}
