# Notes and Recommendations (Important to know about):
# Testing: Thoroughly test this script in a non-production environment before running it in production.
# Error Handling: Implement comprehensive error handling for production use.
# Permissions: Ensure your AWS credentials have the necessary permissions for these actions.
# Endpoint Deletion: The delete_gwlb_endpoints function assumes that GWLB endpoints are identifiable by their association with the VPC. Adjust this function if your endpoints are tagged or identified differently.
# Target Group Retrieval: The get_gwlb_details function assumes there's only one target group associated with the GWLB. If there are multiple target groups, this logic should be adjusted.
# Safety Checks: Consider adding more checks and logs to ensure each step completes successfully before proceeding to the next.

# This script provides a structured approach to automate the deletion of resources in an AWS environment, but due to the potential 
# impact of these operations, careful consideration and testing are advised.

iimport boto3
from botocore.exceptions import ClientError, BotoCoreError
from time import sleep

# Initialize AWS clients
elbv2_client = boto3.client('elbv2')
ec2_client = boto3.client('ec2')

def get_gwlb_details(gwlb_name):
    """
    Retrieves the details of a specified Gateway Load Balancer and its first associated target group.
    Args:
    - gwlb_name: Name of the Gateway Load Balancer
    Returns:
    - Tuple containing GWLB details and Target Group ARN
    """
    try:
        response = elbv2_client.describe_load_balancers(Names=[gwlb_name])
        gwlb = response['LoadBalancers'][0]
        target_group_arn = gwlb['TargetGroups'][0]['TargetGroupArn']  # Assuming single target group
        return gwlb, target_group_arn
    except ClientError as e:
        print(f"Error retrieving GWLB details: {e}")
        return None, None

def get_registered_targets(target_group_arn):
    """
    Retrieves a list of targets registered with a given target group.
    Args:
    - target_group_arn: ARN of the target group
    Returns:
    - List of registered target IDs
    """
    try:
        response = elbv2_client.describe_target_health(TargetGroupArn=target_group_arn)
        return [target['Target']['Id'] for target in response['TargetHealthDescriptions']]
    except ClientError as e:
        print(f"Error retrieving registered targets: {e}")
        return []

def deregister_targets(target_group_arn, targets):
    """
    Deregisters targets from a specified target group.
    Args:
    - target_group_arn: ARN of the target group
    - targets: List of target IDs to deregister
    """
    try:
        elbv2_client.deregister_targets(TargetGroupArn=target_group_arn, Targets=[{'Id': target} for target in targets])
    except ClientError as e:
        print(f"Error deregistering targets: {e}")

def terminate_ec2_instances(instance_ids):
    """
    Terminates a list of specified EC2 instances.
    Args:
    - instance_ids: List of EC2 instance IDs
    """
    try:
        ec2_client.terminate_instances(InstanceIds=instance_ids)
    except ClientError as e:
        print(f"Error terminating EC2 instances: {e}")

def check_instances_terminated(instance_ids):
    """
    Checks whether the specified EC2 instances are terminated.
    Args:
    - instance_ids: List of EC2 instance IDs
    """
    try:
        while True:
            response = ec2_client.describe_instances(InstanceIds=instance_ids)
            statuses = [instance['State']['Name'] for reservation in response['Reservations'] for instance in reservation['Instances']]
            if all(status == 'terminated' for status in statuses):
                break
            sleep(10)  # Wait for 10 seconds before next check
    except ClientError as e:
        print(f"Error checking instance termination status: {e}")

def delete_target_group(target_group_arn):
    """
    Deletes a specified target group.
    Args:
    - target_group_arn: ARN of the target group
    """
    try:
        elbv2_client.delete_target_group(TargetGroupArn=target_group_arn)
    except ClientError as e:
        print(f"Error deleting target group: {e}")

def delete_gwlb(gwlb_arn):
    """
    Deletes a specified Gateway Load Balancer.
    Args:
    - gwlb_arn: ARN of the Gateway Load Balancer
    """
    try:
        elbv2_client.delete_load_balancer(LoadBalancerArn=gwlb_arn)
    except ClientError as e:
        print(f"Error deleting GWLB: {e}")

def delete_gwlb_endpoints(vpc_id):
    """
    Deletes Gateway Load Balancer endpoints associated with a specified VPC.
    Args:
    - vpc_id: ID of the VPC
    """
    try:
        response = ec2_client.describe_vpc_endpoints(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        endpoint_ids = [endpoint['VpcEndpointId'] for endpoint in response['VpcEndpoints']]
        for endpoint_id in endpoint_ids:
            ec2_client.delete_vpc_endpoints(VpcEndpointIds=[endpoint_id])
    except ClientError as e:
        print(f"Error deleting GWLB endpoints: {e}")

def main():
    """
    Main function to orchestrate the deletion of an older Inspection VPC with its associated resources.
    """
    # User inputs
    gwlb_name = input("Enter the name of the Gateway Load Balancer: ")
    vpc_id = input("Enter the VPC ID: ")

    # Workflow execution
    gwlb, target_group_arn = get_gwlb_details(gwlb_name)
    if gwlb and target_group_arn:
        print("Gateway Load Balancer Details:", gwlb)

        targets = get_registered_targets(target_group_arn)
        print("Registered Targets:", targets)

        if targets:
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
    else:
        print("Failed to retrieve GWLB details. Exiting.")

if __name__ == "__main__":
    main()
