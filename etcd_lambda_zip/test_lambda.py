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

@patch('etcd_lambda.complete_lifecycle_hook')
class TestKickoff(unittest.TestCase):

    def test_launch_instance_called(self, mock_lifecycle_hook):
        
    



if __name__=='__main__':
    unittest.main()
