import os
import tarfile
import sagemaker
from botocore.exceptions import ClientError
from sagemaker.pytorch import PyTorchModel
from sagemaker.serializers import JSONSerializer
from sagemaker.deserializers import JSONDeserializer
from sagemaker.utils import name_from_base
from sagemaker.predictor import Predictor

def create_tarball(source_dir, output_path):
    """
    Create a tarball from source_dir, excluding certain files.
    """
    with tarfile.open(output_path, "w:gz") as tar:
        # Add the code directory (inference.py, requirements.txt)
        code_dir = os.path.join(source_dir, "deploy_sagemaker", "code")
        tar.add(code_dir, arcname="code")
        
        # Add other necessary directories
        # We need core, models, deploy, rates
        for dirname in ["core", "models", "deploy", "rates"]:
            dir_path = os.path.join(source_dir, dirname)
            if os.path.exists(dir_path):
                tar.add(dir_path, arcname=dirname)
            else:
                print(f"Warning: {dirname} not found in {source_dir}")

        for filename in ["board3_5.pkl", "board3_5_v1.pkl"]:
            file_path = os.path.join(source_dir, filename)
            if os.path.exists(file_path):
                tar.add(file_path, arcname=filename)
            else:
                print(f"Warning: {filename} not found in {source_dir}")

        # Add any other files if needed (e.g., config files)
        # Check for specific files used by ev_v1_aggressive
        # It uses strategy_data_v2 which is in the python file.
        # It doesn't seem to use external model files.
        
        print(f"Created {output_path}")

def _get_role():
    role = os.environ.get("SAGEMAKER_ROLE_ARN") or os.environ.get("AWS_SAGEMAKER_ROLE_ARN")
    if role:
        return role
    try:
        return sagemaker.get_execution_role()
    except ValueError:
        raise RuntimeError(
            "Could not determine SageMaker execution role. Set SAGEMAKER_ROLE_ARN."
        )

def _endpoint_exists(sess: sagemaker.Session, endpoint_name: str) -> bool:
    try:
        sess.sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        return True
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in {"ValidationException"}:
            return False
        raise


def _create_model(sess: sagemaker.Session, model: PyTorchModel, instance_type: str) -> str:
    model_name = name_from_base("holdem-ev-model")
    container_def = model.prepare_container_def(instance_type=instance_type)
    sess.sagemaker_client.create_model(
        ModelName=model_name,
        ExecutionRoleArn=model.role,
        PrimaryContainer=container_def,
    )
    return model_name


def _create_endpoint_config(
    sess: sagemaker.Session,
    *,
    model_name: str,
    endpoint_config_name: str,
    instance_type: str,
    initial_instance_count: int,
) -> str:
    sess.sagemaker_client.create_endpoint_config(
        EndpointConfigName=endpoint_config_name,
        ProductionVariants=[
            {
                "VariantName": "AllTraffic",
                "ModelName": model_name,
                "InitialInstanceCount": initial_instance_count,
                "InstanceType": instance_type,
                "InitialVariantWeight": 1.0,
            }
        ],
    )
    return endpoint_config_name


