from __future__ import print_function
import os
import sys
# import git
# import shutil
from time import strftime, sleep
import boto3
from botocore.exceptions import ClientError

# REPO_URL = "https://github.com/georgymh/decentralized-ml-js"
# REPO_PATH = "/tmp/decentralized-ml-js"
# ZIP_PATH = '/tmp/cloud-node.zip'

APPLICATION_NAME = "cloud-node"
S3_BUCKET = "cloud-node-deployment"
AWS_REGION = 'us-west-1'

BUCKET_KEY = APPLICATION_NAME + '/' + 'cloudnode_build.zip'
DEPLOYMENT_NAME = 'deploy-elb-{}'
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
#     """
#     Removes temporary folders.
#     """
#     try:
#         shutil.rmtree(REPO_PATH)
#         shutil.rmtree(ZIP_PATH)
#     except:
#         pass

# def clone_repo():
#     """
#     Clones the repo locally.
#     """
#     git.exec_command('clone', REPO_URL)
#     return REPO_PATH

# def zip_server_directory():
#     """
#     Zips the cloned repo so it can be uploaded to S3.
#     """
#     shutil.make_archive(ZIP_PATH.split('.zip')[0], 'zip', REPO_PATH + "/server")
#     return ZIP_PATH


def create_new_version(version_label):
    """
    Helper function that creates a new application version of an environment in
    AWS Elastic Beanstalk.
    """
    try:
        client = boto3.client('elasticbeanstalk')
    except ClientError as err:
        raise Exception("Failed to create boto3 client.\n" + str(err))

    try:
        response = client.create_application_version(
            ApplicationName=APPLICATION_NAME,
            VersionLabel=version_label,
            Description='New build',
            SourceBundle={
                'S3Bucket': S3_BUCKET,
                'S3Key': BUCKET_KEY
            },
            Process=True
        )
    except ClientError as err:
        raise Exception("Failed to create application version.\n" + str(err))

    try:
        if response['ResponseMetadata']['HTTPStatusCode'] is 200:
            return True, "success"
        else:
            raise Exception("Response did not return 200. Response: \n" + str(response))
    except (KeyError, TypeError) as err:
        raise Exception(str(err))

def deploy_new_version(env_name, version_label):
    """
    Helper function to deploy a created version of the environment to AWS
    Elastic Beanstalk.

    This needs to run after `create_new_version()`.
    """
    try:
        client = boto3.client('elasticbeanstalk')
    except ClientError as err:
        raise Exception("Failed to create boto3 client.\n" + str(err))

    try:
        response = client.create_environment(
            ApplicationName=APPLICATION_NAME,
            EnvironmentName=env_name,
            VersionLabel=version_label,
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
        raise Exception("Failed to update environment.\n" + str(err))

    return response

def deploy_cloud_node(env_name):
    """
    Creates and then deploys a new version of the Cloud Node to AWS Elastic
    Beanstalk.
    """
    # if not upload_to_s3(ZIP_PATH):
    #     sys.exit(1)
    version_label = strftime("%Y%m%d%H%M%S")
    _ = create_new_version(version_label)
    # Wait for the new version to be consistent before deploying
    sleep(5)
    _ = deploy_new_version(env_name, version_label)
    return True


def make_codepipeline_elb_deploy_action(env_name):
    """
    Crafts a Deployment Action for AWS CodePipeline in JSON format.
    """
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
         'ApplicationName': APPLICATION_NAME,
         'EnvironmentName': env_name
      },
      'outputArtifacts':[

      ],
      'inputArtifacts':[
         {
            'name':'SourceArtifact'
         }
      ],
      'region': AWS_REGION
   }

def add_codepipeline_deploy_step(env_name):
    """
    Makes a Cloud Node self-updateable by updating the AWS CodePipeline
    pipeline.
    """
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
        raise Exception("Error adding deploy step: " + str(e))

    return True


def run_deploy_routine(repo_id):
    """
    Runs the Deploy routine
    """
    # pre_steps()
    # _ = clone_repo()
    # _ = zip_server_directory()
    _ = deploy_cloud_node(repo_id)
    _ = add_codepipeline_deploy_step(repo_id)

def _delete_cloud_node(repo_id):
    """
    Deletes cloud node
    """
    try:
        client = boto3.client('elasticbeanstalk')
    except ClientError as err:
       raise Exception("Failed to create boto3 client.\n" + str(err))

    try:
        response = client.terminate_environment(
            EnvironmentName=repo_id,
            TerminateResources=True,
        )

        return response
    except ClientError as err:
        raise Exception("Failed to delete environment.\n" + str(err))

def _remove_codepipeline_deploy_step(env_name):
    """
    Removes Cloud Node from the AWS CodePipeline pipeline.
    """
    try:
        target_name = DEPLOYMENT_NAME.format(env_name)
        client = boto3.client('codepipeline')
        pipeline_response = client.get_pipeline(
            name=PIPELINE_NAME,
        )

        pipeline_data = pipeline_response['pipeline']
        for stage in pipeline_data['stages']:
            if stage['name'] == 'Deploy':
                stage['actions'] = [action for action in stage['actions'] \
                                    if action['name'] != target_name]
                _ = client.update_pipeline(
                    pipeline=pipeline_data
                )
                print("Updated CodeDeploy pipeline.")

                return True
    except Exception as e:
        raise Exception("Error removing deploy step: " + str(e))

def run_delete_routine(repo_id):
    """
    Runs delete cloud node routine
    """
    _ = _delete_cloud_node(repo_id)
    _ = _remove_codepipeline_deploy_step(repo_id)
