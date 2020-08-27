config = {
    'cf_template_description': 'This template is generated with python'
                               'using troposphere framework to create'
                               'dynamic Cloudfront templates with'
                               'different vars according to the'
                               'PYTHON_ENV environment variable for'
                               'ECS service.',
    'project_name': 'megazord-ecs-service',
    'service_name': 'devops-api',
    'network_stack_name': 'ansible-megazord-network',
    'ecs_stack_name': 'ansible-megazord-ecs-fargate',
    'tg_health_check_path': '/health',
    'application_path_api': '/*',
    'artifact_store': 'megazord-artifact-store',
    'artifact_name': 'dev-megazord-ecs-service.zip'
}
