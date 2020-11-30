from troposphere import (
    Template,
    Ref,
    Tags,
    Output,
    ImportValue,
    Export,
    Sub,
    GetAtt,
    Join,
)
from troposphere.ec2 import SecurityGroup, SecurityGroupRule
from troposphere.iam import Role, PolicyType
from troposphere.ecs import Cluster
import troposphere.elasticloadbalancingv2 as elb


def generate_template(d):

    # Set template metadata
    t = Template()
    t.add_version("2010-09-09")
    t.set_description(d["cf_template_description"])

    # aws_account_id = Ref("AWS::AccountId")
    # aws_region = Ref("AWS::Region")

    # ALB SG
    ALBSG = t.add_resource(
        SecurityGroup(
            "ALBSG",
            GroupDescription="Enable HTTP access.",
            SecurityGroupIngress=[
                SecurityGroupRule(
                    IpProtocol="tcp", FromPort="80", ToPort="80", CidrIp="0.0.0.0/0"
                )
            ],
            VpcId=ImportValue(d["network_stack_name"] + "-VPCId"),
        )
    )

    # ALB
    ALB = t.add_resource(
        elb.LoadBalancer(
            "ALB",
            Name=d["project_name"],
            Scheme="internet-facing",
            SecurityGroups=[Ref("ALBSG")],
            Subnets=[
                ImportValue(d["network_stack_name"] + "-PublicSubnetId1"),
                ImportValue(d["network_stack_name"] + "-PublicSubnetId2"),
            ],
            Tags=Tags(d["tags"]),
        )
    )

    # ECS cluster
    ECSCluster = t.add_resource(
        Cluster("ECSCluster", ClusterName=d["project_name"], Tags=Tags(d["tags"]))
    )

    # ECS cluster SG
    ClusterSG = t.add_resource(
        SecurityGroup(
            "ClusterSG",
            GroupDescription="Enable HTTP access.",
            SecurityGroupIngress=[
                SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort="0",
                    ToPort="65535",
                    SourceSecurityGroupId=Ref(ALBSG),
                )
            ],
            VpcId=ImportValue(d["network_stack_name"] + "-VPCId"),
        )
    )

    # ALB listener
    listener80 = t.add_resource(
        elb.Listener(
            "Listener80",
            Port="80",
            Protocol="HTTP",
            LoadBalancerArn=Ref("ALB"),
            DefaultActions=[
                elb.Action(
                    Type="fixed-response",
                    FixedResponseConfig=elb.FixedResponseConfig(
                        StatusCode="200",
                        MessageBody=(
                            "This is a fixed response for the default " "ALB action"
                        ),
                        ContentType="text/plain",
                    ),
                )
            ],
        )
    )

    # ECS service role
    ECSClusterRole = t.add_resource(
        Role(
            "ECSClusterRole",
            RoleName="ECSClusterRole",
            AssumeRolePolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        )
    )

    # ECS Cluster Role Policy
    t.add_resource(
        PolicyType(
            'ECSClusterRolePolicy',
            PolicyName="ECSCLusterRolePolicy",
            Roles=[Ref(ECSClusterRole)],
            PolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "ECSTaskManagement",
                        "Effect": "Allow",
                        "Action": [
                            "ec2:AttachNetworkInterface",
                            "ec2:CreateNetworkInterface",
                            "ec2:CreateNetworkInterfacePermission",
                            "ec2:DeleteNetworkInterface",
                            "ec2:DeleteNetworkInterfacePermission",
                            "ec2:Describe*",
                            "ec2:DetachNetworkInterface",
                            "elasticloadbalancing:DeregisterInstancesFromLoadBalancer",
                            "elasticloadbalancing:DeregisterTargets",
                            "elasticloadbalancing:Describe*",
                            "elasticloadbalancing:RegisterInstancesWithLoadBalancer",
                            "elasticloadbalancing:RegisterTargets",
                            "route53:ChangeResourceRecordSets",
                            "route53:CreateHealthCheck",
                            "route53:DeleteHealthCheck",
                            "route53:Get*",
                            "route53:List*",
                            "route53:UpdateHealthCheck",
                            "servicediscovery:DeregisterInstance",
                            "servicediscovery:Get*",
                            "servicediscovery:List*",
                            "servicediscovery:RegisterInstance",
                            "servicediscovery:UpdateInstanceCustomHealthStatus",
                            "ecr:*",
                            "cloudwatch:*",
                            "logs:*",
                            "iam:*",
                        ],
                        "Resource": "*"
                    },
                    {
                        "Sid": "AutoScaling",
                        "Effect": "Allow",
                        "Action": [
                            "autoscaling:Describe*"
                        ],
                        "Resource": "*"
                    },
                    {
                        "Sid": "AutoScalingManagement",
                        "Effect": "Allow",
                        "Action": [
                            "autoscaling:DeletePolicy",
                            "autoscaling:PutScalingPolicy",
                            "autoscaling:SetInstanceProtection",
                            "autoscaling:UpdateAutoScalingGroup"
                        ],
                        "Resource": "*",
                        "Condition": {
                            "Null": {
                                "autoscaling:ResourceTag/AmazonECSManaged": "false"
                            }
                        }
                    },
                    {
                        "Sid": "AutoScalingPlanManagement",
                        "Effect": "Allow",
                        "Action": [
                            "autoscaling-plans:CreateScalingPlan",
                            "autoscaling-plans:DeleteScalingPlan",
                            "autoscaling-plans:DescribeScalingPlans"
                        ],
                        "Resource": "*"
                    },
                    {
                        "Sid": "CWAlarmManagement",
                        "Effect": "Allow",
                        "Action": [
                            "cloudwatch:DeleteAlarms",
                            "cloudwatch:DescribeAlarms",
                            "cloudwatch:PutMetricAlarm"
                        ],
                        "Resource": "arn:aws:cloudwatch:*:*:alarm:*"
                    },
                    {
                        "Sid": "ECSTagging",
                        "Effect": "Allow",
                        "Action": [
                            "ec2:CreateTags"
                        ],
                        "Resource": "arn:aws:ec2:*:*:network-interface/*"
                    },
                    {
                        "Sid": "CWLogGroupManagement",
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:DescribeLogGroups",
                            "logs:PutRetentionPolicy"
                        ],
                        "Resource": "arn:aws:logs:*:*:log-group:/aws/ecs/*"
                    },
                    {
                        "Sid": "CWLogStreamManagement",
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogStream",
                            "logs:DescribeLogStreams",
                            "logs:PutLogEvents"
                        ],
                        "Resource": "arn:aws:logs:*:*:log-group:/aws/ecs/*:log-stream:*"
                    }
                ]
            }
        )
    )

    # Codebuild role
    CodebuildDeveloperRole = t.add_resource(
        Role(
            "CodebuildDeveloperRole",
            RoleName="CodebuilDevelopRole",
            AssumeRolePolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "codebuild.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        )
    )

    # Codebuild developer role policy
    t.add_resource(
        PolicyType(
            'CodebuildDeveloperRolePolicy',
            PolicyName="CodebuildDeveloperRolePolicy",
            Roles=[Ref(CodebuildDeveloperRole)],
            PolicyDocument={
                "Statement": [
                    {
                        "Action": [
                            "codebuild:StartBuild",
                            "codebuild:StopBuild",
                            "codebuild:BatchGet*",
                            "codebuild:GetResourcePolicy",
                            "codebuild:DescribeTestCases",
                            "codebuild:List*",
                            "codecommit:GetBranch",
                            "codecommit:GetCommit",
                            "codecommit:GetRepository",
                            "codecommit:ListBranches",
                            "cloudwatch:GetMetricStatistics",
                            "events:DescribeRule",
                            "events:ListTargetsByRule",
                            "events:ListRuleNamesByTarget",
                            "logs:GetLogEvents",
                            "s3:*",
                            "logs:*",
                            "ecr:*"
                        ],
                        "Effect": "Allow",
                        "Resource": "*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "ssm:PutParameter"
                        ],
                        "Resource": "arn:aws:ssm:*:*:parameter/CodeBuild/*"
                    },
                    {
                        "Sid": "CodeStarNotificationsReadWriteAccess",
                        "Effect": "Allow",
                        "Action": [
                            "codestar-notifications:CreateNotificationRule",
                            "codestar-notifications:DescribeNotificationRule",
                            "codestar-notifications:UpdateNotificationRule",
                            "codestar-notifications:Subscribe",
                            "codestar-notifications:Unsubscribe"
                        ],
                        "Resource": "*",
                        "Condition": {
                            "StringLike": {
                                "codestar-notifications:NotificationsForResource": "arn:aws:codebuild:*"
                            }
                        }
                    },
                    {
                        "Sid": "CodeStarNotificationsListAccess",
                        "Effect": "Allow",
                        "Action": [
                            "codestar-notifications:ListNotificationRules",
                            "codestar-notifications:ListEventTypes",
                            "codestar-notifications:ListTargets",
                            "codestar-notifications:ListTagsforResource"
                        ],
                        "Resource": "*"
                    },
                    {
                        "Sid": "SNSTopicListAccess",
                        "Effect": "Allow",
                        "Action": [
                            "sns:ListTopics",
                            "sns:GetTopicAttributes"
                        ],
                        "Resource": "*"
                    }
                ],
                "Version": "2012-10-17"
            }
        )
    )

    # Codepipeline role
    CodePipelineRole = t.add_resource(
        Role(
            "CodePipelineRole",
            RoleName="CodePipelineRole",
            AssumeRolePolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "codepipeline.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        )
    )

    t.add_resource(
        PolicyType(
            'CodePipelineRolePolicy',
            PolicyName="CodePipelineRolePolicy",
            Roles=[Ref(CodePipelineRole)],
            PolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": [
                            "cloudformation:CreateStack",
                            "cloudformation:DeleteStack",
                            "cloudformation:DescribeStacks",
                            "cloudformation:UpdateStack",
                            "cloudformation:CreateChangeSet",
                            "cloudformation:DeleteChangeSet",
                            "cloudformation:DescribeChangeSet",
                            "cloudformation:ExecuteChangeSet",
                            "cloudformation:SetStackPolicy",
                            "cloudformation:ValidateTemplate",
                            "iam:PassRole",
                            "s3:*",
                        ],
                        "Resource": "*",
                        "Effect": "Allow"
                    },
                    {
                        "Action": [
                            "codebuild:BatchGetBuilds",
                            "codebuild:StartBuild"
                        ],
                        "Resource": "*",
                        "Effect": "Allow"
                    },
                    {
                        "Action": [
                            "ecr:*"
                        ],
                        "Resource": "*",
                        "Effect": "Allow"
                    },
                    {
                        "Action": [
                            "ecs:DescribeServices",
                            "ecs:DescribeTaskDefinition",
                            "ecs:DescribeTasks",
                            "ecs:ListTasks",
                            "ecs:RegisterTaskDefinition",
                            "ecs:UpdateService"
                        ],
                        "Resource": "*",
                        "Effect": "Allow"
                    },
                    {
                        "Action": [
                            "codedeploy:CreateDeployment",
                            "codedeploy:GetDeployment",
                            "codedeploy:GetApplication",
                            "codedeploy:GetApplicationRevision",
                            "codedeploy:RegisterApplicationRevision",
                            "codedeploy:GetDeploymentConfig",
                            "ecs:RegisterTaskDefinition",
                            "iam:PassRole"
                        ],
                        "Resource": "*",
                        "Effect": "Allow"
                    }
                ]
            }
        )
    )
    # Outputs

    # ListenerArnHTTP
    t.add_output(
        Output(
            "ListenerArnHTTP",
            Description="Listener Arn (HTTP) of the newly created Listener",
            Export=Export(Sub("${AWS::StackName}-ListenerArnHTTP")),
            Value=Ref(listener80),
        )
    )

    t.add_output(
        Output(
            "ECSClusterRole",
            Description="ECS Cluster role with managed policy",
            Export=Export(Sub("${AWS::StackName}-ECSClusterRole")),
            Value=GetAtt(ECSClusterRole, "Arn"),
        )
    )

    t.add_output(
        Output(
            "CodePipelineRole",
            Description="CodePipeline role with managed policy",
            Export=Export(Sub("${AWS::StackName}-CodePipelineRole")),
            Value=GetAtt(CodePipelineRole, "Arn"),
        )
    )

    t.add_output(
        Output(
            "CodebuildDeveloperRole",
            Description="Codebuild role with managed policy",
            Export=Export(Sub("${AWS::StackName}-CodebuildDeveloperRole")),
            Value=GetAtt(CodebuildDeveloperRole, "Arn"),
        )
    )

    t.add_output(
        Output(
            "ECSClusterName",
            Description="ECS cluster name.",
            Export=Export(Sub("${AWS::StackName}-ECSClusterName")),
            # Value=GetAtt(ECSCluster, "Arn"),
            Value=Ref(ECSCluster),
        )
    )

    t.add_output(
        Output(
            "ALB",
            Description="ALB name.",
            Export=Export(Sub("${AWS::StackName}-ALBName")),
            Value=GetAtt(ALB, "LoadBalancerName"),
        )
    )

    t.add_output(
        Output(
            "ECSClusterSG",
            Description="ECS Cluster SG name.",
            Export=Export(Sub("${AWS::StackName}-ECSClusterSG")),
            Value=Ref(ClusterSG),
        )
    )

    return t
