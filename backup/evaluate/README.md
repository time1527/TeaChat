## 创建虚拟环境
```bash
conda create -n opencompass python=3.10
conda activate opencompass
cd ~
git clone -b 0.2.4 https://github.com/open-compass/opencompass
cd opencompass
pip install -e .
pip install -r requirements.txt
pip install protobuf
```
## 下载评测数据
```bash
cd ~/opencompass
wget https://github.com/open-compass/opencompass/releases/download/0.2.2.rc1/OpenCompassData-core-20240207.zip
unzip OpenCompassData-core-20240207.zip
```
## 修改数据集配置
以ceval为例：
```diff
# few-shot/zero-shot
- from opencompass.openicl.icl_retriever import FixKRetriever
+ from opencompass.openicl.icl_retriever import FixKRetriever,ZeroRetriever

# 注释掉非高中内容的数据

# 修改prompt
- f"以下是中国关于{_ch_name}考试的单项选择题，请选出其中的正确答案。\n{{question}}\nA. {{A}}\nB. {{B}}\nC. {{C}}\nD. {{D}}\n答案: "
+ f"以下是中国关于{_ch_name}考试的单项选择题，请直接选出其中的正确答案。\n{{question}}\nA. {{A}}\nB. {{B}}\nC. {{C}}\nD. {{D}}\n答案: "

# 修改few-shot/zero-shot
- retriever=dict(type=FixKRetriever, fix_id_list=[0, 1, 2, 3, 4]),
+ retriever=dict(type=ZeroRetriever),
```
## 评测
```bash
python /root/opencompass/run.py --datasets ceval_gen --hf-path /root/share/new_models/Shanghai_AI_Laboratory/internlm2-chat-7b --tokenizer-path /root/share/new_models/Shanghai_AI_Laboratory/internlm2-chat-7b --tokenizer-kwargs padding_side='left' truncation='left' trust_remote_code=True --model-kwargs trust_remote_code=True device_map='auto' --max-seq-len 1024 --max-out-len 16 --batch-size 8 --num-gpus 1 --work-dir /root/github/TeaChat/evaluate/7b/ceval_gen_first_16 --debug
```
## 查看结果
在`/root/github/TeaChat/evaluate/7b/ceval_gen_first_16/20240509_221051/summary/summary_20240509_221051.txt`中可查看结果：
```txt
ceval-high_school_mathematics: {'accuracy': 5.555555555555555}
ceval-high_school_physics: {'accuracy': 42.10526315789473}
ceval-high_school_chemistry: {'accuracy': 31.57894736842105}
ceval-high_school_biology: {'accuracy': 21.052631578947366}
ceval-high_school_politics: {'accuracy': 52.63157894736842}
ceval-high_school_geography: {'accuracy': 52.63157894736842}
ceval-high_school_chinese: {'accuracy': 57.89473684210527}
ceval-high_school_history: {'accuracy': 65.0}
```
