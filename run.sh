#!/bin/bash
script_dir=$(dirname "$0")
path=$(python "$script_dir/settings.py")
# https://github.com/InternLM/lmdeploy/blob/main/docs/en/advance/long_context.md
lmdeploy serve api_server "$path" \
    --model-name internlm2-chat-1_8b \
    --model-format hf \
    --quant-policy 0 \
    --server-name 127.0.0.1 \
    --server-port 23333  \
    --tp 1 \
    --cache-max-entry-count 0.1 \
    --rope-scaling-factor 2 \
    --session-len 160000 & sleep 30s

python "$script_dir/gradio_app_with_multiagent.py"
