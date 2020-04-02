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
    cloud_ip_address, cloud_task_arn = _run_new_task(CLOUD_CLUSTER_NAME, \
        CLOUD_TASK_DEFINITION)
    names = _make_names(repo_id)
    ip_addresses = [cloud_ip_address]
    _modify_domains("CREATE", names, ip_addresses)
    return {
        "CloudIpAddress": cloud_ip_address,
        "CloudTaskArn": cloud_task_arn
    }

def stop_nodes(task_arn, repo_id, cloud_ip_address):
    _stop_task(CLOUD_CLUSTER_NAME, task_arn)
    names = _make_names(repo_id)
    ip_addresses = [cloud_ip_address]
    _modify_domains("DELETE", names, ip_addresses)

def _create_new_task(cluster_name, task_definition):
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
    network_interface = ec2_client.NetworkInterface(network_interface_id)
    ip_address_details = network_interface.private_ip_addresses[0]
    if "Association" not in ip_address_details:
        sleep(1)
        return _get_public_ip(network_interface_id)
    ip_address = ip_address_details["Association"]["PublicIp"]
    return ip_address

def _run_new_task(cluster_name, task_definition):
    task_arn = _create_new_task(cluster_name, task_definition)
    network_interface_id = _get_network_interface_id(task_arn)
    ip_address = _get_public_ip(network_interface_id)
    return ip_address, task_arn

def _stop_task(cluster_name, task_arn):
    _ = ecs_client.stop_task(
        cluster=cluster_name,
        task=task_arn,
        reason="User requested deletion."
    )

def _modify_domains(action, names, ip_addresses):
    changes = [_route53_record(action, name, ip_address) \
        for name, ip_address in zip(names, ip_addresses)]
    response = route53_client.change_resource_record_sets(
        HostedZoneId=DOMAIN_ID,
        ChangeBatch={"Changes": changes}
    )

def _route53_record(action, name, ip_address):
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
    return [CLOUD_SUBDOMAIN.format(repo_id)]