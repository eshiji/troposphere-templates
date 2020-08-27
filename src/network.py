from config.network.config import config
from pkg.network import generate_template as generate_network_template

t = generate_network_template(config)

# print(config.config['public_subnet_cidr_blocks'][0])
# print(config.config['tags']['ProjectName'])
# print(config.config['tags'])

print(t.to_yaml())
