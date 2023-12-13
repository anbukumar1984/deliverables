# Notes and Recommendations:
# Replace Placeholders: Replace 'my-gwlb' and 'vpc-12345678' with actual values from your AWS environment.
# Testing: Thoroughly test this script in a non-production environment before running it in production.
# Error Handling: Implement comprehensive error handling for production use.
# Permissions: Ensure your AWS credentials have the necessary permissions for these actions.
# Endpoint Deletion: The delete_gwlb_endpoints function assumes that GWLB endpoints are identifiable by their association with the VPC. Adjust this function if your endpoints are tagged or identified differently.
# Target Group Retrieval: The get_gwlb_details function assumes there's only one target group associated with the GWLB. If there are multiple target groups, this logic should be adjusted.
# Safety Checks: Consider adding more checks and logs to ensure each step completes successfully before proceeding to the next.


import boto3
from time import sleep

elbv2_client = boto3.client('elbv2')
ec2_client = boto3.client('ec2')

def get_gwlb_details(gwlb_name):
    response = elbv2_client.describe_load_balancers(Names=[gwlb_name])
    gwlb = response['LoadBalancers'][0]
    target_group_arn = gwlb['TargetGroups'][0]['TargetGroupArn']  # Assuming single target group
    return gwlb, target_group_arn

def get_registered_targets(target_group_arn):
    response = elbv2_client.describe_target_health(TargetGroupArn=target_group_arn)
    return [target['Target']['Id'] for target in response['TargetHealthDescriptions']]

def deregister_targets(target_group_arn, targets):
    elbv2_client.deregister_targets(TargetGroupArn=target_group_arn, Targets=[{'Id': target} for target in targets])

def terminate_ec2_instances(instance_ids):
    ec2_client.terminate_instances(InstanceIds=instance_ids)

def check_instances_terminated(instance_ids):
    while True:
        response = ec2_client.describe_instances(InstanceIds=instance_ids)
        statuses = [instance['State']['Name'] for reservation in response['Reservations'] for instance in reservation['Instances']]
        if all(status == 'terminated' for status in statuses):
            break
        sleep(10)  # Wait for 10 seconds before next check

def delete_target_group(target_group_arn):
    elbv2_client.delete_target_group(TargetGroupArn=target_group_arn)

def delete_gwlb(gwlb_arn):
    elbv2_client.delete_load_balancer(LoadBalancerArn=gwlb_arn)

def delete_gwlb_endpoints(vpc_id):
    # Assuming endpoints are tagged or named to identify them as belonging to the specific VPC
    response = ec2_client.describe_vpc_endpoints(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    endpoint_ids = [endpoint['VpcEndpointId'] for endpoint in response['VpcEndpoints']]
    for endpoint_id in endpoint_ids:
        ec2_client.delete_vpc_endpoints(VpcEndpointIds=[endpoint_id])

# Replace with your values
gwlb_name = 'my-gwlb'
vpc_id = 'vpc-12345678'

# Workflow execution
gwlb, target_group_arn = get_gwlb_details(gwlb_name)
print("Gateway Load Balancer Details:", gwlb)

targets = get_registered_targets(target_group_arn)
print("Registered Targets:", targets)

deregister_targets(target_group_arn, targets)
print("Targets Deregistered")

terminate_ec2_instances(targets)
print("EC2 Instances Termination Initiated")

check_instances_terminated(targets)
print("EC2 Instances Terminated")

delete_target_group(target_group_arn)
print("Target Group Deleted")

delete_gwlb_endpoints(vpc_id)
print("GWLB Endpoints Deleted")

delete_gwlb(gwlb['LoadBalancerArn'])
print("GWLB Deleted")

print("Deletion process completed.")

