# troposphere-templates

Create dynamic cloudformation json or yml templates using predefined dictionary values for each environment (e.g. dev, stg, prod etc) and deploy in a new AWS account.
 
## Installation
```python
aws configure --profile profile_name
python -m virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
export PYTHON_ENV=dev
```

## Usage
```python
cd src/
python network.py
python ecs_fargate
python ecs_service
python s3_cloudfront.py
```

## Ansible
Create buckets to store templates and artifacts(MUST run):
``` 
ansible-playbook -vvv deploy.yml -e env=demo -t demo
```

Running everything together in a new AWS account:
``` 
ansible-playbook -vvv deploy.yml -e env=demo -t demo
```

Network:
```
ansible-playbook -vvv deploy.yml -e env=demo -t network
```

ECS Cluster:
```
ansible-playbook -vvv deploy.yml -e env=demo -t ecs_fargate
```

ECS service:
```
ansible-playbook -vvv deploy.yml -e env=demo -t ecs_service
```

S3 CLoudfront:
```
ansible-playbook -vvv deploy.yml -e env=demo -t s3_cloudfront
```


## ROADMAP
- Manifest and setup.py to create a package
- Adjusts to role policies permissions
- App Autoscaling target
- App Autoscaling policy
- Route53 resource for ALB rules (host-header)

## Template resources 
**Network**
- VPC
- 4 subnets (2 private and 2 public)
- Internet Gateway
- 2 Nat Gateways
- 2 Elastic IPs
- 3 Route tables (1 public and 2 private)
- Route for NAT GTW
- Route for IGW

**ECS Cluster (Fargate)**
- Application Load Balancer (ALB)
- Security Group for ALB
- Security Group for ECS services
- ALB Listener (HTTP)
- ECS service policy and role
- Codebuild policy and role
- Codepipeline policy and role

**ECS service**
- ECS task definition
- ECR
- Target Group
- ALB Listener rule
- ECS service
- Codebuild Project
- Codepipeline

**S3 Cloudfront**
- S3
- Cloudfront Distribution
- OAI (Origin Access Identity)
- S3 bucket policy