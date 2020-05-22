import os
import sys
import json
import requests
from time import strftime, sleep

import boto3
from botocore.exceptions import ClientError

from dynamodb import _get_demo_cloud_domain, _get_demo_api_key


CLUSTER_NAME = "default"
CLOUD_SUBDOMAIN = "{}.cloud.discreetai.com"
EXPLORA_SUBDOMAIN = "{}.explora.discreetai.com"
EXPLORA_URL = "{0}.explora.discreetai.com/?token={1}"
DEMO_CLOUD_DOMAIN = "{}.cloud.discreetai.com"
TASK_DETAILS = {
    "cloud": ("cloud-task-definition", "cloud-container", \
        CLOUD_SUBDOMAIN),
    "explora": ("explora-task-definition", "explora-container", \
        EXPLORA_SUBDOMAIN)
}
DOMAIN_ID = "/hostedzone/Z3NSW3B4FM6A7X"
DEPLOYING_STATUSES = ["PROVISIONING", "PENDING", "ACTIVATING"]
RUNNING_STATUS = "RUNNING"
SHUTTING_DOWN_STATUSES = ["DEACTIVATING", "STOPPING", "DEPROVISIONING"]
ERROR_STATUS = "STOPPED"

ecs_client = boto3.client("ecs")
ec2_client = boto3.resource("ec2")
route53_client = boto3.client('route53')

def create_new_nodes(repo_id, api_key, token, is_demo):
    """
    Runs new tasks (Explora + cloud) for ECS cluster. Sets domain of task to 
    be `<repo_id>.cloud.discreetai.com by creating an record in Route53.
    
    Args:
        repo_id (str): The repo ID of the repo this task is to be associated
            with.
        api_key (str): The corresponding API key of the repo. Used for auth in
            the tasks.
        is_demo (bool): Boolean for whether this repo is a demo repo or not.
    
    Returns:
        dict: A dictionary holding the public IP address and task ARN of the
            newly created cloud and Explora task.
    """
    results = {"ApiKey": api_key, "IsDemo": is_demo, \
        "Token": token, "ExploraUrl": EXPLORA_URL.format(repo_id, token)}

    for name, details in TASK_DETAILS.items():
        if is_demo and name == "cloud":
            with open("demo_cloud_details.json", "r") as f:
                results.update(json.load(f))
            continue
        task_definition, container_name, subdomain = details
        task_arn, ip_address = _run_new_task(task_definition, container_name, \
            repo_id, api_key, token, subdomain)
        results[name.capitalize() + "IpAddress"] = ip_address
        results[name.capitalize() + "TaskArn"] = task_arn
    
    return results

def stop_nodes(task_arns, ip_addresses, repo_id, is_demo):
    """
    Stop the cloud and Explora task with its task ARN and remove the 
    corresponding record in Route53.
    
    Args:
        task_arns (list): The ARN of the tasks to be stopped.
        repo_id (str): The repo ID of the repo associated with this task.
        ip_addresses (list): The public IP addresses of the tasks.
        is_demo (bool): Boolean for whether this repo is a demo repo or not.
    """
    subdomains = [EXPLORA_SUBDOMAIN] \
        if is_demo else [CLOUD_SUBDOMAIN, EXPLORA_SUBDOMAIN]

    for task_arn, subdomain, ip_address in zip(task_arns, subdomains, \
            ip_addresses):
        domain = subdomain.format(repo_id)
        _stop_task(task_arn, domain, ip_address)

def get_status(task_arns, repo_id, is_demo):
    """
    Retrieve the statuses of the cloud and Explora task and form a general
    status. 
    
    Args:
        task_arns (list): The ARN of the tasks whose statuses are needed.
        repo_id (str): The repo ID of the repo associated with this task.
        is_demo (bool): Boolean for whether this repo is a demo repo or not.
    
    Returns:
        str: The general status describing the state of both the tasks.
    """
    statuses = _retrieve_statuses(task_arns)
    return _determine_status(statuses, repo_id, is_demo)

def wait_until_next_available_repo(repos):
    for repo_details in repos:
        status = get_status([repo_details["ExploraTaskArn"]], \
            repo_details["Id"], True)
        if status == "AVAILABLE":
            return repo_details
    sleep(5)
    return wait_until_next_available_repo(repos)

def reset_cloud_node(repo_id, is_demo):
    """
    Reset the cloud node with the given repo ID.

    Args:
        repo_id (str): The repo ID of the repo associated with this task.
        is_demo (bool): Boolean for whether this repo is a demo repo or not.
    """
    demo_domain = _get_demo_cloud_domain()
    cloud_node_url = DEMO_CLOUD_DOMAIN.format(demo_domain) \
        if is_demo else CLOUD_SUBDOMAIN.format(repo_id)
    # TODO: Add HTTPS to cloud node
    cloud_response = requests.get("http://{0}/status/{1}".format(cloud_node_url, repo_id))

def update_cloud_demo_node():
    """
    Update the demo cloud node with the latest Docker image.
    """
    try:
        delete_demo_node()
    except Exception as e:
        print(str(e))
    return create_demo_node()

