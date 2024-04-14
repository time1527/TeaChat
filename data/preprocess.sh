#! /bin/bash

# on local
# rm hashes.txt
# rm /home/pika/Project/TeaChat/data/hashes.txt
# # mintest
# python /home/pika/Project/TeaChat/data/pt_main.py \
#     --input_dir /home/pika/Dataset/minpt/ \
#     --test_dir /home/pika/Dataset/opencompass/data/ \
#     --nf_threshold 5

# python /home/pika/Project/TeaChat/data/sft_main.py \
#     --input_dir /home/pika/Dataset/minsft/ \
#     --test_dir /home/pika/Dataset/opencompass/data/

python /home/pika/Project/TeaChat/data/pt_main.py \
    --input_dir /home/pika/Dataset/pt/ \
    --test_dir /home/pika/Dataset/opencompass/data/ \
    --nf_threshold 100

python /home/pika/Project/TeaChat/data/sft_main.py \
    --input_dir /home/pika/Dataset/sft/ \
    --test_dir /home/pika/Dataset/opencompass/data/



# # on intern studio
# # mintest
# python /root/TeaChat/data/pt_main.py \
#     --input_dir /root/dataset/minpt/ \
#     --test_dir /root/download/opencompass/data/ \
#     --nf_threshold 5

# python /root/TeaChat/data/sft_main.py \
#     --input_dir /root/dataset/minsft/ \
#     --test_dir /root/download/opencompass/data/


# python /root/TeaChat/data/pt_main.py \
#     --input_dir /root/dataset/pretrain/ \
#     --test_dir /root/download/opencompass/data/ \
#     --nf_threshold 100

# python /root/TeaChat/data/sft_main.py \
#     --input_dir /root/dataset/sft/ \
#     --test_dir /root/download/opencompass/data/