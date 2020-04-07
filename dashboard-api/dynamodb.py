import time
import decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr


dynamodb_client = boto3.resource('dynamodb', region_name='us-west-1')

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
                        'Timestamp': item['Timestamp']
                    }
                )
        print("Successfully deleted logs!")
        return True
    except Exception as e:
        raise Exception("Error while getting logs for repo. " + str(e))

def _get_user_data(user_id):
    """
    Returns the user's data.
    """
    table = _get_dynamodb_table("UsersDashboardData")
    try:
        response = table.get_item(
            Key={
                "UserId": user_id,
            }
        )
        data = response["Item"]
    except:
        raise Exception("Error while getting user dashboard data.")
    return data

def _remove_repo_from_user_details(user_id, repo_id, api_key):
    """
    Upon removing a repo, remove the repo from the user's details.
    """
    table = _get_dynamodb_table("UsersDashboardData")
    try:
        response = table.get_item(
            Key={
                "UserId": user_id,
            }
        )
        data = response["Item"]
        repos_managed = data['ReposManaged']
        api_keys = data['ApiKeys']
        if repo_id in repos_managed and api_key in api_keys:
            repos_managed.remove(repo_id)
            api_keys.remove(api_key)
            if len(repos_managed) == 0:
                data.pop('ReposManaged')
                data.pop('ApiKeys')
            data['ReposRemaining'] += 1
            table.put_item(
                Item=data
            )
            print("Successfully removed repo_id from user details!")
            return True
        else:
            raise Exception("Could not find corresponding API key or repo id!")
    except Exception as e:
        raise Exception("Error while removing user dashboard data: " + str(e))

def _get_repo_details(user_id, repo_id):
    """
    Returns a repo's details.
    """
    repos_table = _get_dynamodb_table("Repos")
    try:
        response = repos_table.get_item(
            Key={
                "Id": repo_id,
                "OwnerId": user_id,
            }
        )
        repo_details = response["Item"]
    except:
        raise Exception("Error while getting repo details.")
    return repo_details

def _remove_repo_details(user_id, repo_id):
    """
    Removes a repo's details.
    """
    repos_table = _get_dynamodb_table("Repos")
    try:
        response = repos_table.delete_item(
            Key={
                "Id": repo_id,
                "OwnerId": user_id,
            }
        )
        print("Removed repo details!")
        return True
    except:
        raise Exception("Error while getting repo details.")


def _update_user_data_with_new_repo(user_id, repo_id, api_key):
    """
    Updates a user with a new repo and its metadata.
    """
    table = _get_dynamodb_table("UsersDashboardData")
    try:
        response = table.get_item(
            Key={
                "UserId": user_id,
            }
        )
        data = response["Item"]

        repos_managed = data.get('ReposManaged', set([]))
        api_keys = data.get('ApiKeys', set([]))

        repos_managed.add(repo_id)
        api_keys.add(api_key)

        response = table.update_item(
            Key={
                'UserId': user_id,
            },
            UpdateExpression="SET ReposRemaining = ReposRemaining - :val, ReposManaged = :val2, ApiKeys = :val3",
            ExpressionAttributeValues={
                ':val': decimal.Decimal(1),
                ':val2': repos_managed,
                ':val3': api_keys,
            }
        )
    except Exception as e:
        raise Exception("Error while updating user data with new repo data: " + str(e))

def _create_new_repo_document(user_id, repo_id, repo_name, repo_description, \
        server_details):
    """
    Creates a new repo document in the DB.
    """
    table = _get_dynamodb_table("Repos")
    try:
        item = {
            'Id': repo_id,
            'Name': repo_name,
            'Description': repo_description,
            'OwnerId': user_id,
            'ContributorsId': [],
            'CoordinatorAddress': CLOUD_SUBDOMAIN.format(repo_id),
            'CreatedAt': int(time.time()),
            'creds': 'N/A'
        }
        item.update(server_details)
        table.put_item(Item=item)
    except:
        raise Exception("Error while creating the new repo document.")
    return repo_id

def _get_all_repos(user_id):
    """
    Returns all repos for a user.
    """
    try:
        user_data = _get_user_data(user_id)
        repos_managed = user_data.get('ReposManaged', 'None')

        repos_table = _get_dynamodb_table("Repos")
        all_repos = []
        for repo_id in repos_managed:
            if repo_id == "null": continue
            response = repos_table.get_item(
                Key={
                    "Id": repo_id,
                    "OwnerId": user_id,
                }
            )

            if 'Item' in response:
                all_repos.append(response['Item'])
    except:
        raise Exception("Error while getting all repos.")
    return all_repos

def _get_dynamodb_table(table_name):
    """
    Helper function that returns an AWS DynamoDB table object.
    """
    table = dynamodb_client.Table(table_name)
    return table
