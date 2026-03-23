import json
import logging
import sys
import os
import traceback
# from flask import Flask, request, jsonify # Not needed for SageMaker contract

# Add the root directory to sys.path so we can import models and core
# Assuming SageMaker unpacks the model.tar.gz into /opt/ml/model
# and our code structure puts 'holdem' content at the root of model.tar.gz
# or inside a 'code' directory if using the 'code' directory structure.
# SageMaker usually adds /opt/ml/model/code to PYTHONPATH if it exists.
# But we might need to add /opt/ml/model as well if our imports are top-level like 'models.agent...'

# If we package everything into model.tar.gz such that 'models' is at the root of the archive:
# /opt/ml/model/models/...
# Then we need /opt/ml/model in sys.path.

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is likely /opt/ml/model/code
MODEL_DIR = os.path.dirname(ROOT_DIR) # This is likely /opt/ml/model

if MODEL_DIR not in sys.path:
    sys.path.insert(0, MODEL_DIR)

# Also try to append the current directory just in case
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Handle local development environment
if not os.path.exists(os.path.join(MODEL_DIR, 'models')):
    # Maybe we are running locally in dev mode, try parent directory
    PARENT_DIR = os.path.dirname(MODEL_DIR)
    if os.path.exists(os.path.join(PARENT_DIR, 'models')):
         if PARENT_DIR not in sys.path:
            sys.path.insert(0, PARENT_DIR)

try:
    import models.agent.manager as agent_manager
    import models.agent
except ImportError:
    # Fallback: maybe we are not in 'code' subdir but at root?
    # Or maybe the structure is different.
    # Let's print sys.path for debugging in logs
    print(f"sys.path: {sys.path}")
    raise

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

def model_fn(model_dir):
    """
    Load the model. In this case, instantiate the agent.
    """
    logger.info("Loading model from %s", model_dir)
    try:
        default_model_name = os.environ.get("DEFAULT_MODEL_NAME", "ev_v1_aggressive")
        model_names_env = os.environ.get("MODEL_NAMES", "").strip()
        model_configs_env = os.environ.get("MODEL_CONFIGS_JSON", "").strip()
        model_configs = {}
        if model_configs_env:
            model_configs = json.loads(model_configs_env)

        if model_names_env:
            model_names = [name.strip() for name in model_names_env.split(",") if name.strip()]
        else:
            model_names = "ev_v1_aggressive,ev_v2_neutral,prob_conservative_v1_250909,gto_v1,gto_v2,mtt_v1".split(",")#sorted(list(agent_manager._registry.agent_specs.keys()))

        agents = {}
        load_errors = {}
        default_config = model_configs.get("_default") if isinstance(model_configs, dict) else None
        if default_config is None:
            default_config = {"argmax_action": False}
        for model_name in model_names:
            try:
                config = default_config
                if isinstance(model_configs, dict) and model_name in model_configs:
                    config = model_configs.get(model_name) or default_config
                agents[model_name] = agent_manager.make_agent(
                    model_name, config
                )
                logger.info("Agent %s loaded successfully", model_name)
            except Exception:
                load_errors[model_name] = traceback.format_exc()
                logger.error("Failed to load agent %s: %s", model_name, load_errors[model_name])

        if not agents and load_errors:
            first_error = next(iter(load_errors.values()))
            raise RuntimeError(f"Failed to load any agent. First error:\n{first_error}")

        if agents and default_model_name not in agents:
            default_model_name = next(iter(agents.keys()))

        if load_errors:
            logger.info("Some agents failed to load: %s", sorted(list(load_errors.keys())))

        return {"models": agents, "default_model_name": default_model_name}
    except Exception as e:
        logger.error("Error loading model: %s", traceback.format_exc())
        raise

