from __future__ import print_function
import os
import sys
# import git
# import shutil
from time import strftime, sleep
import boto3
from botocore.exceptions import ClientError


CLOUD_CLUSTER_NAME = "default"
CLOUD_TASK_DEFINITION = "first-run-task-definition"
DOMAIN_ID = "/hostedzone/Z3NSW3B4FM6A7X"
CLOUD_SUBDOMAIN = "{}.cloud.discreetai.com"
EXPLORA_SUBDOMAIN = "{}.explora.discreetai.com"

ecs_client = boto3.client("ecs")
ec2_client = boto3.resource("ec2")
route53_client = boto3.client('route53')

def create_new_nodes(repo_id):
    """
    Runs new task (node) for ECS cloud cluster. Sets domain of task to be
    `<repo_id>.cloud.discreetai.com by creating an record in Route53.
    
    Args:
        repo_id (str): The repo ID of the repo this task is to be associated
            with.
    
    Returns:
        dict: A dictionary holding the public IP address and task ARN of the
            newly created cloud task.
    """
    cloud_ip_address, cloud_task_arn = _run_new_task(CLOUD_CLUSTER_NAME, \
        CLOUD_TASK_DEFINITION)
    names = _make_names(repo_id)
    ip_addresses = [cloud_ip_address]
    _modify_domains("CREATE", names, ip_addresses)
    return {
        "CloudIpAddress": cloud_ip_address,
        "CloudTaskArn": cloud_task_arn
    }

def stop_nodes(cloud_task_arn, repo_id, cloud_ip_address):
    """
    Stop the cloud task with its task ARN and remove the corresponding record 
    in Route53.
    
    Args:
        cloud_task_arn (str): The ARN of the cloud task to be stopped.
        repo_id (str): The repo ID of the repo associated with this task.
        cloud_ip_address (str): The public IP address of the cloud task. 
    """
    _stop_task(CLOUD_CLUSTER_NAME, cloud_task_arn)
    names = _make_names(repo_id)
    ip_addresses = [cloud_ip_address]
    _modify_domains("DELETE", names, ip_addresses)

def _create_new_task(cluster_name, task_definition):
    """
    Run new task in the provided cluster with the provided task definition.
    
    Args:
        cluster_name (str): The name of the cluster to run the task in.
        task_definition (str): The name of the schema of the task to be run.
    
    Returns:
        str: The task ARN of the newly created task.
    """
    new_task_response = ecs_client.run_task(
        cluster=cluster_name,
        taskDefinition=task_definition,
        launchType="FARGATE",
        networkConfiguration = {
            "awsvpcConfiguration": {
                "subnets": ["subnet-066927cc2aa7d231f"],
                "assignPublicIp": "ENABLED",
            }
        }
    )
    if new_task_response["failures"]:
        raise Exception(str(new_task_response["failures"]))
    task_arn = new_task_response["tasks"][0]["taskArn"]

    return task_arn

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

def _run_new_task(cluster_name, task_definition):
    """
    Run new task in the provided cluster with the provided task definition.
    
    Args:
        cluster_name (str): The name of the cluster to run the task in.
        task_definition (str): The name of the schema of the task to be run.
    
    Returns:
        (str, str): The task ARN and public IP address of the newly created 
            task.
    """
    task_arn = _create_new_task(cluster_name, task_definition)
    network_interface_id = _get_network_interface_id(task_arn)
    ip_address = _get_public_ip(network_interface_id)
    return ip_address, task_arn

def _stop_task(cluster_name, task_arn):
    """
    Stop task in the provided cluster with the provided task ARN.
    
    Args:
        cluster_name (str): The name of the cluster to run the task in.
        task_arn (str): The ARN of the task to be stopped.
    """
    _ = ecs_client.stop_task(
        cluster=cluster_name,
        task=task_arn,
        reason="User requested deletion."
    )

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
    return [CLOUD_SUBDOMAIN.format(repo_id)]