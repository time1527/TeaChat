model_path=/home/pika/Downloads/1_8b4e1
code_path=/home/pika/Repo/opencompass
cd "$code_path"
for i in $(seq 10000 1000 27000); do
    rm -r "$model_path/last_eval$i"
    mkdir -p "$model_path/last_eval$i"
    python "$code_path/run.py" --datasets ceval_gen \
    --hf-path "$model_path/final$i" \
    --tokenizer-path "$model_path/final$i" \
    --tokenizer-kwargs padding_side='left' truncation='left' trust_remote_code=True \
    --model-kwargs trust_remote_code=True device_map='auto' \
    --max-seq-len 2048 --max-out-len 512 --batch-size 4 --num-gpus 1 --debug \
    --work-dir "$model_path/last_eval$i"
done



