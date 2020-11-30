from config.ecs_fargate.config import config
from pkg.ecs_fargate import generate_template


t = generate_template(config)

# print(config.config['public_subnet_cidr_blocks'][0])
# print(config.config['tags']['ProjectName'])
# print(config.config['tags'])

print(t.to_yaml())
