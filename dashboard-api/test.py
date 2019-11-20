import boto3
from boto3.dynamodb.conditions import Key, Attr

APPLICATION_NAME = "cloud-node"
PIPELINE_NAME = 'cloud-node-deploy'
DEPLOYMENT_NAME = 'deploy-elb-{}'
AWS_REGION = 'us-west-1'

def _get_dynamodb_table(table_name):
    """
    Helper function that returns an AWS DynamoDB table object.
    """
    dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
    table = dynamodb.Table(table_name)
    return table

table_name = "CandidateAuth"
table = _get_dynamodb_table(table_name)

response = table.get_item(
    Key={
        'uuid': '0f0ea682-293d-470b-9981-6f06f017bec5',
    }
)

# items = table.scan()
# print(items)
# print(response)
print('Item' in response)
# print(response['Item'])

# item = response['Item']
# print(item)
# with table.batch_writer() as batch:
#     with open('output.txt', 'r') as f:
#         for uuid in f.readlines():
#             print(uuid.split("\n")[0])
#             batch.put_item(
#                 Item={
#                     'uuid': uuid.split("\n")[0],
#                     'status': False
#                 }
#             )