import json
import os
import uuid

import boto3


class SqsQueue:
    def __init__(self, region, queue_url):
        key_id = os.environ.get('AWS_KEY_ID')
        acc_key = os.environ.get('AWS_ACC_KEY')
        self.region = region
        self.queue_url = queue_url
        self.sqs = boto3.client('sqs', region_name=self.region,
                                aws_access_key_id=key_id, aws_secret_access_key=acc_key)

    def send_message(self, message):
        self.sqs.send_message(QueueUrl=self.queue_url, MessageBody=message)

    def send_fifo_message(self, message, message_uid, group_id='default'):
        self.sqs.send_message(QueueUrl=self.queue_url, MessageBody=message, MessageGroupId=group_id, MessageDeduplicationId=message_uid)

    def receive_message(self):
        response = self.sqs.receive_message(
            QueueUrl=self.queue_url, MaxNumberOfMessages=1)
        if 'Messages' in response:
            return response['Messages'][0]
        else:
            return None

    def delete_message(self, receipt_handle):
        self.sqs.delete_message(QueueUrl=self.queue_url,
                                ReceiptHandle=receipt_handle)

    def clear_queue(self):
        while True:
            message = self.receive_message()
            if message is None:
                break
            self.delete_message(message['ReceiptHandle'])
            print(f'Deleted message: {message["MessageId"]}')


region = 'us-east-1'
queue_url_fifo  = 'https://sqs.us-east-1.amazonaws.com/487783143761/test-fifo-queue.fifo'
queue_url_stand = 'https://sqs.us-east-1.amazonaws.com/487783143761/test-stand-queue'


def test_send_message():
    sqs = SqsQueue(region, queue_url_stand)
    sqs.send_message(json.dumps({'test2': 'test2'}))


def test_read_message():
    sqs = SqsQueue(region, queue_url_stand)
    m = sqs.receive_message()
    print(m)
    if m is not None:
        print(m['Body'])
        sqs.delete_message(m['ReceiptHandle'])


if __name__ == '__main__':
    test_read_message()
