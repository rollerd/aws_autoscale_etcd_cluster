import requests
import sys
import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

etcd_existing_cluster_launch_config = 'etcd_existing_cluster_launch_config'


def add_etcd_member(available_etcd_instance_ip_list, private_ip):
    '''
    Does the actual work of querying the cluster and adding the instance
    '''
    payload = {"peerURLs":["http://{0}:2380".format(private_ip)]}
    for ip in available_etcd_instance_ip_list:
        try:
            r = requests.post("http://{0}:2379/v2/members".format(ip), json=payload, timeout=1)
            logger.debug("add_etcd_member: ETCD MEMBER IP ({0}) POST RESULT: {1}".format(ip, r.text))
            if r.status_code == 200:
                break
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as err:
            logger.warn("ERROR: {0}".format(err))
            pass

    return 0
    
            
def remove_etcd_member(available_instance_ip_list, terminating_instance_name):
    '''
    Does the actual work of querying the etcd cluster and removing the instance
    '''
    for ip in available_instance_ip_list: # Work through list of available autoscaling group instance IPs to try and find an active etcd cluster member
        try:
            r = requests.get("http://{0}:2379/v2/members".format(ip), timeout=1) # We query instance IPs for cluster member info
            etcd_member_dict = json.loads(r.text)
            logger.debug("remove_etcd_member: ETCD MEMBER DICT: {0}".format(etcd_member_dict))
            available_instance_ip = ip # We have a reponse and record this instances IP for performing the removal later
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as err:
            logger.error("ERROR(passing): {0}".format(err))
            pass # log issue but continue processing IPs

    member_id_to_remove = None
    for member in etcd_member_dict["members"]: # Figure out the etcd id for the member we want to remove
        if member["name"] == terminating_instance_name:
            member_id_to_remove = member["id"]
            break

    if member_id_to_remove:
        r = requests.delete("http://{0}:2379/v2/members/{1}".format(available_instance_ip, member_id_to_remove))
        logger.debug("remove_etcd_member: ETCD CLUSTER RESPONSE: instance_name: {0} status: {1} msg: {2}".format(terminating_instance_name, r.status_code, r.text))
    else: # Its possible the terminated instance was not a full etcd cluster member
        return 2

    if r.status_code in [200, 204, 410]:
        logger.info("REMOVED CLUSTER MEMBER")
        return 0

    return 1


def id_to_ip(instance_id):
    '''
    Given an ec2 autoscaling instance ID, return the IP for that instance or None if none exist
    '''
    ec2_client, autoscaling_client = get_boto_clients()
    instance_data = ec2_client.describe_instances(Filters=[{"Name": "instance-id", "Values": [instance_id]}])
    logger.debug("id_to_ip: INSTANCE_DATA: {0}".format(instance_data))
    private_ip = instance_data["Reservations"][0]["Instances"][0].get("PrivateIpAddress", None)

    return private_ip


def complete_lifecycle_hook(message):
    '''
    Let autoscaling group know that it can continue with scale in/out request
    '''
    ec2_client, autoscaling_client = get_boto_clients()
    response = autoscaling_client.complete_lifecycle_action(LifecycleHookName=message["LifecycleHookName"], 
                                                            AutoScalingGroupName=message["AutoScalingGroupName"], 
                                                            LifecycleActionToken=message["LifecycleActionToken"], 
                                                            LifecycleActionResult="CONTINUE")

    logger.info("complete_lifecycle_hook: RESPONSE={0}".format(response))


def get_autoscaling_group_ips(message):
    '''
    Collect autoscaling group instance data and return list of instance IPs
    '''
    ec2_client, autoscaling_client = get_boto_clients()

    autoscaling_instance_data = autoscaling_client.describe_auto_scaling_instances() # Get the info for all instances in autoscaling groups

    all_autoscaling_instances_list = autoscaling_instance_data["AutoScalingInstances"] # Pull out the instance data
    logger.debug("get_autoscaling_group_ips: ALL_AUTOSCALING INSTANCES_LIST: {0}".format(all_autoscaling_instances_list))
#    print(all_autoscaling_instances_list)
    group_instance_ips = []
    for instance in all_autoscaling_instances_list: # Create a list of IP addresses for the instances in the specified autoscaling group
        if instance["AutoScalingGroupName"] == message["AutoScalingGroupName"]: # If instance is a part of the autoscaling group specified in the SNS message
            private_ip = id_to_ip(instance["InstanceId"])
            if private_ip:
                group_instance_ips.append(private_ip)

    return group_instance_ips


