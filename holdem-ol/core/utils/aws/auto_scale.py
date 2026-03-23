import os
import boto3


class AutoScale:
    def __init__(self, region, asg_name):
        key_id = os.environ.get('AWS_KEY_ID')
        acc_key = os.environ.get('AWS_ACC_KEY')
        self.region = region
        self.asg_name = asg_name
        self.client = boto3.client('autoscaling', region_name=region, aws_access_key_id=key_id,
                                   aws_secret_access_key=acc_key)

    def get_desired_capacity(self):
        response = self.client.describe_auto_scaling_groups(AutoScalingGroupNames=[self.asg_name])
        return response['AutoScalingGroups'][0]['DesiredCapacity']

    def get_max_capacity(self):
        response = self.client.describe_auto_scaling_groups(AutoScalingGroupNames=[self.asg_name])
        return response['AutoScalingGroups'][0]['MaxSize']

    def get_min_capacity(self):
        response = self.client.describe_auto_scaling_groups(AutoScalingGroupNames=[self.asg_name])
        return response['AutoScalingGroups'][0]['MinSize']

    def set_desired_capacity(self, desired_capacity):
        self.client.update_auto_scaling_group(AutoScalingGroupName=self.asg_name, DesiredCapacity=desired_capacity)

    def scale_up(self):
        desired_capacity = self.get_desired_capacity()
        max_capacity = self.get_max_capacity()
        desired_capacity = desired_capacity + 1
        if desired_capacity > max_capacity:
            return
        self.set_desired_capacity(desired_capacity)

    def scale_down(self):
        desired_capacity = self.get_desired_capacity()
        min_capacity = self.get_min_capacity()
        desired_capacity = desired_capacity - 1
        if desired_capacity < min_capacity:
            return
        self.set_desired_capacity(desired_capacity)