#!/usr/bin/env bash

# 如果没有安装 grpcio-tools，可以使用 pip install grpcio-tools==1.62.1 安装
python -m grpc_tools.protoc -I=. --python_out=. --grpc_python_out=.  winrate.proto