#!/bin/bash
path=/root/model/internlm2-chat-1_8b
lmdeploy serve api_server "$path" --model-name internlm2-chat-1_8b --model-format hf --quant-policy 0 --server-name 0.0.0.0 --server-port 23333  --tp 1 --cache-max-entry-count 0.1 & sleep 30s
python /root/github/TeaChat/test/test_multi_agent.py