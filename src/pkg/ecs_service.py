from troposphere import Template, Ref, Tags, ImportValue, Join
from troposphere.ec2 import SecurityGroup, SecurityGroupRule
from troposphere.codebuild import (
    Project,
    Artifacts,
    EnvironmentVariable,
    Source,
    Environment,
)
from troposphere.codepipeline import (
    Pipeline,
    Stages,
    Actions,
    ActionTypeId,
    OutputArtifacts,
    InputArtifacts,
    ArtifactStore,
)
from troposphere.ecr import Repository
from troposphere.ecs import (
    Cluster,
    Service,
    TaskDefinition,
    ContainerDefinition,
    NetworkConfiguration,
    AwsvpcConfiguration,
    PortMapping,
    LoadBalancer,
    LogConfiguration,
)
import troposphere.elasticloadbalancingv2 as elb


def generate_template(d):

    # Set template metadata
    t = Template()
    t.add_version("2010-09-09")
    t.set_description(d["cf_template_description"])

    aws_account_id = Ref("AWS::AccountId")
    aws_region = Ref("AWS::Region")

    # Task definition
    task_definition = t.add_resource(
        TaskDefinition(
            "TaskDefinition",
            Family=Join("", [d["env"], "-", d["project_name"], "-", d["service_name"]]),
            RequiresCompatibilities=["FARGATE"],
            Cpu=d["container_cpu"],
            Memory=d["container_memory"],
            NetworkMode="awsvpc",
            ExecutionRoleArn=ImportValue(d["ecs_stack_name"] + "-ECSClusterRole"),
            ContainerDefinitions=[
                ContainerDefinition(
                    Name=Join(
                        "", [d["env"], "-", d["project_name"], "-", d["service_name"]]
                    ),
                    Image=Join(
                        "",
                        [
                            aws_account_id,
                            ".dkr.ecr.",
                            aws_region,
                            ".amazonaws.com/",
                            d["env"],
                            d["project_name"],
                            d["service_name"], ":latest"
                        ],
                    ),
                    Essential=True,
                    PortMappings=[
                        PortMapping(
                            ContainerPort=d["container_port"],
                            HostPort=d["container_port"],
                        )
                    ],
                    EntryPoint=["sh", "-c"],
                    Command=[d["container_command"]],
                    LogConfiguration=LogConfiguration(
                        LogDriver="awslogs",
                        Options={
                            "awslogs-region": aws_region,
                            "awslogs-group": Join("", [d["env"], "-", d["project_name"], "-", d["service_name"]]),
                            "awslogs-stream-prefix": "ecs",
                            "awslogs-create-group": "true"
                        }
                    )
                )
            ],
            Tags=Tags(d["tags"], {"Name": d["project_name"] + "-task-definition"}),
        )
    )

    # ECR
    ecr = t.add_resource(
        Repository(
            "ECR",
            DependsOn="ListenerRule",
            RepositoryName=Join(
                "", [d["env"], "-", d["project_name"], "-", d["service_name"]]
            ),
            Tags=Tags(d["tags"], {"Name": d["project_name"] + "-ecr"}),
        )
    )
    # Target group
    target_group = t.add_resource(
        elb.TargetGroup(
            "TargetGroup",
            Name=Join("", [d["env"], "-", d["service_name"]]),
            HealthCheckIntervalSeconds="30",
            HealthCheckProtocol="HTTP",
            HealthCheckPort=d["container_port"],
            HealthCheckTimeoutSeconds="10",
            HealthyThresholdCount="4",
            HealthCheckPath=d["tg_health_check_path"],
            Matcher=elb.Matcher(HttpCode="200-299"),
            Port=d["container_port"],
            Protocol="HTTP",
            TargetType="ip",
            UnhealthyThresholdCount="3",
            VpcId=ImportValue(d["network_stack_name"] + "-VPCId"),
            Tags=Tags(d["tags"], {"Name": d["project_name"] + "-ecr"}),
        )
    )
    # Listener rule
    t.add_resource(
        elb.ListenerRule(
            "ListenerRule",
            DependsOn="TargetGroup",
            ListenerArn=ImportValue(d["ecs_stack_name"] + "-ListenerArnHTTP"),
            Conditions=[
                elb.Condition(Field="path-pattern", Values=[d["application_path_api"]])
            ],
            Actions=[elb.Action(Type="forward", TargetGroupArn=Ref(target_group))],
            Priority="1",
        )
    )
    # ECS service
    ecs_service = t.add_resource(
        Service(
            "ECSService",
            ServiceName=Join(
                "", [d["env"], "-", d["project_name"], "-", d["service_name"]]
            ),
            DependsOn="pipeline",
            DesiredCount=d["container_desired_tasks_count"],
            TaskDefinition=Ref(task_definition),
            LaunchType="FARGATE",
            NetworkConfiguration=NetworkConfiguration(
                AwsvpcConfiguration=AwsvpcConfiguration(
                    Subnets=[
                        ImportValue(d["network_stack_name"] + "-PrivateSubnetId1"),
                        ImportValue(d["network_stack_name"] + "-PrivateSubnetId2"),
                    ],
                    SecurityGroups=[ImportValue(d["ecs_stack_name"] + "-ECSClusterSG")],
                )
            ),
            LoadBalancers=(
                [
                    LoadBalancer(
                        ContainerName=Join(
                            "",
                            [d["env"], "-", d["project_name"], "-", d["service_name"]],
                        ),
                        ContainerPort=d["container_port"],
                        TargetGroupArn=Ref(target_group),
                    )
                ]
            ),
            Cluster=ImportValue(d["ecs_stack_name"] + "-ECSClusterName"),
            Tags=Tags(d["tags"], {"Name": d["project_name"] + "-ecs-service"}),
        )
    )
    # App Autoscaling target

    # App Autoscaling policy

    # Codebuild project
    codebuild = t.add_resource(
        Project(
            "codebuild",
            Name=Join("", [d["env"], "-", d["project_name"], "-", d["service_name"]]),
            DependsOn="ECR",
            ServiceRole=ImportValue(d["ecs_stack_name"] + "-CodebuildDeveloperRole"),
            Artifacts=Artifacts(Name="Build", Location=d["artifact_store"], Type="S3",),
            Description="Build a docker image and send it to ecr",
            Source=Source(
                BuildSpec="buildspec.yml",
                Type="S3",
                Location=d["artifact_store"] + "/" + d["artifact_name"],
            ),
            Environment=Environment(
                ComputeType="BUILD_GENERAL1_SMALL",
                Image="aws/codebuild/standard:4.0",
                PrivilegedMode=True,
                Type="LINUX_CONTAINER",
                EnvironmentVariables=[
                    EnvironmentVariable(
                        Name="AWS_DEFAULT_REGION", Type="PLAINTEXT", Value=aws_region,
                    ),
                    EnvironmentVariable(
                        Name="SERVICE_NAME",
                        Type="PLAINTEXT",
                        Value=Join(
                            "",
                            [d["env"], "-", d["project_name"], "-", d["service_name"]],
                        ),
                    ),
                    EnvironmentVariable(
                        Name="IMAGE_URI",
                        Type="PLAINTEXT",
                        Value=Join(
                            "",
                            [
                                aws_account_id,
                                ".dkr.ecr.",
                                aws_region,
                                ".amazonaws.com/",
                                d["env"],
                                "-",
                                d["project_name"],
                                "-",
                                d["service_name"],
                            ],
                        ),
                    ),
                ],
            ),
            Tags=Tags(d["tags"], {"Name": d["project_name"] + "-codebuild"}),
        )
    )

    # Codepipeline
    pipeline = t.add_resource(
        Pipeline(
            "pipeline",
            Name=Join("", [d["env"], "-", d["project_name"], "-", d["service_name"]]),
            RoleArn=ImportValue(d["ecs_stack_name"] + "-CodePipelineRole"),
            Stages=[
                Stages(
                    Name="Source",
                    Actions=[
                        Actions(
                            Name="Source",
                            ActionTypeId=ActionTypeId(
                                Category="Source",
                                Owner="AWS",
                                Version="1",
                                Provider="S3",
                            ),
                            OutputArtifacts=[OutputArtifacts(Name="source_artifact")],
                            Configuration={
                                "S3Bucket": d["artifact_store"],
                                "S3ObjectKey": d["artifact_name"],
                            },
                            RunOrder="1",
                        )
                    ],
                ),
                Stages(
                    Name="Build",
                    Actions=[
                        Actions(
                            Name="Build",
                            InputArtifacts=[InputArtifacts(Name="source_artifact")],
                            OutputArtifacts=[OutputArtifacts(Name="build_artifact")],
                            ActionTypeId=ActionTypeId(
                                Category="Build",
                                Owner="AWS",
                                Version="1",
                                Provider="CodeBuild",
                            ),
                            Configuration={"ProjectName": Ref(codebuild)},
                            RunOrder="1",
                        )
                    ],
                ),
                Stages(
                    Name="Deploy",
                    Actions=[
                        Actions(
                            Name="Deploy",
                            InputArtifacts=[InputArtifacts(Name="build_artifact")],
                            ActionTypeId=ActionTypeId(
                                Category="Deploy",
                                Owner="AWS",
                                Version="1",
                                Provider="ECS",
                            ),
                            Configuration={
                                "ClusterName": ImportValue(
                                    d["ecs_stack_name"] + "-ECSClusterName"
                                ),
                                "ServiceName": Join(
                                    "",
                                    [
                                        d["env"],
                                        "-",
                                        d["project_name"],
                                        "-",
                                        d["service_name"],
                                    ],
                                ),
                                "FileName": "definitions.json",
                            },
                        )
                    ],
                ),
            ],
            ArtifactStore=ArtifactStore(Type="S3", Location=d["artifact_store"]),
        )
    )
    # Route53

    # Outputs

    return t
