import argparse
import json
import os
import uuid

import testing.config as config
from core.utils.aws.sqs import SqsQueue
from core.utils.aws.auto_scale import AutoScale

key_id = os.environ.get('AWS_KEY_ID')
acc_key = os.environ.get('AWS_ACC_KEY')


def main():
    parser = argparse.ArgumentParser("Model Evaluate")

    parser.add_argument("--model_name", type=str, default="")
    parser.add_argument("--model_version", type=str, default="")
    parser.add_argument("--model_service_url", type=str, default="")
    parser.add_argument("--round_count", type=int, default=2000)
    parser.add_argument("--slumbot_count", type=int, default=1000)
    parser.add_argument("--appoint_agent", type=str, default="")
    args = parser.parse_args()

    if args.model_name == "":
        print("no model specified")
        return
    if args.model_version == "":
        print("no model version specified")
        return
    if args.model_service_url == "":
        print("no model service url specified")
        return

    write_task(args.model_name, args.model_version, args.model_service_url, args.round_count, args.slumbot_count, args.appoint_agent)
    trigger_testing()


def write_task(model_name, version, model_service_url, round_count, slumbot_count, appoint_agent):
    # Create SQS client
    sqs = SqsQueue(config.region, config.sqs_url)

    task = {
        "model_name": model_name,
        "version": version,
        "model_service_url": model_service_url,
        "round_count": round_count,
        "slumbot_count": slumbot_count,
        "appoint_agent": appoint_agent
    }
    task_json = json.dumps(task)

    sqs.send_fifo_message(task_json, str(uuid.uuid4()))

    print(f"write task to SQS: {task}")


def trigger_testing():
    # Create Auto Scaling client
    autoscaling = AutoScale(config.region, config.auto_scaling_group)
    current_desired_capacity = autoscaling.get_desired_capacity()
    max_capacity = autoscaling.get_max_capacity()
    num_ec2_instances = current_desired_capacity + 1
    autoscaling.scale_up()

    print(f"trigger testing, current desired capacity: {current_desired_capacity}, new desired capacity: {num_ec2_instances}, max capacity: {max_capacity}")


if __name__ == '__main__':
    main()
