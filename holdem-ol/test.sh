export PYTHONPATH=$PWD/..:$PYTHONPATH
# export WIN_RATE_RPC_URI="127.0.0.1:8989"
# export PYTHONWARNINGS="ignore::DeprecationWarning"
# export RAY_memory_monitor_refresh_ms=0

# nohup python deploy/server.py --model_name dqn --port 10202 --model_path=chaos/p2/slimv2/p2_slimv2_model_20800.pth --argmax_action=True > evlog/p2_slimv2_model_20800.log   2>&1 &
# python deploy/server.py --model_name gto_v2 --port 10202 --model_path=./board3_5.pkl


# python deploy/server.py --model_name dqn --port 10202 --model_path=./p2_slimv2_model_33900.pth --argmax_action=False

python deploy/server.py --model_name ev_v1_aggressive --port 10202