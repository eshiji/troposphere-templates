from troposphere import GetAtt, Output, Sub, Export
from troposphere import Ref, Tags, Template
from troposphere.ec2 import (
    Route,
    VPCGatewayAttachment,
    SubnetRouteTableAssociation,
    Subnet,
    RouteTable,
    VPC,
    EIP,
    InternetGateway,
    NatGateway,
)


def generate_template(d):
    # Set template metadata
    t = Template()
    t.add_version("2010-09-09")
    t.set_description(d["cf_template_description"])

    # ref_stack_id = Ref('AWS::StackId')
    # ref_region = Ref('AWS::Region')
    # ref_stack_name = Ref('AWS::StackName')

    # Create VPC
    vpc = t.add_resource(
        VPC(
            "VPC",
            EnableDnsSupport=True,
            EnableDnsHostnames=True,
            CidrBlock=d["vpc_cidr_block"],
            Tags=Tags(d["tags"], {"Name": d["project_name"]}),
        )
    )

    # Create Public Subnets
    public_subnet_count = 1
    public_subnets = []
    az_count = 0
    for public_subnet_cidr_block in d["public_subnet_cidr_blocks"]:
        public_subnets.append(
            t.add_resource(
                Subnet(
                    "PublicSubnet" + str(public_subnet_count),
                    CidrBlock=public_subnet_cidr_block,
                    VpcId=Ref(vpc),
                    AvailabilityZone=d["availability_zones"][az_count],
                    Tags=Tags(
                        d["tags"],
                        {
                            "Name": d["project_name"]
                            + "-public-subnet"
                            + str(public_subnet_count)
                        },
                    ),
                )
            )
        )
        public_subnet_count += 1
        az_count += 1

    # Create Private Subnets
    private_subnet_count = 1
    private_subnets = []
    az_count = 0
    for private_subnet_cidr_block in d["private_subnet_cidr_blocks"]:
        private_subnets.append(
            t.add_resource(
                Subnet(
                    "PrivateSubnet" + str(private_subnet_count),
                    CidrBlock=private_subnet_cidr_block,
                    VpcId=Ref(vpc),
                    AvailabilityZone=d["availability_zones"][az_count],
                    Tags=Tags(
                        d["tags"],
                        {
                            "Name": d["project_name"]
                            + "-private-subnet"
                            + str(private_subnet_count)
                        },
                    ),
                )
            )
        )
        private_subnet_count += 1
        az_count += 1

    # Create Internet Gateway
    internetGateway = t.add_resource(
        InternetGateway(
            "InternetGateway",
            Tags=Tags(
                d["tags"],
                {
                    "Name": d["project_name"]
                    + "-igw"
                }
            ),
        )
    )

    # Attach Internet Gateway to VPC
    t.add_resource(
        VPCGatewayAttachment(
            "AttachmentInternetGateway",
            VpcId=Ref(vpc),
            InternetGatewayId=Ref(internetGateway),
        )
    )

    # Create Two EIP for each Nat Gateway
    eip_count = 1
    for eip in range(2):
        t.add_resource(
            EIP(
                "Eip" + str(eip_count),
                Domain="vpc",
                Tags=Tags(
                    d["tags"],
                    {
                        "Name": d["project_name"]
                        + "-eip"
                        + str(eip_count)
                    }
                ),
            )
        )
        eip_count += 1

    # Create Public Route Table
    publicRouteTable = t.add_resource(
        RouteTable(
            "PublicRouteTable",
            VpcId=Ref(vpc),
            Tags=Tags(
                d["tags"],
                {
                    "Name": d["project_name"]
                    + "-public-rtb"
                }
            ),
        )
    )

    # Create Route to Internet Gateway on Public Route Table
    t.add_resource(
        Route(
            "RouteIgw",
            DependsOn="AttachmentInternetGateway",
            GatewayId=Ref("InternetGateway"),
            DestinationCidrBlock="0.0.0.0/0",
            RouteTableId=Ref(publicRouteTable),
        )
    )

    # Create Private Route Table1
    PrivateRouteTable1 = t.add_resource(
        RouteTable(
            "PrivateRouteTable1",
            VpcId=Ref(vpc),
            Tags=Tags(
                d["tags"],
                {
                    "Name": d["project_name"]
                    + "-private-rtb1"
                }
            ),
        )
    )

    # Create Private Route Table2
    PrivateRouteTable2 = t.add_resource(
        RouteTable(
            "PrivateRouteTable2",
            VpcId=Ref(vpc),
            Tags=Tags(
                d["tags"],
                {
                    "Name": d["project_name"]
                    + "-private-rtb2"
                }
            ),
        )
    )

    # Associate Public Subnets with Public Route Table
    public_subnet_count = 1
    for public_subnet in range(len(public_subnets)):
        t.add_resource(
            SubnetRouteTableAssociation(
                "PublicSubnetRouteTableAssociation" + str(public_subnet_count),
                SubnetId=Ref("PublicSubnet" + str(public_subnet_count)),
                RouteTableId=Ref(publicRouteTable),
            )
        )
        public_subnet_count += 1

    # Associate Private Subnet1 with Private Route Table1
    t.add_resource(
        SubnetRouteTableAssociation(
            "PrivateSubnetPrivateRouteTableAssociation1",
            SubnetId=Ref("PrivateSubnet1"),
            RouteTableId=Ref(PrivateRouteTable1),
        )
    )

    # Associate Private Subnet2 with Private Route Table2
    t.add_resource(
        SubnetRouteTableAssociation(
            "PrivateSubnetPrivateRouteTableAssociation2",
            SubnetId=Ref("PrivateSubnet2"),
            RouteTableId=Ref(PrivateRouteTable2),
        )
    )

    # Create Two Nat Gateways one for each Private Route Table
    nat_gtw_count = 1
    public_subnet_count = 1
    for nat_gtw in range(2):
        t.add_resource(
            NatGateway(
                "Nat" + str(nat_gtw_count),
                AllocationId=GetAtt("Eip" + str(nat_gtw_count), "AllocationId"),
                SubnetId=Ref("PublicSubnet" + str(public_subnet_count)),
                Tags=Tags(
                    d["tags"],
                    {
                        "Name": d["project_name"]
                        + "-nat"
                        + str(public_subnet_count)
                    },
                ),
            )
        )
        nat_gtw_count += 1
        public_subnet_count += 1

    # Create route in rtb1 to nat1
    t.add_resource(
        Route(
            "RouteNat1",
            DependsOn="Nat1",
            NatGatewayId=Ref("Nat1"),
            DestinationCidrBlock="0.0.0.0/0",
            RouteTableId=Ref("PrivateRouteTable1"),
        )
    )

    # Create route in rtb2 to nat2
    t.add_resource(
        Route(
            "RouteNat2",
            DependsOn="Nat2",
            NatGatewayId=Ref("Nat2"),
            DestinationCidrBlock="0.0.0.0/0",
            RouteTableId=Ref("PrivateRouteTable2"),
        )
    )

    # Outputs
    t.add_output(
        Output(
            "VPCId",
            Description="VPCId of the newly created VPC",
            Export=Export(Sub("${AWS::StackName}-VPCId")),
            Value=Ref(vpc),
        )
    )

    public_subnet_count = 1
    count = 0
    for subnet in public_subnets:
        t.add_output(
            Output(
                "PublicSubnet" + str(public_subnet_count),
                Description=f"PublicSubnetId{public_subnet_count}for cross reference.",
                Export=Export(
                    Sub("${AWS::StackName}" + f"-PublicSubnetId{public_subnet_count}")
                ),
                Value=Ref(public_subnets[count]),
            )
        )
        count += 1
        public_subnet_count += 1

    private_subnet_count = 1
    count = 0
    for subnet in private_subnets:
        t.add_output(
            Output(
                "PrivateSubnet" + str(private_subnet_count),
                Description=f"PrivateSubnetId{private_subnet_count} for cross reference.",
                Export=Export(
                    Sub("${AWS::StackName}" + f"-PrivateSubnetId{private_subnet_count}")
                ),
                Value=Ref(private_subnets[count]),
            )
        )
        count += 1
        private_subnet_count += 1

    return t