def deploy():
    role = _get_role()

    sess = sagemaker.Session()
    bucket = sess.default_bucket()
    prefix = "holdem-ev-v1-aggressive"
    endpoint_name = os.environ.get("SAGEMAKER_ENDPOINT_NAME", "holdem-ev-endpoint-config-2026-03-13-15-04-28-342")
    instance_type = os.environ.get("SAGEMAKER_INSTANCE_TYPE", "ml.m5.4xlarge")
    initial_instance_count = int(os.environ.get("SAGEMAKER_INITIAL_INSTANCE_COUNT", "1"))
    
    # Create model.tar.gz
    source_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    model_artifact = "model.tar.gz"
    create_tarball(source_dir, model_artifact)
    
    # Upload to S3
    model_uri = sess.upload_data(model_artifact, bucket=bucket, key_prefix=prefix)
    print(f"Uploaded model to {model_uri}")
    
    # Create PyTorchModel
    # We use PyTorch container as a generic Python container
    model = PyTorchModel(
        model_data=model_uri,
        role=role,
        entry_point="inference.py",
        source_dir=os.path.join(os.path.dirname(__file__), "code"),
        framework_version="2.2.0",
        py_version="py310",
        sagemaker_session=sess,
        name=name_from_base("holdem-ev-v1"),
        env={
            "DEFAULT_MODEL_NAME": "ev_v1_aggressive",
            "MODEL_NAMES": "ev_v1_aggressive,ev_v2_neutral,prob_conservative_v1_250909,gto_v1,gto_v2,mtt_v1",
            "MODEL_CONFIGS_JSON": '{"_default":{"argmax_action":false,"board_path":"/opt/ml/model"},"gto_v1":{"model_path":"/opt/ml/model/board3_5_v1.pkl","board_path":"/opt/ml/model"},"gto_v2":{"model_path":"/opt/ml/model/board3_5.pkl","board_path":"/opt/ml/model"},"mtt_v1":{"model_path":"/opt/ml/model/board3_5_v1.pkl","board_path":"/opt/ml/model"}}',
        }
    )
    
    model_name = _create_model(sess, model, instance_type=instance_type)
    endpoint_config_name = _create_endpoint_config(
        sess,
        model_name=model_name,
        endpoint_config_name=name_from_base("holdem-ev-endpoint-config"),
        instance_type=instance_type,
        initial_instance_count=initial_instance_count,
    )

    if _endpoint_exists(sess, endpoint_name):
        old_endpoint_config_name = sess.sagemaker_client.describe_endpoint(
            EndpointName=endpoint_name
        )["EndpointConfigName"]
        print(
            f"Updating endpoint {endpoint_name} from {old_endpoint_config_name} to {endpoint_config_name}"
        )
        sess.sagemaker_client.update_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name,
        )
        sess.wait_for_endpoint(endpoint_name)
    else:
        print(f"Creating endpoint {endpoint_name} with {endpoint_config_name}")
        sess.sagemaker_client.create_endpoint(
            EndpointName=endpoint_name, EndpointConfigName=endpoint_config_name
        )
        sess.wait_for_endpoint(endpoint_name)

    predictor = Predictor(
        endpoint_name=endpoint_name,
        sagemaker_session=sess,
        serializer=JSONSerializer(),
        deserializer=JSONDeserializer(),
    )
    
    print(f"Deployed to endpoint: {predictor.endpoint_name}")
    
    # Example prediction
    example_input = {'inputs': {'dealer_id': 0, 'players': [{'chips_to_desk': 0, 'chips_remain': 7070000, 'id': 0}, {'chips_to_desk': 2727000, 'chips_remain': 0, 'id': 1}, {'chips_to_desk': 4682000, 'chips_remain': 168000, 'id': 2}, {'chips_to_desk': 1513000, 'chips_remain': 18238000, 'id': 3}, {'chips_to_desk': 1513000, 'chips_remain': 0, 'id': 4}, {'chips_to_desk': 1050000, 'chips_remain': 4117000, 'id': 5}, {'chips_to_desk': 450000, 'chips_remain': 6378000, 'id': 6}, {'chips_to_desk': 200000, 'chips_remain': 17968000, 'id': 7}, {'chips_to_desk': 100000, 'chips_remain': 3508000, 'id': 8}], 'small_blind': 100000, 'my_hand_cards': ['S6', 'C8'], 'actions': [{'player_id': 8, 'after_pot': 100000, 'action': -1, 'stage': 0, 'num': 100000, 'after_remain_chips': 3508000}, {'player_id': 7, 'after_pot': 300000, 'action': -2, 'stage': 0, 'num': 200000, 'after_remain_chips': 17968000}, {'player_id': 6, 'after_pot': 750000, 'action': 2, 'stage': 0, 'num': 450000, 'after_remain_chips': 6378000}, {'player_id': 5, 'after_pot': 1800000, 'action': 2, 'stage': 0, 'num': 1050000, 'after_remain_chips': 4117000}, {'player_id': 4, 'after_pot': 3313000, 'action': 3, 'stage': 0, 'num': 1513000, 'after_remain_chips': 0}, {'player_id': 3, 'after_pot': 4826000, 'action': 1, 'stage': 0, 'num': 1513000, 'after_remain_chips': 18238000}, {'player_id': 2, 'after_pot': 9508000, 'action': 2, 'stage': 0, 'num': 4682000, 'after_remain_chips': 168000}, {'player_id': 1, 'after_pot': 12235000, 'action': 3, 'stage': 0, 'num': 2727000, 'after_remain_chips': 0}, {'player_id': 0, 'after_pot': 12235000, 'action': 0, 'stage': 0, 'num': 0, 'after_remain_chips': 7070000}], 'public_cards': [], 'game_type': 1, 'my_id': 8, 'ante': 0}}
    
    result = predictor.predict(example_input)
    print("Prediction result:", result)

if __name__ == "__main__":
    deploy()
