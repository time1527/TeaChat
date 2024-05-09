![logo](assets\logo.png)

# TeaChat
<a href="https://img.shields.io/badge/language-python-blue"><img src="https://img.shields.io/badge/language-python-blue" alt="Stars Badge"/></a>
<a href="https://github.com/time1527/TeaChat/stargazers"><img src="https://img.shields.io/github/stars/time1527/TeaChat" alt="Stars Badge"/></a>
<a href="https://github.com/time1527/TeaChat/network/members"><img src="https://img.shields.io/github/forks/time1527/TeaChat" alt="Forks Badge"/></a>
<a href="https://github.com/time1527/TeaChat/pulls"><img src="https://img.shields.io/github/issues-pr/time1527/TeaChat" alt="Pull Requests Badge"/></a>
<a href="https://github.com/time1527/TeaChat/issues"><img src="https://img.shields.io/github/issues/time1527/TeaChat" alt="Issues Badge"/></a>
<a href="https://github.com/time1527/TeaChat/graphs/contributors"><img alt="GitHub contributors" src="https://img.shields.io/github/contributors/time1527/TeaChat?color=2b9348"></a>
<a href="https://github.com/time1527/TeaChat/blob/master/LICENSE"><img src="https://img.shields.io/github/license/time1527/TeaChat?color=2b9348" alt="License Badge"/></a>

TeaChat是使用题库作为垂类语料库，涵盖数学、语文、英语、物理、化学、生物、政治、历史、地理九大高中学科，使用fine-tune、RAG、Multi-Agent技术，提供高考习题解答、解析功能，旨在响应深化教育改革、促进教育公平的发展理念，提供一款人人可用的免费教师AI，减小教育资源差距。

## Framework

coming soon...

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

## 基本目录

```bash
├── assets：头像和流程图
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
├── run.sh：lmdeploy serve + gradio_app
└── streamlit_app.backup
```

## 技术概览

数据处理：[datasketch](https://github.com/ekzhu/datasketch)

微调：[xtuner](https://github.com/InternLM/xtuner)

评测：[opencompass](https://github.com/open-compass/opencompass)

RAG：[langchain](https://github.com/langchain-ai/langchain)

multi-agent：[metagpt](https://github.com/geekan/MetaGPT)

前端：[gradio](https://github.com/gradio-app/gradio)

## v0.1进展

* [x] 增量预训练数据收集：2024/03/26
* [x] 增量预训练数据整理：2024/04/15
* [x] SFT前评测：2024/04/23
* [x] SFT数据收集：2024/03/26
* [x] SFT数据整理：2024/04/15
* [ ] SFT
  * [x] internlm2_1.8b_chat + 垂类数据：2024/04/21
  * [x] internlm2_1.8b_chat + 垂类数据 + 通用数据：2024/04/27
* [ ] SFT后评测：
  * [x] internlm2_1.8b_chat + 垂类数据：2024/04/23
  * [x] internlm2_1.8b_chat + 垂类数据 + 通用数据：：2024/05/05
* [x] RAG数据收集：2024/4/20
* [x] RAG：2024/04/26
* [ ] Multi-Agent：ing

## 致谢

感谢[书生浦语第二期训练营](https://github.com/InternLM/Tutorial/tree/camp2)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=time1527/TeaChat&type=Date)](https://star-history.com/#time1527/TeaChat&Date)
