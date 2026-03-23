import argparse
import traceback
from flask import Flask, request, jsonify
from models.agent.manager import make_agent

# 创建 Flask 应用
app = Flask(__name__)

# output example
# {
#     "result": 2000,
#     "data": {
#         "action":, // fold, check, call, raise
#         "num":
#     }
# }

agent = None


def _ok_response(data):
    return jsonify({'predictions': data})


# def _ok_response(data):
#     return jsonify({'result': 2000, 'data': data})


# def _error_4000_response(msg):
#     return jsonify({'result': 4000, 'msg': msg})

def _error_4000_response(msg):
    return jsonify({'error_code': "BAD_REQUEST", 'msg': msg})


def check_param(param):
    return ""


@app.route('/health', methods=['Get'])
def root():
    return "ok"


@app.route('/name', methods=['Get'])
def get_name():
    if hasattr(agent, "get_name"):
        return agent.get_name()
    return "known"


@app.route('/invocations', methods=['POST'])
def predict_route():
    # 获取请求的数据
    data = request.json
    print(data)

    check_result = check_param(data)
    if check_result != "":
        return _error_4000_response(check_result)

    # 调用预测函数进行预测
    result = agent.predict_api(data)

    # 返回预测结果
    return _ok_response(result)


@app.errorhandler(Exception)
def handle_exception(e: Exception):
    # 将异常信息转化为字符串
    error_message = traceback.format_exc()
    print(error_message)

    return _error_4000_response(error_message)


def main():
    global agent
    parser = argparse.ArgumentParser("model service")
    parser.add_argument("--model_name", type=str, default="")
    parser.add_argument("--model_path", type=str, default="")
    parser.add_argument("--board_path", type=str, default="./")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5200)
    parser.add_argument("--argmax_action", type=bool, default=False)
    parser.add_argument("--debug", type=bool, default=False)
    args = parser.parse_args()

    if args.model_name == "":
        print("no model specified")
        return

    agent = make_agent(args.model_name, {"model_path": args.model_path, "argmax_action": args.argmax_action,"board_path":args.board_path})

    app.run(port=args.port, debug=args.debug, host=args.host)


import joblib
class InfoSet:
    """
    Most of the infoset information (actions, player) should be inherited from the history class.

    """

    def __init__(self, infoSet_key, actions, player):
        self.infoSet = infoSet_key
        self.__actions = actions
        self.__player = player

        self.regret = {a: 0 for a in self.actions()}
        self.strategy = {a: 0 for a in self.actions()}
        self.cumulative_strategy = {a: 0 for a in self.actions()}
        self.get_strategy()
        assert 1.0 - sum(self.strategy.values()) < 1e-6

    def __repr__(self) -> str:
        return str(self.infoSet)

    def actions(self) :
        return self.__actions

    def player(self):
        return self.__player

    def to_dict(self):
        return {
            "infoset": self.infoSet,
            "regret": self.regret,
            "cumulative_strategy": self.cumulative_strategy,
        }

    def get_strategy(self):
        """
        Updates the current strategy based on the current regret, using regret matching
        """
        regret = {a: max(r, 0) for a, r in self.regret.items()}

        regret_sum = sum(regret.values())

        if regret_sum > 0:
            self.strategy = {a: r / regret_sum for a, r in regret.items()}
        else:
            self.strategy = {a: 1 / len(self.actions()) for a in self.actions()}

    def get_average_strategy(self):
        """ """
        assert len(self.actions()) == len(
            self.cumulative_strategy
        )  # The cumulative strategy should map a probability for every action

        strategy_sum = sum(self.cumulative_strategy.values())

        if strategy_sum > 0:
            return {a: s / strategy_sum for a, s in self.cumulative_strategy.items()}
        else:
            return {a: 1 / len(self.actions()) for a in self.actions()}

class PostflopHoldemInfoSet(InfoSet):
    """
    Information Sets (InfoSets) cannot be chance histories, nor terminal histories.
    This condition is checked when infosets are created.

    This infoset is an abstracted versions of the history in this case.
    See the `get_infoSet_key(self)` function for these

    There are 2 abstractions we are doing:
            1. Card Abstraction (grouping together similar hands)
            2. Action Abstraction

    I've imported my abstractions from `abstraction.py`.

    """

    def __init__(self, infoSet_key, actions, player):
        assert len(infoSet_key) >= 1
        super().__init__(infoSet_key, actions, player)

# 运行 Flask 应用
if __name__ == '__main__':
    main()
