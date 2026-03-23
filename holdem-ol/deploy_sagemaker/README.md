# SageMaker Deployment for Holdem Agent

This directory contains scripts to deploy the `ev_v1_aggressive` agent to AWS SageMaker.

## Structure

- `code/inference.py`: The entry point for the SageMaker endpoint. Handles model loading and inference logic.
- `code/requirements.txt`: Python dependencies required by the agent.
- `deploy.py`: Script to package the project code and deploy it to SageMaker.

## Prerequisites

1.  AWS Credentials configured (e.g., via `aws configure` or environment variables).
2.  Permissions to create SageMaker models, endpoints, and upload to S3.
3.  `sagemaker` python SDK installed (`pip install sagemaker`).

## Deployment Steps

1.  Run the deployment script:
    ```bash
    python deploy_sagemaker/deploy.py
    ```
    This script will:
    - Create a `model.tar.gz` containing the project code (`core`, `models`, `deploy`) and the inference code.
    - Upload the tarball to the default SageMaker S3 bucket.
    - Create a SageMaker Model using the PyTorch container (serving as a generic Python environment).
    - Deploy the model to an endpoint (default instance: `ml.m5.large`).

2.  Note on Winrate Service:
    The `ev_v1_aggressive` agent normally connects to a local gRPC service for winrate calculations. 
    Since the gRPC service is not included in this deployment package, the agent will automatically fallback to using Monte Carlo simulation (`treys` library) for winrate calculation. 
    This is functional but might be slightly slower than the gRPC service.

## Testing

You can test the inference logic locally using:
```bash
python deploy_sagemaker/code/inference.py
```
This simulates a prediction request with sample data.
