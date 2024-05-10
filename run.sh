#!/bin/bash
# path=/home/pika/Model/Shanghai_AI_Laboratory/internlm2-chat-1_8b
path=/home/pika/Downloads/second/final_model/final40000
lmdeploy serve api_server "$path" --model-name internlm2-chat-1_8b --model-format hf --quant-policy 0 --server-name 127.0.0.1 --server-port 23333  --tp 1 --cache-max-entry-count 0.1 & sleep 30s
python /home/pika/Project/TeaChat/gradio_app.py 
