import logging
import boto3

class S3WithProfile:
    def __init__(self, profile, bucket):
        self.profile = profile
        self.bucket = bucket
        self.session = boto3.Session(profile_name=profile)
        self.s3 = self.session.client('s3')
    
    def download(self, key, local_path):
        try:
            self.s3.download_file(self.bucket, key, local_path)
            return True
        except Exception as e:
            logging.error(f'Error downloading {key} {local_path} {e}')
            return False
    
    def exists(self, key):
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except:
            return False

class S3:
    def __init__(self, bucket):
        self.bucket = bucket
        self.s3 = boto3.client('s3')
    
    def download(self, key, local_path):
        try:
            self.s3.download_file(self.bucket, key, local_path)
            return True
        except Exception as e:
            logging.error(f'Error downloading {key} {local_path} {e}')
            return False
    
    def exists(self, key):
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except:
            return False