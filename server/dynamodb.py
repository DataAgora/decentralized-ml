import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
import logging

class DB(object):
    '''
    DynamoDB class used to manage two tables.

    'jupyterhub-users' (users_table) maps usernames to whether they are in use or not
    'Repos' (repos_table) maps repo_ids to usernames (N/A if no username mapping exists yet) 
    '''
    def __init__(self):
        '''
        Set up DB and tables.
        '''
        access_key = os.environ["AWS_ACCESS_KEY_ID"]
        secret_key = os.environ["AWS_SECRET_ACCESS_KEY"]
        self.dynamodb = boto3.resource('dynamodb', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name='us-west-1')
        self.users_table = self.dynamodb.Table('jupyterhub-users')
        self.repos_table = self.dynamodb.Table('Repos')
    
    def create_table(self):
        '''
        Recreate users table (ONLY TO BE USED AFTER DELETING)
        '''
        self.users_table = self.dynamodb.create_table(
            TableName='jupyterhub-users',
            KeySchema=[
                {
                    'AttributeName': 'username',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'repo_id',
                    'KeyType': 'SORT'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'username',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'repo_id',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        table.meta.client.get_waiter('table_exists').wait(TableName='jupyterhub-users')

    def delete_table(self):
        '''
        Delete the users table
        '''
        self.users_table.delete()
        self.users_table = None

    def add_user(self, username, batch=None):
        '''
        Add a single user to the users table
        '''
        if not batch:
            batch = self.users_table
        assert batch != None, "Table not initialized!"
        batch.put_item(
            Item={
                'username': username,
                'in_use': False
            }
        )

    def add_multiple_users(self, usernames):
        '''
        Add multiple users in a single batch update
        '''
        with self.users_table.batch_writer() as batch:
            for username in usernames:
                self.add_user(username, batch=batch)


    def get_username(self, user_id, repo_id):
        '''
        Get username for given repo_id. If a username doesn't exist for this repo, retrieve an 
        available username and make it unavailable for other repos.
        '''
        creds = self._get_creds(user_id, repo_id)
        if creds != 'N/A':
            return creds
        return self._get_next_available_username(user_id, repo_id)

    def _get_next_available_username(self, user_id, repo_id):
        '''
        Retrieve next available username and make it unavailable for other repos.
        '''
        response = self.users_table.scan(
            FilterExpression=Attr('in_use').eq(False)
        )
        items = response['Items']
        assert items, "No more usernames available!"
        self._set_user_creds(user_id, repo_id, items[0]['username'])
        self._set_creds_in_use(items[0]['username'], True)
        return items[0]['username']

    def _set_user_creds(self, user_id, repo_id, username):
        '''
        Set username for given repo_id
        '''
        self.repos_table.update_item(
            Key={
                'Id': repo_id,
                'OwnerId': user_id
            },
            UpdateExpression='SET creds = :val1',
            ExpressionAttributeValues={
                ':val1': username
            }
        )

    def _set_creds_in_use(self, username, in_use):
        '''
        Set the 'in_use' boolean for this username
        '''              
        self.users_table.update_item(
            Key={
                'username': username,
            },
            UpdateExpression='SET in_use = :val1',
            ExpressionAttributeValues={
                ':val1': in_use
            }
        )

    def _get_creds(self, user_id, repo_id):
        '''
        Get username for given repo_id (N/A if it doesn't exist)
        '''
        response = self.repos_table.get_item(
            Key={
                'Id': repo_id,
                'OwnerId': user_id
            }
        )
        item = response['Item']
        return item['creds']