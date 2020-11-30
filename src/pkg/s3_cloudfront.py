from troposphere import Output, Ref, Template, Join, GetAtt, Tags
from troposphere.s3 import Bucket, Private, PublicAccessBlockConfiguration, BucketPolicy
from troposphere.cloudfront import Distribution, DistributionConfig
from troposphere.cloudfront import Origin, DefaultCacheBehavior
from troposphere.cloudfront import ForwardedValues
from troposphere.cloudfront import S3OriginConfig
from troposphere.cloudfront import CloudFrontOriginAccessIdentity, CloudFrontOriginAccessIdentityConfig
from troposphere.cloudfront import CustomErrorResponse, ViewerCertificate
from awacs.aws import (
    Allow,
    Policy,
    Principal,
    Statement
)

def generate_template(d):
    t = Template()
    t.set_description(d["cf_template_description"])

    S3bucket = t.add_resource(
        Bucket(
            "S3Bucket", 
            BucketName=Join("-", [d["project_name"], d["env"]]),
            AccessControl=Private,
            PublicAccessBlockConfiguration=PublicAccessBlockConfiguration(
                BlockPublicAcls=True,
                BlockPublicPolicy=True,
                IgnorePublicAcls=True,
                RestrictPublicBuckets=True,
            ),
            Tags=Tags(d["tags"], {"Name": d["project_name"]}),
        )
    )

    CFOriginAccessIdentity = t.add_resource(
        CloudFrontOriginAccessIdentity(
            "CFOriginAccessIdentity",
            CloudFrontOriginAccessIdentityConfig=CloudFrontOriginAccessIdentityConfig(
                Comment=Join(" ", ["Cloudfront Origin Access Identity", d["project_name"], d["env"]])
            ),
        )
    )

    t.add_resource(
        BucketPolicy(
            "BucketPolicy",
            Bucket=Ref("S3Bucket"),
            PolicyDocument=dict(
                Statement=[
                    dict(
                        Sid="Allow-cf",
                        Effect="Allow",
                        Action=[
                            "s3:GetObject", 
                            "s3:ListBucket"
                        ],
                        Principal=Principal(
                            "CanonicalUser",
                            GetAtt(CFOriginAccessIdentity, "S3CanonicalUserId")
                        ),
                        Resource=[
                            Join("", ["arn:aws:s3:::", Ref("S3Bucket"), "/*"]),
                            Join("", ["arn:aws:s3:::", Ref("S3Bucket")]),
                        ]
                    )
                ]
            )
        )
    )

    myDistribution = t.add_resource(
        Distribution(
            "myDistribution",
            DistributionConfig=DistributionConfig(
                Enabled=True,
                HttpVersion='http2',
                DefaultRootObject=d['default_root_object'],
                Origins=[Origin(
                    Id=Join("-", [d["project_name"], d["env"]]), 
                    DomainName=GetAtt(S3bucket, "DomainName"),
                    S3OriginConfig=S3OriginConfig(
                        OriginAccessIdentity=Join("/",["origin-access-identity", "cloudfront", Ref(CFOriginAccessIdentity)])
                    )
                )],
                DefaultCacheBehavior=DefaultCacheBehavior(
                    TargetOriginId=Join("-", [d["project_name"], d["env"]]),
                    ForwardedValues=ForwardedValues(
                        QueryString=False
                    ),
                    ViewerProtocolPolicy="allow-all",
                    MaxTTL=0,
                    MinTTL=0,
                    DefaultTTL=0,
                ),
                CustomErrorResponses=[CustomErrorResponse(
                    ErrorCachingMinTTL=0,
                    ErrorCode=404,
                    ResponsePagePath=Join("",["/", d['default_root_object']]),
                    ResponseCode=200,
                )],
                ViewerCertificate=ViewerCertificate(
                    CloudFrontDefaultCertificate=True
                ),
            ),
            Tags=Tags(d["tags"], {"Name": d["project_name"]}),
        )
    )

    t.add_output(Output(
        "BucketName",
        Value=Ref(S3bucket),
        Description="Name of S3 bucket to hold website content"
    ))

    t.add_output([
    Output("DistributionId", Value=Ref(myDistribution)),
    Output(
        "DistributionName",
        Value=Join("", ["http://", GetAtt(myDistribution, "DomainName")])),
    ])

    return t

