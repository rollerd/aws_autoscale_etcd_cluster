import unittest
from unittest.mock import patch, MagicMock, Mock
import json
import etcd_lambda


data = json.dumps({'Records': [{'EventSource': 'aws:sns', 'EventVersion': '1.0', 'EventSubscriptionArn': 'arn:aws:sns:us-west-2:123456789:etcd_lifecycle_update:39a5b419-ce43-4b17-bf9d-79d41e4645ba', 'Sns': {'Type': 'Notification', 'MessageId': 'a55dc5b6-ae1e-5f6d-acd6-977744765a7c', 'TopicArn': 'arn:aws:sns:us-west-2:123456789:etcd_lifecycle_update', 'Subject': "Auto Scaling: Lifecycle action 'REPLACEME' for instance i-0ff0440f9024c4e37 in progress.", 'Message': '{"LifecycleHookName":"etcd_hook_instance_terminate","AccountId":"123456789","RequestId":"20e582a3-8b5f-2d31-330c-44bfbcb103f5","LifecycleTransition":"autoscaling:EC2_INSTANCE_REPLACEME","AutoScalingGroupName":"etcd_autoscaling_group","Service":"AWS Auto Scaling","Time":"2017-12-30T19:25:28.151Z","EC2InstanceId":"i-0ff0440f9024c4e37","NotificationMetadata":"{\\n \\"transition\\": \\"REPLACEME\\"\\n}\\n","LifecycleActionToken":"5f89f1c1-c77e-4b73-a658-123456789"}', 'Timestamp': '2017-12-30T19:25:28.182Z', 'SignatureVersion': '1', 'Signature': 'longrandomdatastring', 'SigningCertUrl': 'https://sns.us-west-2.amazonaws.com/SimpleNotificationService-123456789.pem', 'UnsubscribeUrl': 'https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:123456789:etcd_lifecycle_update:39a5b419-ba', 'MessageAttributes': {}}}]})

terminate_data = json.loads(data.replace('REPLACEME', 'TERMINATING'))
launch_data = json.loads(data.replace('REPLACEME', 'LAUNCHING'))
terminate_message = json.loads(terminate_data['Records'][0]['Sns']['Message'])
launch_message = json.loads(launch_data['Records'][0]['Sns']['Message']) 
bad_data = {'bad': 'data'}


@patch('etcd_lambda.terminate_instance')
@patch('etcd_lambda.launch_instance')
@patch('etcd_lambda.complete_lifecycle_hook')
class TestKickoff(unittest.TestCase):

    def test_kickoff_calls_terminate_instance_func_only(self, mock_complete_lifecycle_hook, mock_launch_instance, mock_terminate_instance):
        etcd_lambda.kickoff(terminate_data, 'context')
        mock_terminate_instance.assert_called_with(terminate_message)
        mock_launch_instance.assert_not_called()

    def test_kickoff_calls_launch_instance_func_only(self, mock_complete_lifecycle_hook, mock_launch_instance, mock_terminate_instance):
        etcd_lambda.kickoff(launch_data, 'context')
        mock_launch_instance.assert_called_with(launch_message)
        mock_terminate_instance.assert_not_called()

    def test_kickoff_bad_data_raise_exception(self, mock_complete_lifecycle_hook, mock_launch_instance, mock_terminate_instance):
        self.assertRaises(KeyError, etcd_lambda.kickoff, bad_data, 'context')


@patch('etcd_lambda.remove_etcd_member')
@patch('etcd_lambda.id_to_ip', return_value='10.10.10.10')
@patch('etcd_lambda.get_autoscale_group_ips', return_value=['10.10.10.10', '20.20.20.20', '30.30.30.30', '40.40.40.40'])
class TestTerminateInstance(unittest.TestCase):

    def test_terminate_instance_remove_etcd_member_called_with_correct_args(self, mock_get_autoscale_group_ips, mock_id_to_ip, mock_remove_etcd_member):
        etcd_lambda.terminate_instance(terminate_message)
        etcd_lambda.remove_etcd_member.assert_called_with(['20.20.20.20', '30.30.30.30', '40.40.40.40'], terminate_message['EC2InstanceId'])


@patch('etcd_lambda.add_etcd_member')
@patch('etcd_lambda.id_to_ip', return_value='10.10.10.10')
@patch('etcd_lambda.get_autoscale_group_ips', return_value=['10.10.10.10', '20.20.20.20', '30.30.30.30', '40.40.40.40'])
class TestLaunchInstance(unittest.TestCase):

    def test_launch_instance_add_etcd_member_called_with_correct_args(self, mock_get_autoscale_group_ips, mock_id_to_ip, mock_add_etcd_member):
        etcd_lambda.launch_instance(launch_message)
        etcd_lambda.add_etcd_member.assert_called_with(['20.20.20.20', '30.30.30.30', '40.40.40.40'], '10.10.10.10')


class TestIdToIp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        etcd_lambda.setup_boto_clients()

    def setUp(self):
        self.instance_data_fixture = {'Reservations':[{'Instances':[{'PrivateIpAddress': '10.10.10.10'}]}]}
    def test_id_to_ip_returns_correct_ip_address(self):
        etcd_lambda.EC2_CLIENT.describe_instances = Mock(return_value=self.instance_data_fixture)
        assert etcd_lambda.id_to_ip('instanceId') == '10.10.10.10'


@patch('etcd_lambda.id_to_ip', return_value='10.10.10.10')
class TestGetAutoScaleGroupIps(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        etcd_lambda.setup_boto_clients()

    def setUp(self):
        self.autoscaling_inst_data = {'AutoScalingInstances':[{'AutoScalingGroupName': 'etcd_autoscaling_group', 'InstanceId': '12345'}, {'AutoScalingGroupName': 'ignore', 'InstanceId': 'throw_error'}, {'AutoScalingGroupName': 'etcd_autoscaling_group', 'InstanceId': '3456'}]}

    def test_get_autoscaling_group_ips_success(self, mock_id_to_ip):
        etcd_lambda.AUTOSCALING_CLIENT.describe_auto_scaling_instances = Mock(return_value=self.autoscaling_inst_data)
        assert etcd_lambda.get_autoscale_group_ips(launch_message) == ['10.10.10.10', '10.10.10.10']


@patch('etcd_lambda.requests.get')
class TestRemoveEtcdMember(unittest.TestCase):

  i  


    

    


if __name__=='__main__':
    unittest.main()
