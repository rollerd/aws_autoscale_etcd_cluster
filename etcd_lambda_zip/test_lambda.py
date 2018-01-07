import unittest
from unittest.mock import patch, MagicMock, Mock, call
import json
import etcd_lambda


data = json.dumps({'Records': [{'EventSource': 'aws:sns', 'EventVersion': '1.0', 'EventSubscriptionArn': 'arn:aws:sns:us-west-2:123456789:etcd_lifecycle_update:39a5b419-ce43-4b17-bf9d-79d41e4645ba', 'Sns': {'Type': 'Notification', 'MessageId': 'a55dc5b6-ae1e-5f6d-acd6-977744765a7c', 'TopicArn': 'arn:aws:sns:us-west-2:123456789:etcd_lifecycle_update', 'Subject': "Auto Scaling: Lifecycle action 'REPLACEME' for instance i-0ff0440f9024c4e37 in progress.", 'Message': '{"LifecycleHookName":"etcd_hook_instance_terminate","AccountId":"123456789","RequestId":"20e582a3-8b5f-2d31-330c-44bfbcb103f5","LifecycleTransition":"autoscaling:EC2_INSTANCE_REPLACEME","AutoScalingGroupName":"etcd_autoscaling_group","Service":"AWS Auto Scaling","Time":"2017-12-30T19:25:28.151Z","EC2InstanceId":"i-0ff0440f9024c4e37","NotificationMetadata":"{\\n \\"transition\\": \\"REPLACEME\\"\\n}\\n","LifecycleActionToken":"5f89f1c1-c77e-4b73-a658-123456789"}', 'Timestamp': '2017-12-30T19:25:28.182Z', 'SignatureVersion': '1', 'Signature': 'longrandomdatastring', 'SigningCertUrl': 'https://sns.us-west-2.amazonaws.com/SimpleNotificationService-123456789.pem', 'UnsubscribeUrl': 'https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:123456789:etcd_lifecycle_update:39a5b419-ba', 'MessageAttributes': {}}}]})

terminate_data = json.loads(data.replace('REPLACEME', 'TERMINATING'))
launch_data = json.loads(data.replace('REPLACEME', 'LAUNCHING'))
terminate_message = json.loads(terminate_data['Records'][0]['Sns']['Message'])
launch_message = json.loads(launch_data['Records'][0]['Sns']['Message']) 
bad_data = {'bad': 'data'}


class TestBotoClients(unittest.TestCase):

    def test_get_boto_clients(self):
        with patch.object(etcd_lambda.boto3, 'client', return_value=None) as mock_client:
            etcd_lambda.get_boto_clients()

        calls = [call('ec2'), call('autoscaling')]
        mock_client.assert_has_calls(calls)


@patch('etcd_lambda.ensure_correct_launch_config')
@patch('etcd_lambda.terminate_instance')
@patch('etcd_lambda.launch_instance')
@patch('etcd_lambda.complete_lifecycle_hook')
class TestKickoff(unittest.TestCase):

    def test_kickoff__launch_instance_called(self, mock_lifecycle_hook, mock_launch_instance, mock_terminate_instance, mock_launch_config):
        etcd_lambda.kickoff(launch_data, 'context')
        mock_launch_instance.assert_called()
        mock_terminate_instance.assert_not_called()
        mock_lifecycle_hook.assert_called()

    def test_kickoff__terminate_instance_called(self, mock_lifecycle_hook, mock_launch_instance, mock_terminate_instance, mock_launch_config):
        etcd_lambda.kickoff(terminate_data, 'context')
        mock_terminate_instance.assert_called()
        mock_launch_instance.assert_not_called()
        mock_lifecycle_hook.assert_called()


