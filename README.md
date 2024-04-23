# TeaChat

## 环境安装

创建虚拟环境：

```bash
conda create -n teachat python=3.10
```

安装依赖：

```bash
pip install -r requirements.txt
```

## v0.1计划及进展

* [ ] 预训练前评测
* [x] 增量预训练数据收集：2024/03/26
* [x] 增量预训练数据整理：2024/04/15
* [ ] 增量预训练
* [ ] 预训练后（SFT前）评测
* [x] SFT数据收集：2024/03/26
* [x] SFT数据整理：2024/04/15
* [ ] SFT
  * [x] internlm2_1.8b_chat + 垂类数据：2024/04/21

* [ ] SFT后评测
* [ ] RLHF
* [ ] 部署
* [x] RAG数据收集：2024/4/20
* [ ] RAG：ing
* [ ] Multi-Agent

## 致谢

感谢[书生浦语第二期训练营](https://github.com/InternLM/Tutorial/tree/camp2)
