import os
import sys
import requests
from time import strftime, sleep

import boto3
from botocore.exceptions import ClientError


CLUSTER_NAME = "default"
CLOUD_TASK_DEFINITION = "cloud-task-definition"
EXPLORA_TASK_DEFINITION = "explora-task-definition"
CLOUD_CONTAINER_NAME = "cloud-container"
EXPLORA_CONTAINER_NAME = "explora-container"
CLOUD_SUBDOMAIN = "{}.cloud.discreetai.com"
EXPLORA_SUBDOMAIN = "{}.explora.discreetai.com"
DOMAIN_ID = "/hostedzone/Z3NSW3B4FM6A7X"
DEPLOYING_STATUSES = ["PROVISIONING", "PENDING", "ACTIVATING"]
RUNNING_STATUS = "RUNNING"
SHUTTING_DOWN_STATUSES = ["DEACTIVATING", "STOPPING", "DEPROVISIONING"]
ERROR_STATUS = "STOPPED"

ecs_client = boto3.client("ecs")
ec2_client = boto3.resource("ec2")
route53_client = boto3.client('route53')

def create_new_nodes(repo_id, api_key):
    """
    Runs new tasks (Explora + cloud) for ECS cluster. Sets domain of task to 
    be `<repo_id>.cloud.discreetai.com by creating an record in Route53.
    
    Args:
        repo_id (str): The repo ID of the repo this task is to be associated
            with.
        api_key (str): The corresponding API key of the repo. Used for auth in
            the tasks.
    
    Returns:
        dict: A dictionary holding the public IP address and task ARN of the
            newly created cloud and Explora task.
    """
    cloud_ip_address, cloud_task_arn, explora_ip_address, explora_task_arn = \
        _run_new_tasks(api_key)
    names = _make_names(repo_id)
    ip_addresses = [cloud_ip_address, explora_ip_address]
    _modify_domains("CREATE", names, ip_addresses)
    return {
        "CloudIpAddress": cloud_ip_address,
        "CloudTaskArn": cloud_task_arn,
        "ExploraIpAddress": explora_ip_address,
        "ExploraTaskArn": explora_task_arn, 
        "ApiKey": api_key
    }

def stop_nodes(cloud_task_arn, explora_task_arn, repo_id, cloud_ip_address, \
        explora_ip_address):
    """
    Stop the cloud and Explora task with its task ARN and remove the 
    corresponding record in Route53.
    
    Args:
        cloud_task_arn (str): The ARN of the cloud task to be stopped.
        explora_task_arn (str): The ARN of the Explora task to be stopped.
        repo_id (str): The repo ID of the repo associated with this task.
        cloud_ip_address (str): The public IP address of the cloud task.
        explora_ip_address (str): The public IP address of the Explora task. 
    """
    _stop_tasks(cloud_task_arn, explora_task_arn)
    names = _make_names(repo_id)
    ip_addresses = [cloud_ip_address, explora_ip_address]
    _modify_domains("DELETE", names, ip_addresses)

def get_status(cloud_task_arn, explora_task_arn, repo_id):
    """
    Retrieve the statuses of the cloud and Explora task and form a general
    status. 
    
    Args:
        cloud_task_arn (str): The ARN of the cloud task to be stopped.
        explora_task_arn (str): The ARN of the Explora task to be stopped.
        repo_id (str): The repo ID of the repo associated with this task.
    
    Returns:
        str: The general status describing the state of both the tasks.
    """
    statuses = _retrieve_statuses(cloud_task_arn, explora_task_arn)
    return _determine_status(statuses, repo_id)

def _run_new_tasks(api_key):
    """
    Run new task in the provided cluster with the provided task definition.
    
    Args:
        api_key (str): The corresponding API key of the repo. Used for auth in
            the task.
    
    Returns:
        (str, str): The task ARN and public IP address of the newly created 
            task.
    """
    cloud_task_arn, explora_task_arn = _create_new_task(api_key)
    cloud_network_interface_id = _get_network_interface_id(cloud_task_arn)
    explora_network_interface_id = _get_network_interface_id(explora_task_arn)
    cloud_ip_address = _get_public_ip(cloud_network_interface_id)
    explora_ip_address = _get_public_ip(explora_network_interface_id)
    return cloud_ip_address, cloud_task_arn, explora_ip_address, \
        explora_task_arn

