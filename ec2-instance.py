# 1. Modify get_registered_targets to Return IPs

def get_registered_targets(target_group_arn):
    """
    Retrieves a list of targets (either instance IDs or IPs) registered with a given target group.
    Args:
    - target_group_arn: ARN of the target group
    Returns:
    - List of registered target IDs or IPs
    """
    try:
        response = elbv2_client.describe_target_health(TargetGroupArn=target_group_arn)
        return [target['Target']['Id'] for target in response['TargetHealthDescriptions']]
    except ClientError as e:
        print(f"Error retrieving registered targets: {e}")
        return []

# 2. Map IPs to Instance IDs

def map_ips_to_instance_ids(ip_addresses):
    """
    Maps a list of IP addresses to their corresponding EC2 instance IDs.
    Args:
    - ip_addresses: List of IP addresses
    Returns:
    - Dictionary mapping IPs to instance IDs
    """
    instances = ec2_client.describe_instances()
    ip_to_instance_id = {}

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            for interface in instance['NetworkInterfaces']:
                ip_address = interface['PrivateIpAddress']
                if ip_address in ip_addresses:
                    ip_to_instance_id[ip_address] = instance['InstanceId']

    return ip_to_instance_id

# 3. Update terminate_ec2_instances

def terminate_ec2_instances(targets):
    """
    Terminates a list of specified EC2 instances or IPs.
    Args:
    - targets: List of EC2 instance IDs or IPs
    """
    # If the targets are IP addresses, map them to instance IDs
    if targets and is_ip_address(targets[0]):
        ip_to_instance_id = map_ips_to_instance_ids(targets)
        targets = [ip_to_instance_id[ip] for ip in targets if ip in ip_to_instance_id]

    try:
        ec2_client.terminate_instances(InstanceIds=targets)
    except ClientError as e:
        print(f"Error terminating EC2 instances: {e}")

# 4. Helper Function to Check If Target is IP

import re

def is_ip_address(address):
    """
    Checks if the given address is an IP address.
    Args:
    - address: String to check
    Returns:
    - Boolean indicating if the address is an IP
    """
    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    return ip_pattern.match(address) is not None