@patch('etcd_lambda.get_autoscaling_group_ips', return_value=['10.10.10.10', '20.20.20.20', '30.30.30.30'])
@patch('etcd_lambda.remove_etcd_member')
@patch('etcd_lambda.id_to_ip', return_value='10.10.10.10')
class TestTerminateInstance(unittest.TestCase):

    def test_terminate_instance__remove_member_called_without_terminated_instance_ip(self, mock_id_to_ip, mock_remove_etcd_member, mock_group_ips):
        etcd_lambda.terminate_instance(terminate_message)
        mock_remove_etcd_member.assert_called_with(['20.20.20.20', '30.30.30.30'], terminate_message['EC2InstanceId'])

@patch('etcd_lambda.get_autoscaling_group_ips', return_value=['10.10.10.10', '20.20.20.20', '30.30.30.30'])
@patch('etcd_lambda.id_to_ip', return_value='10.10.10.10')
@patch('etcd_lambda.add_etcd_member')
class TestLaunchInstance(unittest.TestCase):

    def test_launch_instance__add_member_called_without_launch_instance_ip(self, mock_add_etcd_member, mock_id_to_ip, mock_group_ips):
        etcd_lambda.launch_instance(launch_message)
        mock_add_etcd_member.assert_called_with(['20.20.20.20', '30.30.30.30'], '10.10.10.10')


@patch('etcd_lambda.get_boto_clients')
@patch('etcd_lambda.id_to_ip', return_value='10.10.10.10')
class TestGetAutoScalingGroups(unittest.TestCase):

    def test_get_autoscaling_group_ips__return_only_ips_in_autoscaling_group(self, mock_id_to_ip, mock_get_boto_clients):
        ec2_client = Mock()
        autoscaling_client = Mock()
        mock_get_boto_clients.return_value=(ec2_client, autoscaling_client)
        autoscaling_client.describe_auto_scaling_instances.return_value={'AutoScalingInstances': [{'AutoScalingGroupName': 'etcd_autoscaling_group', 'InstanceId': 'instanceid'}, {'AutoScalingGroupName': 'SomeOtherGroup', 'InstanceId': 'instanceid2'}]}
        assert etcd_lambda.get_autoscaling_group_ips(launch_message) == ['10.10.10.10']


@patch('etcd_lambda.get_boto_clients')
class TestIdToIp(unittest.TestCase):

    def test_id_to_ip__returns_ip(self, mock_get_boto_clients):
        ec2_client = Mock()
        autoscaling_client = Mock()
        mock_get_boto_clients.return_value=(ec2_client, autoscaling_client)
        ec2_client.describe_instances.return_value = {'Reservations': [{'Instances': [{'PrivateIpAddress': '10.10.10.10'}]}]}
        assert etcd_lambda.id_to_ip('someInstanceId') == '10.10.10.10'


class TestRemoveEtcdMember(unittest.TestCase):

    def test_remove_etcd_member__make_requests_delete_called(self):
        etcd_member_dict = Mock(text = '{"members": [{"name": "terminatingInstance", "id": "terminatingId"}, {"name": "ignoreInstance", "id": "ignoreid"}]}')
        with patch.object(etcd_lambda.requests, 'get', return_value=etcd_member_dict) as mock_requests_get:
            requests_del_result = Mock(status_code = 200)
            with patch.object(etcd_lambda.requests, 'delete', return_value=requests_del_result) as mock_requests_delete:
                etcd_lambda.remove_etcd_member(['20.20.20.20'], 'terminatingInstance')
                mock_requests_delete.assert_called()

    def test_remove_etcd_member__make_requests_delete_not_called(self):
        etcd_member_dict = Mock(text = '{"members": [{"name": "nonterminatingInstance", "id": "terminatingId"}, {"name": "ignoreInstance", "id": "ignoreid"}]}')
        with patch.object(etcd_lambda.requests, 'get', return_value=etcd_member_dict) as mock_requests_get:
            requests_del_result = Mock(status_code = 200)
            with patch.object(etcd_lambda.requests, 'delete', return_value=requests_del_result) as mock_requests_delete:
                etcd_lambda.remove_etcd_member(['20.20.20.20'], 'terminatingInstance')
                mock_requests_delete.assert_not_called()


if __name__=='__main__':
    unittest.main()
