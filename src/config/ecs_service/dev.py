config = {
    # Container Definitions
    "container_cpu": "256",
    "container_memory": "512",
    "container_port": "8080",
    "container_command": "python /run.py",
    "container_desired_tasks_count": "1",
    "env": "dev",
    "tags": {"ProjectName": "demo-troposphere-ecs-service", "env": "dev"},
}
