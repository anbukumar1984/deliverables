def get_vpc_endpoint_id_for_gwlb(service_name, vpc_id):
    """
    Retrieves the VPC Endpoint ID for a given GWLB service name within a specific VPC.
    Args:
    - service_name: Service name of the Gateway Load Balancer
    - vpc_id: ID of the VPC
    Returns:
    - The VPC Endpoint ID or None if not found
    """
    try:
        response = ec2_client.describe_vpc_endpoints(
            Filters=[
                {'Name': 'service-name', 'Values': [service_name]},
                {'Name': 'vpc-id', 'Values': [vpc_id]}
            ]
        )
        for endpoint in response['VpcEndpoints']:
            return endpoint['VpcEndpointId']
        return None
    except ClientError as e:
        print(f"Error retrieving VPC Endpoint ID: {e}")
        return None
    
    
def disassociate_route_tables(vpc_endpoint_id):
    """
    Disassociates route tables from the specified VPC Endpoint.
    Args:
    - vpc_endpoint_id: ID of the VPC Endpoint
    """
    try:
        # Retrieve the route table associations
        response = ec2_client.describe_route_tables(
            Filters=[{'Name': 'route.vpc-endpoint-id', 'Values': [vpc_endpoint_id]}]
        )
        for route_table in response['RouteTables']:
            for route in route_table['Routes']:
                if route.get('VpcEndpointId') == vpc_endpoint_id:
                    ec2_client.delete_route(
                        RouteTableId=route_table['RouteTableId'],
                        DestinationCidrBlock=route['DestinationCidrBlock']
                    )
    except ClientError as e:
        print(f"Error disassociating route tables: {e}")


def delete_vpc_endpoint(vpc_endpoint_id):
    """
    Deletes the specified VPC Endpoint.
    Args:
    - vpc_endpoint_id: ID of the VPC Endpoint
    """
    try:
        ec2_client.delete_vpc_endpoints(VpcEndpointIds=[vpc_endpoint_id])
        print(f"Deleted VPC Endpoint {vpc_endpoint_id}")
    except ClientError as e:
        print(f"Error deleting VPC Endpoint: {e}")

def main():
    service_name = 'com.amazonaws.region.vpce.svc-xxxxxxxxxxxxxxxx'  # replace with actual service name
    vpc_id = 'vpc-xxxxxxx'  # replace with your VPC ID

    vpc_endpoint_id = get_vpc_endpoint_id_for_gwlb(service_name, vpc_id)
    if vpc_endpoint_id:
        disassociate_route_tables(vpc_endpoint_id)
        delete_vpc_endpoint(vpc_endpoint_id)
    else:
        print("VPC Endpoint not found.")

if __name__ == "__main__":
    main()


###################################
# Alternate approach

def disassociate_route_tables(vpc_endpoint_id, vpc_id):
    """
    Disassociates route tables from the specified VPC Endpoint.
    Args:
    - vpc_endpoint_id: ID of the VPC Endpoint
    - vpc_id: ID of the VPC
    """
    try:
        # Retrieve all route tables in the VPC
        response = ec2_client.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        for route_table in response['RouteTables']:
            for route in route_table['Routes']:
                # Check if the route is associated with the VPC Endpoint
                if 'VpcEndpointId' in route and route['VpcEndpointId'] == vpc_endpoint_id:
                    # Delete the route
                    ec2_client.delete_route(
                        RouteTableId=route_table['RouteTableId'],
                        DestinationCidrBlock=route['DestinationCidrBlock']
                    )
                    print(f"Route to {route['DestinationCidrBlock']} disassociated from {vpc_endpoint_id}")
    except ClientError as e:
        print(f"Error disassociating route tables: {e}")

