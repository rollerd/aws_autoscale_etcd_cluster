import unittest
from unittest.mock import patch
import etcd_lambda
import json


data = json.dumps({'Records': [{'EventSource': 'aws:sns', 'EventVersion': '1.0', 'EventSubscriptionArn': 'arn:aws:sns:us-west-2:123456789:etcd_lifecycle_update:39a5b419-ce43-4b17-bf9d-79d41e4645ba', 'Sns': {'Type': 'Notification', 'MessageId': 'a55dc5b6-ae1e-5f6d-acd6-977744765a7c', 'TopicArn': 'arn:aws:sns:us-west-2:123456789:etcd_lifecycle_update', 'Subject': "Auto Scaling: Lifecycle action 'REPLACEME' for instance i-0ff0440f9024c4e37 in progress.", 'Message': '{"LifecycleHookName":"etcd_hook_instance_terminate","AccountId":"123456789","RequestId":"20e582a3-8b5f-2d31-330c-44bfbcb103f5","LifecycleTransition":"autoscaling:EC2_INSTANCE_REPLACEME","AutoScalingGroupName":"etcd_autoscaling_group","Service":"AWS Auto Scaling","Time":"2017-12-30T19:25:28.151Z","EC2InstanceId":"i-0ff0440f9024c4e37","NotificationMetadata":"{\\n \\"transition\\": \\"REPLACEME\\"\\n}\\n","LifecycleActionToken":"5f89f1c1-c77e-4b73-a658-123456789"}', 'Timestamp': '2017-12-30T19:25:28.182Z', 'SignatureVersion': '1', 'Signature': 'longrandomdatastring', 'SigningCertUrl': 'https://sns.us-west-2.amazonaws.com/SimpleNotificationService-123456789.pem', 'UnsubscribeUrl': 'https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:123456789:etcd_lifecycle_update:39a5b419-ba', 'MessageAttributes': {}}}]})


class TestKickoff(unittest.TestCase):

    def setUp(self):
        self.terminate_data = json.loads(data.replace('REPLACEME', 'TERMINATING'))
        self.launch_data = json.loads(data.replace('REPLACEME', 'LAUNCHING'))


    @patch('etcd_lambda.terminate_instance')
    @patch('etcd_lambda.launch_instance')
    def test_kickoff_calls_terminate_instance_func(self, mock_launch_instance, mock_terminate_instance):
        etcd_lambda.kickoff(self.terminate_data, 'context')
        message_data = json.loads(self.terminate_data['Records'][0]['Sns']['Message'])
        mock_terminate_instance.assert_called_with(message_data)
        mock_launch_instance.assert_not_called()

    @patch('etcd_lambda.terminate_instance')
    @patch('etcd_lambda.launch_instance')
    def test_kickoff_does_not_call_launch_instance_func(self, mock_launch_instance, mock_terminate_instance):
        etcd_lambda.kickoff(self.terminate_data, 'context')
        mock_launch_instance.assert_not_called()

    @patch('etcd_lambda.terminate_instance')
    @patch('etcd_lambda.launch_instance')
    def test_kickoff_calls_launch_instance_func(self, mock_launch_instance, mock_terminate_instance):
        etcd_lambda.kickoff(self.launch_data, 'context')
        message_data = json.loads(self.launch_data['Records'][0]['Sns']['Message'])
        mock_launch_instance.assert_called_with(message_data)

       
if __name__=='__main__':
    unittest.main()
