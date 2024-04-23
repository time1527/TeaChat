model_path=/home/pika/Downloads/1_8b4e1/final_model
work_path=/home/pika/Downloads/1_8b4e1/
code_path=/home/pika/Repo/opencompass
raw=/home/pika/Model/Shanghai_AI_Laboratory/internlm2-chat-1_8b
prefix=3last_eval
cd "$code_path"
for i in $(seq 10000 1000 27000); do
    rm -r "$work_path/$prefix/$prefix$i"
    mkdir -p "$work_path/$prefix/$prefix$i"
    python "$code_path/run.py" --datasets ceval_gen \
    --hf-path "$model_path/final$i" \
    --tokenizer-path "$model_path/final$i" \
    --tokenizer-kwargs padding_side='left' truncation='left' trust_remote_code=True \
    --model-kwargs trust_remote_code=True device_map='auto' \
    --max-seq-len 2048 --max-out-len 512 --batch-size 4 --num-gpus 1 --debug \
    --work-dir "$work_path/$prefix/$prefix$i"
done

python "$code_path/run.py" --datasets ceval_gen \
    --hf-path "$raw" \
    --tokenizer-path "$raw" \
    --tokenizer-kwargs padding_side='left' truncation='left' trust_remote_code=True \
    --model-kwargs trust_remote_code=True device_map='auto' \
    --max-seq-len 2048 --max-out-len 512 --batch-size 4 --num-gpus 1 --debug \
    --work-dir "$work_path/$prefix/$prefix0"


