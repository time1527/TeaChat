import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from metagpt.actions import Action
from metagpt.logs import logger


class GetMajorAndKeypoint(Action):
    name: str = "GetMajor"

    major_list: list = ["语文","数学","英语","地理","历史","政治","物理","化学","生物"]

    CONDENSE_QUESTION_PROMPT_TEMPLATE: str = """给出以下聊天记录和后续问题，用中文将后续问题改写为一个独立的问题。
    聊天记录:{memory}，
    后续输入:{instruction}，
    独立的问题:
    """
    MAJOR_PROMPT_TEMPLATE: str = """请判断以下文本属于哪一学科，只能输出两个字的回答。
    文本：{standalone_question}，
    选项：{major_list}，
    答案：
    """
    KEYPOINT_PROMPT_TEMPLATE: str = """请判断以下文本考察什么知识点。请只输出知识点，不需要输出分析步骤。
    文本：{standalone_question}，
    知识点：
    """

    async def run(self, memory, instruction):
        prompt1 = self.CONDENSE_QUESTION_PROMPT_TEMPLATE.format(memory=memory, instruction=instruction)  # 从Agent Memory读取
        logger.info(f"CONDENSE_QUESTION_PROMPT: {prompt1}")
        rsp_standalone_question = await self._aask(prompt1)
        logger.info(f"STANDALONE_QUESTION: {rsp_standalone_question}")

        prompt2 = self.MAJOR_PROMPT_TEMPLATE.format(standalone_question=rsp_standalone_question, major_list=self.major_list)
        logger.info(f"MAJOR_PROMPT: {prompt2}")
        # TODO: 如果模型不听话返回了其他文字/多学科怎么处理
        rsp_major = await self._aask(prompt2)
        logger.info(f"MAJOR: {rsp_major}")

        prompt3 = self.KEYPOINT_PROMPT_TEMPLATE.format(standalone_question=rsp_standalone_question)
        logger.info(f"KEYPOINT_PROMPT: {prompt3}")
        rsp_keypoint = await self._aask(prompt3)
        logger.info(f"KEYPOINT: {rsp_keypoint}")

        return rsp_standalone_question,rsp_major, rsp_keypoint


class Judge(Action):
    name: str = "Judge"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt_template = """请判断以下聊天记录是否与文本高度相关。只允许输出一个字“是”或者“否”。
        聊天记录:{messages}
        文本:{text}
        是否高度相关:
        """

    async def run(self, messages, text) -> str:
        prompt = self.prompt_template.format(messages=messages, text=text)
        rsp = await self._aask(prompt)
        use = True if "是" in rsp else False
        return use