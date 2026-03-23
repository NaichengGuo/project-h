import mlflow

import os
import boto3
import json
from botocore.exceptions import ClientError


# 参考：https://eu-west-2.console.aws.amazon.com/codesuite/codecommit/repositories/fqt/browse/refs/heads/dev/--/mlflow/mlflow_log.py?region=eu-west-2#

def set_mlflow_env(
        tracking_uri: str = "http://mlflow.xsyphon.com:7980",
        tracking_user: str = "algo_user",
        secret_name: str = "mlops/mlflow",
        region_name: str = "eu-west-2"
):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e
    secret = json.loads(get_secret_value_response['SecretString'])

    # Set MLflow environments
    mlflow.set_tracking_uri(tracking_uri)
    os.environ["MLFLOW_TRACKING_USERNAME"] = tracking_user
    os.environ["MLFLOW_TRACKING_PASSWORD"] = secret[tracking_user]