def input_fn(request_body, request_content_type):
    """
    Parse the input request.
    """
    logger.info("Received request with content type %s", request_content_type)
    if request_content_type == 'application/json':
        return json.loads(request_body)
    elif request_content_type == 'application/x-npy':
        # If PyTorch serializer uses npy, we might receive this.
        # But we prefer JSON. If we receive npy, we try to decode it.
        # However, our data is structured JSON, not a simple numpy array.
        import numpy as np
        import io
        return np.load(io.BytesIO(request_body), allow_pickle=True)
    else:
        # Handle other content types if necessary
        raise ValueError(f"Unsupported content type: {request_content_type}")

def predict_fn(input_data, model):
    """
    Make a prediction.
    """
    logger.info("Predicting on input data")
    try:
        if hasattr(model, "predict_api"):
            return model.predict_api(input_data)

        if not isinstance(model, dict) or "models" not in model:
            raise ValueError("Invalid model object. Expected agent instance or {'models': {...}} dict.")

        agents = model.get("models") or {}
        default_model_name = model.get("default_model_name")

        params = {}
        if isinstance(input_data, dict):
            params = input_data.get("params") or {}

        model_name = None
        if isinstance(params, dict):
            model_name = params.get("model_name")
        if not model_name and isinstance(input_data, dict):
            model_name = input_data.get("model_name")
        if not model_name and isinstance(input_data, dict):
            inputs = input_data.get("inputs") or {}
            if isinstance(inputs, dict):
                model_name = inputs.get("model_name")
        if not model_name:
            model_name = default_model_name

        agent = agents.get(model_name)
        if agent is None:
            raise ValueError(
                f"Unknown model_name={model_name}. Available: {sorted(list(agents.keys()))}"
            )

        return agent.predict_api(input_data)
    except Exception as e:
        logger.error("Error during prediction: %s", traceback.format_exc())
        raise

def output_fn(prediction, response_content_type):
    """
    Format the output.
    """
    logger.info("Formatting output")
    if response_content_type == 'application/json':
        return json.dumps({'predictions': prediction})
    else:
        raise ValueError(f"Unsupported response content type: {response_content_type}")

# Local testing block
if __name__ == '__main__':
    # This block is for local testing only
    agent = model_fn('.')
    
    # Example input from user (Corrected: my_id is 8, so players list must have at least 9 elements)
    example_input = {'inputs': {'dealer_id': 0, 'players': [{'chips_to_desk': 0, 'chips_remain': 7070000, 'id': 0}, {'chips_to_desk': 2727000, 'chips_remain': 0, 'id': 1}], 'small_blind': 100000, 'my_hand_cards': ['S6', 'C8'], 'actions': [{'player_id': 8, 'after_pot': 100000, 'action': -1, 'stage': 0, 'num': 100000, 'after_remain_chips': 3508000}, {'player_id': 7, 'after_pot': 300000, 'action': -2, 'stage': 0, 'num': 200000, 'after_remain_chips': 17968000}, {'player_id': 6, 'after_pot': 750000, 'action': 2, 'stage': 0, 'num': 450000, 'after_remain_chips': 6378000}, {'player_id': 5, 'after_pot': 1800000, 'action': 2, 'stage': 0, 'num': 1050000, 'after_remain_chips': 4117000}, {'player_id': 4, 'after_pot': 3313000, 'action': 3, 'stage': 0, 'num': 1513000, 'after_remain_chips': 0}, {'player_id': 3, 'after_pot': 4826000, 'action': 1, 'stage': 0, 'num': 1513000, 'after_remain_chips': 18238000}, {'player_id': 2, 'after_pot': 9508000, 'action': 2, 'stage': 0, 'num': 4682000, 'after_remain_chips': 168000}, {'player_id': 1, 'after_pot': 12235000, 'action': 3, 'stage': 0, 'num': 2727000, 'after_remain_chips': 0}, {'player_id': 0, 'after_pot': 12235000, 'action': 0, 'stage': 0, 'num': 0, 'after_remain_chips': 7070000}], 'public_cards': [], 'game_type': 1, 'my_id': 1, 'ante': 0}}
    example_input["params"] = {"model_name": "gto_v1"}
    res = predict_fn(example_input, agent)
    print(output_fn(res, 'application/json'))
