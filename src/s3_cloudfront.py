from config.s3_cloudfront.config import config
from pkg.s3_cloudfront import generate_template

t = generate_template(config)

# print(config.config['public_subnet_cidr_blocks'][0])
# print(config.config['tags']['ProjectName'])
# print(config.config['tags'])

print(t.to_yaml())
