#! /bin/bash

# on local
# # mintest
# python /home/pika/Project/TeaChat/data/pt_main.py \
#     --input_dir /home/pika/Dataset/minpt/ \
#     --test_dir /home/pika/Dataset/opencompass/data/ \
#     --nf_threshold 5

# python /home/pika/Project/TeaChat/data/sft_main.py \
#     --input_dir /home/pika/Dataset/minsft/ \
#     --test_dir /home/pika/Dataset/opencompass/data/

# python /home/pika/Project/TeaChat/data/pt_main.py \
#     --input_dir /home/pika/Dataset/pt/ \
#     --test_dir /home/pika/Dataset/opencompass/data/ \
#     --nf_threshold 100

python /home/pika/Project/TeaChat/data/sft_main.py \
    --input_dir /home/pika/Dataset/sft/ \
    --test_dir /home/pika/Dataset/opencompass/data/