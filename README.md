<div align="center">
  <a href="https://github.com/time1527/TeaChat">
    <img src="assets/logo.png" alt="Logo" width="100%">
  </a>
</div>

# TeaChat
<a href="https://img.shields.io/badge/language-python-blue"><img src="https://img.shields.io/badge/language-python-blue" alt="Stars Badge"/></a>
<a href="https://github.com/time1527/TeaChat/stargazers"><img src="https://img.shields.io/github/stars/time1527/TeaChat" alt="Stars Badge"/></a>
<a href="https://github.com/time1527/TeaChat/network/members"><img src="https://img.shields.io/github/forks/time1527/TeaChat" alt="Forks Badge"/></a>
<a href="https://github.com/time1527/TeaChat/pulls"><img src="https://img.shields.io/github/issues-pr/time1527/TeaChat" alt="Pull Requests Badge"/></a>
<a href="https://github.com/time1527/TeaChat/issues"><img src="https://img.shields.io/github/issues/time1527/TeaChat" alt="Issues Badge"/></a>
<a href="https://github.com/time1527/TeaChat/blob/master/LICENSE"><img src="https://img.shields.io/github/license/time1527/TeaChat?color=2b9348" alt="License Badge"/></a>

<!--
<a href="https://github.com/time1527/TeaChat/graphs/contributors"><img alt="GitHub contributors" src="https://img.shields.io/github/contributors/time1527/TeaChat?color=2b9348"></a>
-->

TeaChat使用题库作为垂类语料库，涵盖数学、语文、英语、物理、化学、生物、政治、历史、地理九大高中学科，使用fine-tune、RAG、Multi-Agent技术，提供高考习题解答、解析功能，旨在响应深化教育改革、促进教育公平的发展理念，提供一款人人可用的免费教师AI，减小教育资源差距。

## Framework

<img src="./assets/framework.png" style="zoom:50%;" />

## QuickStart

创建虚拟环境：

```bash
conda create -n teachat python=3.10
conda activate teachat
```

获取项目：

```bash
git clone https://github.com/time1527/TeaChat.git
cd TeaChat
```

安装依赖：

```bash
pip install -r requirements.txt
```

运行：

```bash
bash run.sh
```

## Catalogue

```bash
├── assets：图片
├── data：增量预训练、sft数据处理
├── evaluate：评估
├── finetune：微调config
├── gradio_app.py：前端
├── LICENSE
├── ocr
├── rag：检索
├── rag_data：RAG数据整理
├── README.md
├── requirements.txt
└── run.sh：lmdeploy serve + gradio_app
```

* [data](./data/README.md)：使用minhash在数据集间、数据集内模糊去重，使用精确去重和模糊去重两种方式将训练数据集相对于垂类评测集去重
* [evaluate](./evaluate/README.md)：使用AGIeval、GAOKAO-Bench、cmmlu、ceval中的高中部分作为垂类评测集，采用zero-shot的方式对微调后的模型展开评测
* [finetune](./finetune/README.md)：使用[YeungNLP/firefly-train-1.1M](https://huggingface.co/datasets/YeungNLP/firefly-train-1.1M)和[QingyiSi/Alpaca-CoT](https://huggingface.co/datasets/QingyiSi/Alpaca-CoT)中的[CoT_data.json](https://huggingface.co/datasets/QingyiSi/Alpaca-CoT/blob/main/Chain-of-Thought/CoT_data.json)作为通用数据集，使用[WanJuan1.0](https://opendatalab.com/OpenDataLab/WanJuan1_dot_0)中的高中数据作为垂类数据集，在internLM2-chat-1_8b的基础上通过QLoRA进行有监督微调
* [rag_data](./rag_data)：
  * 视频链接数据：爬取bilibili视频url
  * 知识点数据：gpt识别人教版课本目录，人工检查，根据页码提取pdf内容
  * QA数据：[WanJuan1.0](https://opendatalab.com/OpenDataLab/WanJuan1_dot_0)中的高中数据
* [rag](./rag)：
  * 元数据筛选：改写langchain的`BM25Retriever`，为其添加元数据筛选功能
  * 混合检索：`BM25FilterRetriever` + `FAISS.as_retriever()`
  * 重排序

## v0.1

* [x] 增量预训练数据收集：2024/03/26
* [x] 增量预训练数据整理：2024/04/15
* [x] SFT前评测：2024/04/23
* [x] SFT数据收集：2024/03/26
* [x] SFT数据整理：2024/04/15
* [ ] SFT
  * [x] internlm2_1.8b_chat + 垂类数据：2024/04/21
  * [x] internlm2_1.8b_chat + 垂类数据 + 通用数据：2024/04/27
  * [x] “internlm2_1.8b_chat + 垂类数据 + 通用数据” + 垂类数据：2024/05/07
* [ ] SFT后评测：
  * [x] internlm2_1.8b_chat + 垂类数据：2024/04/23
  * [x] internlm2_1.8b_chat + 垂类数据 + 通用数据：2024/05/05
  * [x] “internlm2_1.8b_chat + 垂类数据 + 通用数据” + 垂类数据：2024/05/07
* [x] RAG数据收集：2024/4/20
* [x] RAG：2024/04/26
* [ ] Multi-Agent：ing

## 致谢

感谢[书生浦语第二期训练营](https://github.com/InternLM/Tutorial/tree/camp2)

<!--
[![Star History Chart](https://api.star-history.com/svg?repos=time1527/TeaChat&type=Date)](https://star-history.com/#time1527/TeaChat&Date)
-->