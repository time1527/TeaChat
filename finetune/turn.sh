# i=10000
cfg=/home/pika/Project/TeaChat/finetune/sft/internlm2_chat_1_8b_qlora_alpaca_e3_copy.py
raw=/home/pika/Model/Shanghai_AI_Laboratory/internlm2-chat-1_8b
path=/home/pika/Downloads/1_8b4e1
cd "$path"
for i in $(seq 10000 1000 27000); do
    mkdir -p "hf$i"
    xtuner convert pth_to_hf "$cfg"  "$path/iter_$i.pth" "$path/hf$i"
    mkdir -p "final$i"
    xtuner convert merge "$raw" "$path/hf$i" "$path/final$i"
done
