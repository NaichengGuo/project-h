import logging

stream_handle = logging.StreamHandler()
stream_handle.setFormatter(
    logging.Formatter(
        '[%(levelname)s:%(process)d %(module)s:%(lineno)d %(asctime)s] '
        '%(message)s'))
log = logging.getLogger('texas')
log.propagate = False
log.addHandler(stream_handle)
log.setLevel(logging.INFO)


def print_with_time(msg: str):
    from datetime import datetime

    # 获取当前时间
    now = datetime.now()

    # 转换为字符串
    time_string = now.strftime("%Y-%m-%d %H:%M:%S")

    # 打印带有时间的信息
    print(f"[{time_string}] {msg}")


def print_red(msg: str):
    print(f"\033[91m{msg}\033[0m")


if __name__ == '__main__':
    print_with_time("This is a message.")
