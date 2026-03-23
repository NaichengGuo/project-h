import os.path

import boto3


class S3(object):
    def __init__(self, bucket_name: str, prefix: str, key: str = '', acc: str = ''):
        self.bucket_name = bucket_name
        self.prefix = prefix
        if key == '' or acc == '':
            self.s3_cli = boto3.client('s3')
        else:
            self.s3_cli = boto3.client('s3', aws_access_key_id=key, aws_secret_access_key=acc)

    def list_s3_files(self):
        obs = []
        continuation_token = None
        list_kwargs = {
            'Bucket': self.bucket_name,
            'Prefix': self.prefix,
        }
        s3_client = boto3.client('s3')

        while True:
            if continuation_token:
                list_kwargs['ContinuationToken'] = continuation_token
            response = s3_client.list_objects_v2(**list_kwargs)

            if 'Contents' in response:
                for obj in response['Contents']:
                    obs.append(obj['Key'])
            else:
                break
            if 'NextContinuationToken' in response:
                continuation_token = response['NextContinuationToken']
            else:
                break
        return obs

    def list_s3_files_by_range(self, start_prefix: str, end_prefix: str):
        """
        列举S3存储桶中指定前缀范围内的对象键

        Args:
            bucket_name (str): S3存储桶名称
            prefix (str): 对象键前缀
            start_prefix (str, optional): 开始前缀(包含)
            end_prefix (str, optional): 结束前缀(不包含)

        Returns:
            list: 包含符合条件的对象键的列表
        """
        objects = []
        start_after_key = self.prefix + start_prefix if start_prefix else None
        full_end_prefix = self.prefix + end_prefix

        while True:
            list_kwargs = {
                'Bucket': self.bucket_name,
                'Prefix': self.prefix,
                'StartAfter': start_after_key,
            }
            response = self.s3_cli.list_objects_v2(**list_kwargs)

            if 'Contents' in response:
                for obj in response['Contents']:
                    if start_after_key < obj['Key'] < full_end_prefix:
                        objects.append(obj['Key'])
                    else:
                        break
                start_after_key = objects[-1]
            else:
                break
            if not response.get('IsTruncated', False):
                break

        return objects

    def download_files(self, keys: list, local_path: str, log=None):
        for key in keys:
            local_file_name = os.path.join(local_path, key.split('/')[-1])
            self.s3_cli.download_file(self.bucket_name, key, local_file_name)
            if log:
                log(f'File {key} downloaded to {local_file_name}')