def _run_new_task(task_definition, container_name, repo_id, api_key, \
        token, subdomain):
    """
    Run new task in the provided cluster with the provided task definition.
    
    Args:
        task_definition (str): Task definition of the task to be run.
        container_name (str): Name of the Docker container to run in the task.
        repo_id (str): The repo ID of the repo associated with this task.
        api_key (str): The corresponding API key of the repo. Used for auth in
            the tasks.
        subdomain (str): The name of the subdomain to create the domain at.
    
    Returns:
        (str, str): The task ARN and public IP address of the newly created 
            task.
    """
    new_task_response = ecs_client.run_task(
        cluster=CLUSTER_NAME,
        taskDefinition=task_definition,
        launchType="FARGATE",
        networkConfiguration = {
            "awsvpcConfiguration": {
                "subnets": ["subnet-066927cc2aa7d231f"],
                "assignPublicIp": "ENABLED",
            }
        },
        overrides = {
            "containerOverrides": [{
                "name": container_name,
                "environment": [{
                    "name": "REPO_ID",
                    "value": repo_id
                }, {
                    "name": "DEMO_REPO_ID",
                    "value": _get_demo_cloud_domain(),
                }, {
                    "name": "API_KEY",
                    "value": api_key,
                }, {
                    "name": "DEMO_API_KEY",
                    "value": _get_demo_api_key(),
                }, {
                    "name": "TOKEN",
                    "value": token,
                }]
            }]
        }
    )

    if new_task_response["failures"]:
        raise Exception(str(new_task_response["failures"]))

    task_arn = new_task_response["tasks"][0]["taskArn"]
    network_interface_id = _get_network_interface_id(task_arn)
    ip_address = _get_public_ip(network_interface_id)
    
    full_domain = subdomain.format(repo_id)
    _modify_domain("CREATE", full_domain, ip_address)

    return task_arn, ip_address

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

def _stop_task(task_arn, domain, ip_address):
    """
    Stop cloud and Explora task with the provided task ARNs.
    
    Args:
        cloud_task_arn (str): The ARN of the cloud task to be stopped.
        explora_task_arn (str): The ARN of the Explora task to be stopped.
    """
    _ = ecs_client.stop_task(
        cluster=CLUSTER_NAME,
        task=task_arn,
        reason="User requested deletion."
    )

    _modify_domain("DELETE", domain, ip_address)

def _retrieve_statuses(task_arns):
    """
    Retrieve the actual task statuses from the cloud and Explora tasks.
    
    Args:
        task_arns (list): The ARN of the tasks whose statuses are needed.
    
    Returns:
        str: The actual task statuses of the two tasks.
    """
    describe_response = ecs_client.describe_tasks(
        cluster=CLUSTER_NAME,
        tasks=task_arns,
    )
    return [task["containers"][0]["lastStatus"] \
        for task in describe_response["tasks"]]

def _determine_status(statuses, repo_id, is_demo):
    """
    Determine the general status given the actual two task statuses of the
    cloud and Explora tasks.

    For example, as long as one task is deploying/shutting down/shut down, both
    are considered deploying/shutting down/shut down. 
    
    Args:
        statuses (list): The two task statuses of the cloud and Explora tasks.
        repo_id (str): The repo ID of the repo associated with this task.
        is_demo (bool): Boolean for whether this repo is a demo repo or not.
    
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
        demo_domain = _get_demo_cloud_domain()
        cloud_node_url = DEMO_CLOUD_DOMAIN.format(demo_domain) \
            if is_demo else CLOUD_SUBDOMAIN.format(repo_id)
        # TODO: Add HTTPS to cloud node
        cloud_response = requests.get("http://{0}/status/{1}".format(cloud_node_url, repo_id))
        status_data = cloud_response.json()
        return "ACTIVE" if status_data["Busy"] else "AVAILABLE"
    else:
        statuses = str(statuses)
        raise Exception("Found an unexpected set of statuses: {statuses}")

def _modify_domain(action, name, ip_address):
    """
    Create or remove the Route53 domain records with the provided names and
    corresponding public IP addresses.
    
    Args:
        action (str): Action to take. Must be CREATE or DELETE.
        name (list): The name of the domain record to modify.
        ip_address (str): The IP address corresponding to the name.
    """
    change = _route53_record_change(action, name, ip_address)
    response = route53_client.change_resource_record_sets(
        HostedZoneId=DOMAIN_ID,
        ChangeBatch={"Changes": [change]}
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

def create_demo_node():
    """
    Create the demo cloud node.
    """
    name = "cloud"
    details = TASK_DETAILS[name]
    task_definition, container_name, subdomain = details
    demo_domain = _get_demo_cloud_domain()
    full_domain = DEMO_CLOUD_DOMAIN.format(demo_domain)
    demo_api_key = _get_demo_api_key()
    task_arn, ip_address = _run_new_task(task_definition, container_name, \
        demo_domain, demo_api_key, "", CLOUD_SUBDOMAIN)
    results = {
        "CloudIpAddress": ip_address,
        "CloudTaskArn": task_arn
    }
    with open("demo_cloud_details.json", "w") as f:
        json.dump(results, f)

    return results

def delete_demo_node():
    """
    Deletes the demo cloud node.
    """
    demo_domain = _get_demo_cloud_domain()
    full_domain = DEMO_CLOUD_DOMAIN.format(demo_domain)

    with open("demo_cloud_details.json", "r") as f:
        details = json.load(f)
        ip_address = details["CloudIpAddress"]
        task_arn = details["CloudTaskArn"]
        _stop_task(task_arn, full_domain, ip_address)
