import argparse
from testing.evaluate import model_testing, set_mlflow_params


def main():

    parser = argparse.ArgumentParser("Model Evaluate")

    parser.add_argument("--round_count", type=int, default=2000)
    parser.add_argument("--slumbot_count", type=int, default=1000)
    parser.add_argument("--localhost_mlflow", type=bool, default=False)
    parser.add_argument("--disable_mlflow", type=bool, default=False)
    args = parser.parse_args()

    #set_mlflow_params(args.localhost_mlflow, args.disable_mlflow)
    model_testing(args.round_count, args.slumbot_count)

    print("finish testing")

    # try:
    #     model_testing(args.round_count, args.slumbot_count)
    # except Exception as e:
    #     print("Model testing failed with exception")
    #     print(e)
    #     traceback.print_exc()


if __name__ == '__main__':
    main()
