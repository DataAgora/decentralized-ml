from __future__ import print_function
import os
import sys
# import git
import shutil
from time import strftime, sleep
import boto3
import zipfile
from botocore.exceptions import ClientError

REPO_URL = "https://github.com/georgymh/decentralized-ml-js"
REPO_PATH = "/tmp/decentralized-ml-js"
ZIP_PATH = '/tmp/cloud-node.zip'

APPLICATION_NAME = "cloud-node"
S3_BUCKET = "cloud-node-deployment"

VERSION_LABEL = strftime("%Y%m%d%H%M%S")
BUCKET_KEY = APPLICATION_NAME + '/' + 'cloudnode_build.zip'

PIPELINE_NAME = 'cloud-node-deploy'


# def upload_to_s3(artifact):
#     """
#     Uploads an artifact to Amazon S3
#     """
#     try:
#         client = boto3.client('s3')
#     except ClientError as err:
#         print("Failed to create boto3 client.\n" + str(err))
#         return False
#
#     try:
#         client.put_object(
#             Body=open(artifact, 'rb'),
#             Bucket=S3_BUCKET,
#             Key=BUCKET_KEY
#         )
#     except ClientError as err:
#         print("Failed to upload artifact to S3.\n" + str(err))
#         return False
#     except IOError as err:
#         print("Failed to access artifact.zip in this directory.\n" + str(err))
#         return False
#
#     return True


# def pre_steps():
#     try:
#         shutil.rmtree(REPO_PATH)
#         shutil.rmtree(ZIP_PATH)
#     except:
#         pass

# def clone_repo():
#     git.exec_command('clone', REPO_URL)
#     return REPO_PATH

# def zip_server_directory():
#     shutil.make_archive(ZIP_PATH.split('.zip')[0], 'zip', REPO_PATH + "/server")
#     return ZIP_PATH


def create_new_version():
    """
    Creates a new application version in AWS Elastic Beanstalk
    """
    try:
        client = boto3.client('elasticbeanstalk')
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False

    try:
        response = client.create_application_version(
            ApplicationName=APPLICATION_NAME,
            VersionLabel=VERSION_LABEL,
            Description='New build',
            SourceBundle={
                'S3Bucket': S3_BUCKET,
                'S3Key': BUCKET_KEY
            },
            Process=True
        )
    except ClientError as err:
        print("Failed to create application version.\n" + str(err))
        return False

    try:
        if response['ResponseMetadata']['HTTPStatusCode'] is 200:
            return True
        else:
            print(response)
            return False
    except (KeyError, TypeError) as err:
        print(str(err))
        return False

def deploy_new_version(env_name):
    """
    Deploy a new version to AWS Elastic Beanstalk
    """
    try:
        client = boto3.client('elasticbeanstalk')
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False

    try:
        response = client.create_environment(
            ApplicationName=APPLICATION_NAME,
            EnvironmentName=env_name,
            VersionLabel=VERSION_LABEL,
            SolutionStackName="64bit Amazon Linux 2018.03 v2.12.10 running Docker 18.06.1-ce",
            OptionSettings=[
                {
                   'ResourceName':'AWSEBLoadBalancer',
                   'Namespace':'aws:elb:listener:80',
                   'OptionName':'InstanceProtocol',
                   'Value':'TCP'
                },
                {
                   'ResourceName':'AWSEBAutoScalingLaunchConfiguration',
                   'Namespace':'aws:autoscaling:launchconfiguration',
                   'OptionName':'SecurityGroups',
                   'Value':'ebs-websocket'
                },
                {
                    'ResourceName': 'AWSEBLoadBalancer',
                    'Namespace': 'aws:elb:listener:80',
                    'OptionName': 'ListenerProtocol' ,
                    'Value': 'TCP'
                },
            ],
        )
    except ClientError as err:
        print("Failed to update environment.\n" + str(err))
        return False

    print(response)
    return True

def deploy_cloud_node(env_name):
    # if not upload_to_s3(ZIP_PATH):
    #     sys.exit(1)
    if not create_new_version():
        raise Exception("Error (creating version)")
    # Wait for the new version to be consistent before deploying
    sleep(5)
    if not deploy_new_version(env_name):
        raise Exception("Error (deploying version)")
    return True


def make_codepipeline_elb_deploy_action(env_name):
    return {
      'name':'deploy-elb-' + env_name,
      'actionTypeId':{
         'category':'Deploy',
         'owner':'AWS',
         'provider':'ElasticBeanstalk',
         'version':'1'
      },
      'runOrder':1,
      'configuration':{
         'ApplicationName':'cloud-node',
         'EnvironmentName':env_name
      },
      'outputArtifacts':[

      ],
      'inputArtifacts':[
         {
            'name':'SourceArtifact'
         }
      ],
      'region':'us-west-1'
   }

def add_codepipeline_deploy_step(env_name):
    try:
        client = boto3.client('codepipeline')
        pipeline_response = client.get_pipeline(
            name=PIPELINE_NAME,
        )

        pipeline_data = pipeline_response['pipeline']
        for stage in pipeline_data['stages']:
            if stage['name'] == 'Deploy':
                new_action = make_codepipeline_elb_deploy_action(env_name)
                stage['actions'].append(new_action)
                _ = client.update_pipeline(
                    pipeline=pipeline_data
                )
                print("Updated CodeDeploy pipeline.")
    except Exception as e:
        # Does not raise an exception since this is not crucial.
        # TODO: Log an error and alert developers because this could break things.
        print("Error: " + str(e))


def run_deploy_routine(repo_id):
    # pre_steps()
    # _ = clone_repo()
    # _ = zip_server_directory()
    _ = deploy_cloud_node(repo_id)
    add_codepipeline_deploy_step(repo_id)