def _create_new_task(api_key):
    """
    Run new task in the provided cluster with the provided task definition.
    
    Args:
        api_key (str): The corresponding API key of the repo. Used for auth in
            the tasks.
    
    Returns:
        str: The task ARN of the newly created task.
    """
    cloud_task_response = ecs_client.run_task(
        cluster=CLUSTER_NAME,
        taskDefinition=CLOUD_TASK_DEFINITION,
        launchType="FARGATE",
        networkConfiguration = {
            "awsvpcConfiguration": {
                "subnets": ["subnet-066927cc2aa7d231f"],
                "assignPublicIp": "ENABLED",
            }
        },
        overrides = {
            "containerOverrides": [{
                "name": CLOUD_CONTAINER_NAME,
                "environment": [{
                    "name": "API_KEY",
                    "value": api_key
                }]
            }]
        }
    )

    explora_task_response = ecs_client.run_task(
        cluster=CLUSTER_NAME,
        taskDefinition=EXPLORA_TASK_DEFINITION,
        launchType="FARGATE",
        networkConfiguration = {
            "awsvpcConfiguration": {
                "subnets": ["subnet-066927cc2aa7d231f"],
                "assignPublicIp": "ENABLED",
            }
        },
        overrides = {
            "containerOverrides": [{
                "name": EXPLORA_CONTAINER_NAME,
                "environment": [{
                    "name": "API_KEY",
                    "value": api_key
                }]
            }]
        }
    )

    if cloud_task_response["failures"]:
        raise Exception(str(new_task_response["failures"]))

    if explora_task_response["failures"]:
        raise Exception(str(new_task_response["failures"]))

    cloud_task_arn = cloud_task_response["tasks"][0]["taskArn"]
    explora_task_arn = explora_task_response["tasks"][0]["taskArn"]

    return cloud_task_arn, explora_task_arn

def _get_network_interface_id(task_arn):
    """
    Retrieve the network interface ID associated with the task with the
    given task ARN. May take a few seconds as the ID is set after the task is 
    run.
    
    Args:
        task_arn (str): The task ARN of the newly created task.
    
    Returns:
        str: The network interface ID associated with the newly created task.
    """
    task_response = ecs_client.describe_tasks(
        tasks=[task_arn]
    )
    if task_response["failures"]:
        raise Exception(str(task_response["failures"]))
    task_details = task_response["tasks"][0]["attachments"][0]["details"]
    filter_function = lambda x: x["name"] == "networkInterfaceId"
    network_interface_details = list(filter(filter_function, task_details))
    if not network_interface_details:
        sleep(1)
        return _get_network_interface_id(task_arn)
    network_interface_id = network_interface_details[0]["value"]
    return network_interface_id

def _get_public_ip(network_interface_id):
    """
    Retrieve the public IP address of the task associated with the provided
    network interface ID. May take a few seconds as the address is set after 
    the task is run. 
    
    Args:
        network_interface_id (str): The network interface ID associated with 
            the newly created task.
    
    Returns:
        str: The public IP address of the newly created task.
    """
    network_interface = ec2_client.NetworkInterface(network_interface_id)
    ip_address_details = network_interface.private_ip_addresses[0]
    if "Association" not in ip_address_details:
        sleep(1)
        return _get_public_ip(network_interface_id)
    ip_address = ip_address_details["Association"]["PublicIp"]
    return ip_address

