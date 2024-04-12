#! /bin/bash

# python /home/pika/Project/TeaChat/data/pt_main.py \
#     --input_dir /home/pika/Project/TeaChat/data/mintest/ \
#     --test_dir /home/pika/Project/TeaChat/data/OpenCompassData/ \
#     --nf_threshold 5

python /home/pika/Project/TeaChat/data/sft_main.py \
    --input_dir /home/pika/Project/TeaChat/data/mintest/ \
    --test_dir /home/pika/Project/TeaChat/data/OpenCompassData/


# python /home/pika/Project/TeaChat/data/pt_main.py \
#     --input_dir /home/pika/Project/TeaChat/data/pt/ \
#     --test_dir /home/pika/Project/TeaChat/data/OpenCompassData/ \
#     --nf_threshold 100

