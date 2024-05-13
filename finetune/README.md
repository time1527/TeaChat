## 创建虚拟环境

```bash
conda create -n xtuner0.1.17 python=3.10
conda activate xtuner0.1.17
cd ~
mkdir -p /root/xtuner0117 && cd /root/xtuner0117
git clone -b v0.1.17  https://github.com/InternLM/xtuner
cd /root/xtuner0117/xtuner
pip install -e '.[all]'
```
## 选择配置文件
```bash
cd ~/TeaChat/finetune/sft
xtuner list-cfg -p internlm2_chat_7b
xtuner copy-cfg internlm2_chat_7b_qlora_alpaca_e3 ./7b/
mv ./7b/internlm2_chat_7b_qlora_alpaca_e3_copy.py ./7b/first.py
```
## 修改配置文件
```diff
# 模型地址
- pretrained_model_name_or_path = 'internlm/internlm2-chat-7b'
+ pretrained_model_name_or_path = '/root/model/internlm2-chat-7b'

# 数据集地址
- alpaca_en_path = 'tatsu-lab/alpaca'
+ alpaca_en_path = '/root/dataset/xxx.json'

# 数据集参数
- from xtuner.dataset.map_fns import alpaca_map_fn, template_map_fn_factory
+ from xtuner.dataset.map_fns import openai_map_fn, template_map_fn_factory

- dataset=dict(type=load_dataset, path=alpaca_en_path),
+ dataset=dict(type=load_dataset, path='json', data_files=dict(train=alpaca_en_path)),

- dataset_map_fn=alpaca_map_fn,
+ dataset_map_fn=openai_map_fn,
```
其余可修改：
`max_epochs`；`save_steps`；`save_total_limit`；`evaluation_freq`；`evaluation_inputs`

## 训练
```bash
xtuner train /root/github/TeaChat/finetune/sft/7b/first.py --work-dir /root/ft/ --deepspeed deepspeed_zero2
```

## 续训

```bash
xtuner train /root/github/TeaChat/finetune/sft/7b/first.py --work-dir /root/ft/ --resume /root/ft/iter_3000.pth --deepspeed deepspeed_zero2
```

## 转换
```bash
mkdir -p /root/ft/hf
xtuner convert pth_to_hf /root/github/TeaChat/finetune/sft/7b/first.py /root/ft/iter_14000.pth /root/ft/hf
```

## 整合
```bash
mkdir -p /root/ft/final
xtuner convert merge /root/model/internlm2-chat-7b /root/ft/hf /root/ft/final
```