def terminate_instance(message):
    '''
    Remove terminating instance from the etcd cluster and send CONTINUE response to lifecycle hook
    '''
    terminating_instance_id = message["EC2InstanceId"]
    logger.debug("terminate_instance: TERMINATING INSTANCE ID: {0}".format(terminating_instance_id))

    terminating_instance_ip = id_to_ip(terminating_instance_id)
    logger.debug("terminate_instance: TERMINATING INSTANCE IP: {0}".format(terminating_instance_ip))

    available_instance_ip_list = get_autoscaling_group_ips(message)

    if available_instance_ip_list:
 
        if terminating_instance_ip: # If the instance still had an IP when we fetched the info, we remove it from our 'available' IP list"
            available_instance_ip_list.remove(terminating_instance_ip)
        logger.debug("terminate_instance: AVAIL_INSTANCE_IPS: {0}".format(available_instance_ip_list))

        etcd_result = remove_etcd_member(available_instance_ip_list, terminating_instance_id) # Have an active etcd member remove the terminated instance

        if etcd_result == 2:
            logger.warn("The instance terminated may never have been a member of the cluster. Confirm manually")
        if etcd_result == 1:
            logger.warn("There may have been an issue removing etcd member! Confirm removal")

    else:
        logger.warn("Could not get list of available autoscale instance IPs")

    return 0


def launch_instance(message):
    '''
    Add instance to etcd cluster peer list and send CONTINUE response to lifecycle hook
    '''
    launch_instance_id = message["EC2InstanceId"]

    private_ip = id_to_ip(launch_instance_id)

    available_instance_ip_list = get_autoscaling_group_ips(message)

    if available_instance_ip_list:
        available_instance_ip_list.remove(private_ip)

        etcd_result = add_etcd_member(available_instance_ip_list, private_ip)

    else:
        logger.warn("Could not get list of available autoscale instance IPs")
    
    return 0


def get_boto_clients():
    '''
    Create global variables for using the boto3 clients
    '''
    try:
        ec2_client = boto3.client("ec2")
        autoscaling_client = boto3.client("autoscaling")
    except Exception as e:
        logger.error("Could not create boto3 clients: {0}".format(e))
        sys.exit(1)

    return ec2_client, autoscaling_client


def ensure_correct_launch_config(message):
    '''
    Check the current launch config for the etcd_autoscaling_group and change it from new cluster to existing cluster if needed
    '''
    ec2_client, autoscaling_client = get_boto_clients()

    autoscaling_group_data = autoscaling_client.describe_auto_scaling_groups(AutoScalingGroupNames=[message['AutoScalingGroupName']])

    current_launch_config = autoscaling_group_data['AutoScalingGroups'][0]['LaunchConfigurationName']

    if current_launch_config != 'etcd_existing_cluster_launch_config':
        response = autoscaling_client.update_auto_scaling_group(AutoScalingGroupName=message['AutoScalingGroupName'], LaunchConfigurationName=etcd_existing_cluster_launch_config)
        logger.info('Update launch config response: {0}'.format(response))


def kickoff(event, context):
    '''
    Receive event+context from SNS that was triggered by lifecycle hook from autoscaling event
    '''
    records = event["Records"]
    logger.debug("kickoff: records from SNS event: {0}".format(records))

    result = None
    for record in records:
        sns = record["Sns"]
        message = json.loads(sns["Message"])

        try:
            metadata = json.loads(message.get("NotificationMetadata", None))
        except TypeError as e:
            logger.debug('No metadata in record: {0}'.format(e))
            metadata = None

        if metadata:
            lifecycle = metadata["transition"] # The metadata that we have added via the lifecycle hook (not a standard field)

            if lifecycle == "TERMINATING":
                logger.info("RUNNING TERMINATION FUNCTION")
                result = terminate_instance(message)
    
            if lifecycle == "LAUNCHING":
                logger.info("RUNNING LAUNCH FUNCTION")
                result = launch_instance(message)
    
            complete_lifecycle_hook(message)

            if result == 0:
                logger.info('Success')
            else:
                logger.info('Error')
        
        else:
            sns_test_notification = message.get("Event", None)
            if sns_test_notification and sns_test_notification == "autoscaling:TEST_NOTIFICATION":
                logger.debug("kickoff: Got SNS TEST_NOTIFICATION")
            else:
                logger.warn("kickoff: Recieved SNS message, but it wasn't one of: launch, terminate, or test_notification")
            ensure_correct_launch_config(message)
