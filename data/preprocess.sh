#! /bin/bash

# # mintest
python /root/TeaChat/data/pt_main.py \
    --input_dir /root/dataset/minpt/ \
    --test_dir /root/download/opencompass/data/ \
    --nf_threshold 5

python /root/TeaChat/data/sft_main.py \
    --input_dir /root/dataset/minsft/ \
    --test_dir /root/download/opencompass/data/


# python /root/TeaChat/data/pt_main.py \
#     --input_dir /root/dataset/pretrain/ \
#     --test_dir /root/download/opencompass/data/ \
#     --nf_threshold 100

# python /root/TeaChat/data/sft_main.py \
#     --input_dir /root/dataset/sft/ \
#     --test_dir /root/download/opencompass/data/