def _stop_tasks(cloud_task_arn, explora_task_arn):
    """
    Stop cloud and Explora task with the provided task ARNs.
    
    Args:
        cloud_task_arn (str): The ARN of the cloud task to be stopped.
        explora_task_arn (str): The ARN of the Explora task to be stopped.
    """
    _ = ecs_client.stop_task(
        cluster=CLUSTER_NAME,
        task=cloud_task_arn,
        reason="User requested deletion."
    )

    _ = ecs_client.stop_task(
        cluster=CLUSTER_NAME,
        task=explora_task_arn,
        reason="User requested deletion."
    )

def _retrieve_statuses(cloud_task_arn, explora_task_arn):
    """
    Retrieve the actual task statuses from the cloud and Explora tasks.
    
    Args:
        cloud_task_arn (str): The ARN of the cloud task to be stopped.
        explora_task_arn (str): The ARN of the Explora task to be stopped.
    
    Returns:
        str: The actual task statuses of the two tasks.
    """
    describe_response = ecs_client.describe_tasks(
        cluster=CLUSTER_NAME,
        tasks=[
            cloud_task_arn,
            explora_task_arn
        ]
    )
    return [task["containers"][0]["lastStatus"] \
        for task in describe_response["tasks"]]

def _determine_status(statuses, repo_id):
    """
    Determine the general status given the actual two task statuses of the
    cloud and Explora tasks.

    For example, as long as one task is deploying/shutting down/shut down, both
    are considered deploying/shutting down/shut down. 
    
    Args:
        statuses (list): The two task statuses of the cloud and Explora tasks.
        repo_id (str): The repo ID of the repo associated with this task.
    
    Returns:
        str: The general status describing the state of both the tasks.
    """
    if any([status == ERROR_STATUS for status in statuses]):
        return "ERROR"
    elif any([status in SHUTTING_DOWN_STATUSES for status in statuses]):
        return "SHUTTING DOWN"
    elif any([status in DEPLOYING_STATUSES for status in statuses]):
        return "DEPLOYING"
    elif all([status == RUNNING_STATUS for status in statuses]):
        cloud_node_url = CLOUD_SUBDOMAIN.format(repo_id)
        # TODO: Add HTTPS to cloud node
        cloud_response = requests.get("http://" + cloud_node_url + "/status")
        status_data = cloud_response.json()
        return "ACTIVE" if status_data["Busy"] else "IDLE"
    else:
        statuses = str(statuses)
        raise Exception("Found an unexpected set of statuses: {statuses}")

def _modify_domains(action, names, ip_addresses):
    """
    Create or remove the Route53 domain records with the provided names and
    corresponding public IP addresses.
    
    Args:
        action (str): Action to take. Must be CREATE or DELETE.
        names (list): The list of names of domain records.
        ip_addresses (str): The list of corresponding IP addresses that the
            names point at.
    """
    changes = [_route53_record_change(action, name, ip_address) \
        for name, ip_address in zip(names, ip_addresses)]
    response = route53_client.change_resource_record_sets(
        HostedZoneId=DOMAIN_ID,
        ChangeBatch={"Changes": changes}
    )

def _route53_record_change(action, name, ip_address):
    """
    Form the Route53 record change with the provided action, name and public 
    IP address. 
    
    Args:
        action (str): Action to take. Must be CREATE or DELETE.
        name (str): The name of the domain record. Must end in 
            `.discreetai.com`
        ip_address (str): The corresponding IP address that the name points 
            at.
    
    Returns:
        dict: A dictionary encompassing the details of the Route53 change to
            be made.
    """
    return {
        "Action": action,
        "ResourceRecordSet": {
            "Name": name,
            "Type": "A",
            "TTL": 300,
            "ResourceRecords": [{"Value": ip_address}]
        }
    }

def _make_names(repo_id):
    """
    Helper function to make the domain names with the provided repo ID.
    
    Args:
        repo_id (str): The repo ID corresponding to the repo to make domain
            names for.
    
    Returns:
        list: The list of domain names for this repo ID.
    """
    return [CLOUD_SUBDOMAIN.format(repo_id), EXPLORA_SUBDOMAIN.format(repo_id)]
