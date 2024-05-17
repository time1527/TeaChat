import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from .reaction import ReAction
from metagpt.logs import logger


class GetMajorAndKeypoint(ReAction):
    name: str = "GetMajor"

    major_list: list = ["语文","数学","英语","地理","历史","政治","物理","化学","生物"]

    CONDENSE_QUESTION_PROMPT_TEMPLATE: str = """给出以下聊天记录和后续问题，用中文将后续问题改写为一个独立的问题。
    聊天记录:{history}，
    后续问题:{instruction}，
    独立的问题:
    """
    MAJOR_PROMPT_TEMPLATE: str = """请判断以下文本属于哪一学科，只能输出两个字的回答。
    文本：{standalone_question}，
    选项：{major_list}，
    答案：
    """
    KEYPOINT_PROMPT_TEMPLATE: str = """请判断以下文本考察什么知识点。请只输出知识点，不需要输出分析步骤。字数在20字以内。字数在20字以内。字数在20字以内。
    文本：{standalone_question}，
    知识点：
    """

    async def run(self, history, instruction):
        # 1. history + instruction -> standalone_question
        prompt1 = self.CONDENSE_QUESTION_PROMPT_TEMPLATE.format(history=history, instruction=instruction) 
        logger.info(f"CONDENSE_QUESTION_PROMPT: {prompt1}")
        rsp_standalone_question = await self._aask(prompt1,stream = False)
        logger.info(f"STANDALONE_QUESTION: {rsp_standalone_question}")

        # 2.1 standalone_question -> major
        prompt2 = self.MAJOR_PROMPT_TEMPLATE.format(standalone_question=rsp_standalone_question, major_list=self.major_list)
        logger.info(f"MAJOR_PROMPT: {prompt2}")
        # TODO: 如果模型返回了其他多余文字/多学科的处理
        rsp_major = await self._aask(prompt2,stream = False)
        found_majors = [major for major in self.major_list if major in rsp_major]
        if len(found_majors) == 1:rsp_final_major = found_majors[0]
        else: rsp_final_major = ""
        logger.info(f"MAJOR: {rsp_final_major}")

        # 2.2 standalone_question -> keypoint
        prompt3 = self.KEYPOINT_PROMPT_TEMPLATE.format(standalone_question=rsp_standalone_question)
        logger.info(f"KEYPOINT_PROMPT: {prompt3}")
        rsp_keypoint = await self._aask(prompt3,stream = False)
        logger.info(f"KEYPOINT: {rsp_keypoint}")

        return rsp_standalone_question,rsp_final_major, rsp_keypoint


class Judge(ReAction):
    name: str = "Judge"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg_prompt_template = """请判断以下文本是否与聊天记录高度相关。只允许输出一个字“是”或者“否”。
        聊天记录:{messages}，
        文本:{text}，
        是否高度相关:
        """

        self.stq_prompt_template = """请判断以下文本是否与问题高度相关。只允许输出一个字“是”或者“否”。
        问题:{stq}，
        文本:{text}，
        是否高度相关:
        """

    async def run(self, chat_messages, stq,text) -> str:
        # logger.info(f"CHAT_MESSAGES:{chat_messages}")
        # logger.info(f"Judge WILL REVIEW:{text}")
        prompt1 = self.msg_prompt_template.format(messages=chat_messages, text=text)
        rsp1 = await self._aask(prompt1,stream = False)
        logger.info(f"JUDGE OUTPUT1: {rsp1}")
        # TODO：更“高明”的处理，考虑它输出“不是”
        use1 = True if "是" in rsp1 else False

        prompt2 = self.stq_prompt_template.format(stq = stq, text=text)
        rsp2 = await self._aask(prompt2,stream = False)
        logger.info(f"JUDGE OUTPUT2: {rsp2}")
        use2 = True if "是" in rsp2 else False

        return use1 or use2