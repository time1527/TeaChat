from langchain.llms.base import LLM
from typing import Any, List, Optional
from langchain.callbacks.manager import CallbackManagerForLLMRun
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


class InternLM(LLM):
    # 基于本地 InternLM 自定义 LLM 类
    tokenizer: AutoTokenizer = None
    model: AutoModelForCausalLM = None

    def __init__(self, model_path: str):
        # model_path: InternLM 模型路径
        # 从本地初始化模型
        super().__init__()
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print("正在从本地加载模型...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path, trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, trust_remote_code=True
        ).to(torch.bfloat16)
        self.model.to(device)
        self.model = self.model.eval()
        print("完成本地模型的加载...")

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any
    ):
        # 重写调用函数
        # system_prompt = """You are an AI assistant whose name is InternLM (书生·浦语).
        # - InternLM (书生·浦语) is a conversational language model that is developed by Shanghai AI Laboratory (上海人工智能实验室). It is designed to be helpful, honest, and harmless.
        # - InternLM (书生·浦语) can understand and communicate fluently in the language chosen by the user such as English and 中文.
        # """

        system_prompt = """你是一名重点高中的教师，同时也是一名家庭教师，你擅长高中数学，高中语文，高中英语，高中政治，高中历史，高中地理，高中物理，高中化学，高中生物。你能理解用户所输入的中国高考问题，并详细流利地给出该题目的答案和解析。"""
        messages = [(system_prompt, "")]
        response, history = self.model.chat(self.tokenizer, prompt, history=messages)
        return response

    @property
    def _llm_type(self) -> str:
        return "InternLM"
