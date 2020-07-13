import time
import decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr


DEFAULT_USERNAME = "default"
dynamodb_client = boto3.resource('dynamodb', region_name='us-west-1')


def _register_user(username, password):
    table = _get_dynamodb_table("UsersDashboardData")
    try:
        data = {
            "Username": username,
            "Password": password,
            "ReposRemaining": 3,
        }
        table.put_item(Item=data)
    except Exception as e:
        raise Exception("Error while registering user dashboard data: " + str(e))

def _get_user_data(username):
    """
    Returns the user's data.
    """
    table = _get_dynamodb_table("UsersDashboardData")
    try:
        response = table.get_item(
            Key={
                "Username": username,
            }
        )
        data = response["Item"]
    except Exception as e:
        raise Exception("Error while getting user dashboard data: " + str(e))
    return data

def _update_user_data_with_new_repo(username, repo_id):
    """
    Updates a user with a new repo and its metadata.
    """
    table = _get_dynamodb_table("UsersDashboardData")
    try:
        data = _get_user_data(username)

        repos_managed = data.get('ReposManaged', set([]))
        repos_managed.add(repo_id)

        response = table.update_item(
            Key={
                "Username": username,
            },
            UpdateExpression="SET ReposRemaining = ReposRemaining - :val, ReposManaged = :val2",
            ExpressionAttributeValues={
                ':val': decimal.Decimal(1),
                ':val2': repos_managed
            }
        )
    except Exception as e:
        raise Exception("Error while updating user data with new repo data: " + str(e))

def _remove_repo_from_user_details(username, repo_id):
    """
    Upon removing a repo, remove the repo from the user's details.
    """
    table = _get_dynamodb_table("UsersDashboardData")
    try:
        data = _get_user_data(username)
        repos_managed = data['ReposManaged']
        if repo_id in repos_managed:
            repos_managed.remove(repo_id)
            if len(repos_managed) == 0:
                data.pop('ReposManaged')
            data['ReposRemaining'] += 1
            table.put_item(
                Item=data
            )
        else:
            raise Exception("Could not find corresponding repo ID!")
    except Exception as e:
        raise Exception("Error while removing user dashboard data: " + str(e))

def _create_new_repo_document_from_item(item):
    """
    Creates a new repo document in the DB.
    """
    table = _get_dynamodb_table("Repos")
    try:
        table.put_item(Item=item)
    except Exception as e:
        raise Exception("Error while creating the new repo document: " + str(e))

def _create_new_repo_document(username, repo_id, repo_name, repo_description, \
        server_details, is_demo):
    """
    Creates a new repo document in the DB.
    """
    table = _get_dynamodb_table("Repos")
    try:
        item = {
            'Id': repo_id,
            'Name': repo_name,
            'Description': repo_description,
            'OwnerId': username,
            'CreatedAt': int(time.time()),
            'IsDemo': is_demo,
        }
        item.update(server_details)
        table.put_item(Item=item)
    except Exception as e:
        raise Exception("Error while creating the new repo document: " + str(e))
    return repo_id

def _get_repo_details(username, repo_id):
    """
    Returns a repo's details.
    """
    repos_table = _get_dynamodb_table("Repos")
    try:
        response = repos_table.get_item(
            Key={
                "Id": repo_id,
                "OwnerId": username,
            }
        )
        repo_details = response["Item"]
    except Exception as e:
        raise Exception("Error while getting repo details: " + str(e))
    return repo_details

def _remove_repo_details(username, repo_id):
    """
    Removes a repo's details.
    """
    repos_table = _get_dynamodb_table("Repos")
    try:
        response = repos_table.delete_item(
            Key={
                "Id": repo_id,
                "OwnerId": username,
            }
        )
        print("Removed repo details!")
        return True
    except Exception as e:
        raise Exception("Error while getting repo details: " + str(e))

def _get_all_repos(username):
    """
    Returns all repos for a user.
    """
    try:
        user_data = _get_user_data(username)
        repos_managed = user_data.get('ReposManaged', set([]))

        repos_table = _get_dynamodb_table("Repos")
        all_repos = []
        for repo_id in repos_managed:
            if repo_id == "null": continue
            response = repos_table.get_item(
                Key={
                    "Id": repo_id,
                    "OwnerId": username,
                }
            )

            if 'Item' in response:
                all_repos.append(response['Item'])
    except:
        raise Exception("Error while getting all repos.")
    return all_repos

def _get_logs(repo_id):
    """
    Returns the logs for a repo.
    """
    logs_table = _get_dynamodb_table("UpdateStore")
    try:
        response = logs_table.query(
            KeyConditionExpression=Key('RepoId').eq(repo_id) \
                & Key('ExpirationTime').gt(int(time.time())) 
        )
        logs = response["Items"]
    except Exception as e:
        raise Exception("Error while getting logs for repo. " + str(e))
    return logs

def _remove_logs(repo_id):
    """
    Removes the logs for a repo.
    """
    logs_table = _get_dynamodb_table("UpdateStore")
    try:
        response = logs_table.query(
            KeyConditionExpression=Key('RepoId').eq(repo_id)
        )
        with logs_table.batch_writer() as batch:
            for item in response["Items"]:
                batch.delete_item(
                    Key={
                        'RepoId': item['RepoId'],
                        'ExpirationTime': item['ExpirationTime']
                    }
                )
        print("Successfully deleted logs!")
        return True
    except Exception as e:
        raise Exception("Error while getting logs for repo. " + str(e))

def _get_all_users_repos():
    """
    Helper function get all tuples of (username, repo_id).
    """
    users_table = _get_dynamodb_table("UsersDashboardData")
    try:
        users = users_table.scan()["Items"]
        repos = []
        for user in users:
            username = user["Username"]
            password = user["Password"]
            if "ReposManaged" not in user:
                continue
            for repo_id in user["ReposManaged"]:
                repos.append((username, password, repo_id))
        return repos
    except Exception as e:
        raise Exception("Error getting repos for all users. " + str(e))

def _get_demo_cloud_domain():
    """
    Helper function to get the demo API key.
    """
    return _get_repo_details("demo", "cloud-demo")["CloudDomain"]

def _get_demo_api_key():
    """
    Helper function to get the demo API key.
    """
    return _get_repo_details("demo", "cloud-demo")["ApiKey"]

def _get_dynamodb_table(table_name):
    """
    Helper function that returns an AWS DynamoDB table object.
    """
    table = dynamodb_client.Table(table_name)
    return table
