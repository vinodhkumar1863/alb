import boto3

# Create an EC2 client
ec2_client = boto3.client('ec2')

# Create a VPC
vpc_response = ec2_client.create_vpc(
    CidrBlock='10.0.0.0/16'
)

# Create subnets in different availability zones
subnet_response1 = ec2_client.create_subnet(
    AvailabilityZone='us-west-2a',
    CidrBlock='10.0.1.0/24',
    VpcId=vpc_response['Vpc']['VpcId']
)

subnet_response2 = ec2_client.create_subnet(
    AvailabilityZone='us-west-2b',
    CidrBlock='10.0.2.0/24',
    VpcId=vpc_response['Vpc']['VpcId']
)

# Launch EC2 instances in the subnets
instance1_response = ec2_client.run_instances(
    ImageId='ami-0abc1231bEXAMPLE',
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro',
    SubnetId=subnet_response1['Subnet']['SubnetId']
)

instance2_response = ec2_client.run_instances(
    ImageId='ami-0abc1231bEXAMPLE',
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro',
    SubnetId=subnet_response2['Subnet']['SubnetId']
)

# Create a Lambda function
lambda_client = boto3.client('lambda')

response = lambda_client.create_function(
    FunctionName='hello_world_lambda',
    Runtime='python3.8',
    Role='arn:aws:iam::123456789012:role/service-role/role-name',
    Handler='lambda_function.lambda_handler',
    Code={
        'S3Bucket': 'your-s3-bucket',
        'S3Key': 'lambda_function.zip'
    },
    Description='Hello World Lambda Function',
    Timeout=30,
    MemorySize=128
)

# Create an ELB client
elb_client = boto3.client('elbv2')

# Create a load balancer
response = elb_client.create_load_balancer(
    Name='my-load-balancer',
    Subnets=[
        subnet_response1['Subnet']['SubnetId'],
        subnet_response2['Subnet']['SubnetId']
    ],
    SecurityGroups=[
        'sg-0092c13EXAMPLE'
    ],
    Scheme='internet-facing',
    Type='application'
)

# Create a target group for the EC2 instances
target_group_response = elb_client.create_target_group(
    Name='my-target-group',
    Protocol='HTTP',
    Port=80,
    VpcId=vpc_response['Vpc']['VpcId'],
    HealthCheckProtocol='HTTP',
    HealthCheckPort='80',
    HealthCheckPath='/',
    TargetType='instance'
)

# Register targets (EC2 instances) to the target group
register_targets_response = elb_client.register_targets(
    TargetGroupArn=target_group_response['TargetGroups'][0]['TargetGroupArn'],
    Targets=[
        {
            'Id': instance1_response['Instances'][0]['InstanceId'],
            'Port': 80,
        },
        {
            'Id': instance2_response['Instances'][0]['InstanceId'],
            'Port': 80,
        },
    ]
)

# Create a listener for the user path
listener_response_user = elb_client.create_listener(
    LoadBalancerArn=response['LoadBalancers'][0]['LoadBalancerArn'],
    Protocol='HTTP',
    Port=80,
    DefaultActions=[
        {
            'Type': 'forward',
            'TargetGroupArn': target_group_response['TargetGroups'][0]['TargetGroupArn']
        }
    ]
)

# Create a target group for the Lambda function
lambda_target_group_response = elb_client.create_target_group(
    Name='lambda-target-group',
    Protocol='HTTP',
    Port=80,
    VpcId=vpc_response['Vpc']['VpcId'],
    TargetType='lambda'
)

# Create a listener for the search path
listener_response_search = elb_client.create_listener(
    LoadBalancerArn=response['LoadBalancers'][0]['LoadBalancerArn'],
    Protocol='HTTP',
    Port=80,
    DefaultActions=[
        {
            'Type': 'forward',
            'TargetGroupArn': lambda_target_group_response['TargetGroups'][0]['TargetGroupArn']
        }
    ]
)