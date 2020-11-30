config = {
    'vpc_cidr_block': '10.0.0.0/16',
    'public_subnet_cidr_blocks': ['10.0.0.0/24', '10.0.1.0/24'],
    'private_subnet_cidr_blocks': ['10.0.2.0/24', '10.0.3.0/24'],
    'availability_zones': ['us-east-1a', 'us-east-1b'],
    'tags': {
        'Name': 'demo-network1',
        'ProjectName': 'demo-troposphere-network',
        'env': 'dev'
    }
}