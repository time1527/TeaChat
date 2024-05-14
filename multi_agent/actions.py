import asyncio

from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.environment import Environment
from metagpt.tools.search_engine import SearchEngine
from metagpt.tools import SearchEngineType
from metagpt.configs.search_config import SearchConfig

from metagpt.const import MESSAGE_ROUTE_TO_ALL, MESSAGE_ROUTE_TO_NONE

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder


import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.store import TextStore,VideoStore,QAStore

# 每个判断操作都需要聊天记录，取聊天记录从公共memory里取，公共memory怎么用的忘了（.history）
# 看debate实例
# memory = self.get_memories()
# context = "\n".join(f"{msg.sent_from}: {msg.content}" for msg in memory)

# 检索员检索信息所需的参数从收到的Message里取

class GetMajorAndKeypoint(Action):
    name: str = "GetMajor"

    major_list: list = ["语文","数学","英语","地理","历史","政治","物理","化学","生物"]

    CONDENSE_QUESTION_PROMPT: str = """给出以下聊天记录和后续问题，用中文将后续问题改写为一个独立的问题。
    聊天记录:{memory}
    后续输入:{instruction}
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
        prompt1 = self.CONDENSE_QUESTION_PROMPT.format(memory=memory, instruction=instruction)  # 从Agent Memory读取
        logger.info(f"***prompt1 is {prompt1}***")
        rsp_standalone_question = await self._aask(prompt1)
        logger.info(f"***rsp_standalone_question is {rsp_standalone_question}***")

        prompt2 = self.MAJOR_PROMPT_TEMPLATE.format(standalone_question=rsp_standalone_question, major_list=self.major_list)
        logger.info(f"***prompt2 is {prompt2}***")
        rsp_major = await self._aask(prompt2)
        logger.info(f"***rsp_major is {rsp_major}***")

        prompt3 = self.KEYPOINT_PROMPT_TEMPLATE.format(standalone_question=rsp_standalone_question)
        logger.info(f"***prompt3 is {prompt3}***")
        rsp_keypoint = await self._aask(prompt3)
        logger.info(f"***rsp_keypoint is {rsp_keypoint}***")

        return rsp_major, rsp_keypoint

class TextbookRetrievalJudge(Action):
    name: str = "TextbookRetrievalJudge"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)   # TypeError: TextbookRetrievalJudge.__init__() got an unexpected keyword argument 'context'
        self.use_text_prompt_template = """请判断以下聊天记录是否与文本高度相关。只允许输出一个字“是”或者“否”。
        聊天记录:{memory}
        文本:{text_rag_content}
        是否高度相关:
        """

    async def run(self, memory, text_rag_content) -> str:
        use_text_prompt = self.use_text_prompt_template.format(memory=memory, text_rag_content=text_rag_content)
        use_text_resp = await self._aask(use_text_prompt)
        use_text_resp_bool = True if "是" in use_text_resp else False

        return use_text_resp_bool

class VideoRetrievalJudge(Action):
    name: str = "VideoRetrievalJudge"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_video_prompt_template = """请判断以下聊天记录是否与文本高度相关。只允许输出一个字“是”或者“否”。
        聊天记录:{memory}
        文本:{video_rag_pc}
        是否高度相关:
        """

    async def run(self, memory, video_rag_page_content) -> str:
        use_video_prompt = self.use_video_prompt_template.format(memory=memory, video_rag_pc=video_rag_page_content)
        use_video_resp = await self._aask(use_video_prompt)
        use_video_resp_bool = True if "是" in use_video_resp else False

        return use_video_resp_bool

class QARetrievalJudge(Action):
    name: str = "QARetrievalJudge"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_qa_prompt_template = """请判断以下聊天记录是否与文本高度相关。只允许输出一个字“是”或者“否”。
        聊天记录:{memory}
        文本:{qa_rag_q}
        是否高度相关:
        """

    async def run(self, memory, qa_rag_q) -> str:
        use_qa_prompt = self.use_qa_prompt_template.format(memory=memory, qa_rag_q=qa_rag_q)
        use_qa_resp = await self._aask(use_qa_prompt)
        use_qa_resp_bool = True if "是" in use_qa_resp else False
        
        return use_qa_resp_bool


# class WebRetrieval(Action):
#     name: str = "WebRetrieval"

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.search_engine_config = {
#             "api_type": SearchEngineType.SERPER_GOOGLE, 
#             "run_func": None, 
#             "api_key": "478848b1b12bedc1d6d10d4f6fd3af7d",
#         }
#         self.search_engine = search_engine = SearchEngine.from_search_config(SearchConfig(**self.search_engine_config))
#         logger.info(f"***search_engine is {self.search_engine}***")
    
#     async def run(self, query: str):
#         search_res = await self.search_engine.run(query, as_string=False)
#         logger.info(f"***search_res is {search_res}***")
#         resp = search_res[0]['title']

#         # TODO: 信息提取，处理，可能要进网页提取，参考WebBrowseAndSummarize

#         return resp