import asyncio

from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.environment import Environment

from metagpt.const import MESSAGE_ROUTE_TO_ALL, MESSAGE_ROUTE_TO_NONE

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rag.store import TextStore,VideoStore,QAStore

classroom = Environment()

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


class Classifier(Role):
    name: str = "Classifier"
    profile: str = "Classifier"

    def __init__(self, use_text = False, use_video = False, use_qa = False , **kwargs):
        super().__init__(**kwargs)
        self.use_text = use_text
        self.use_video = use_video
        self.use_qa = use_qa
        self.set_actions([GetMajorAndKeypoint])
        self._watch([UserRequirement])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self.rc.todo}")
        todo = self.rc.todo

        memory = self.get_memories()
        logger.info(f"***memory is {memory}***")


        for msg in memory:
            if msg.role =="Human":
                # 这就相当于取最后一条输入，最新的输入
                instruction = msg.content
        logger.info(f"***instruction is {instruction}***")

        rsp_major, rsp_keypoint = await GetMajorAndKeypoint().run(memory, instruction)

        #######################################333
        # send_roles = []
        # if self.use_text:
        #     send_roles.append("TextbookRetriever")
        # if self.use_video:
        #     send_roles.append("VideoRetriever")
        # if self.use_qa:
        #     send_roles.append("QARetriever")

        # msg_major = Message(content=rsp_major, role=self.profile, cause_by=type(todo), 
        #         sent_from = self.name, send_to=send_roles)
        # msg_keypoint = Message(content=rsp_keypoint, role=self.profile, cause_by=type(todo), 
        #         sent_from = self.name, send_to=send_roles)
        # self.rc.env.publish_message(msg_major)
        # self.rc.env.publish_message(msg_keypoint)
        #################################################


        # 在这里指定分发给哪个检索员
        if self.use_text:
            logger.info(f"***ok***")
            msg_major = Message(content=rsp_major, role=self.profile, cause_by=type(todo), 
                sent_from = self.name, send_to="TextbookRetriever")
            msg_keypoint = Message(content=rsp_keypoint, role=self.profile, cause_by=type(todo), 
                sent_from = self.name, send_to="TextbookRetriever")
            self.rc.env.publish_message(msg_major)
            self.rc.env.publish_message(msg_keypoint)
        if self.use_video:
            logger.info(f"***okok***")
            msg_major = Message(content=rsp_major, role=self.profile, cause_by=type(todo), 
                sent_from = self.name, send_to="VideoRetriever")
            msg_keypoint = Message(content=rsp_keypoint, role=self.profile, cause_by=type(todo), 
                sent_from = self.name, send_to="VideoRetriever")
            self.rc.env.publish_message(msg_major)
            self.rc.env.publish_message(msg_keypoint)
        if self.use_qa:
            logger.info(f"***okokok***")
            msg_major = Message(content=rsp_major, role=self.profile, cause_by=type(todo), 
                sent_from = self.name, send_to="QARetriever")
            msg_keypoint = Message(content=rsp_keypoint, role=self.profile, cause_by=type(todo), 
                sent_from = self.name, send_to="QARetriever")
            self.rc.env.publish_message(msg_major)
            self.rc.env.publish_message(msg_keypoint)
        
        return Message(content="dummy message", send_to=MESSAGE_ROUTE_TO_NONE) # 消息已发，所以return一个空消息就行
    

# 如果每个人都能watch到消息，那不就都能被触发了，但如果不send_to=MESSAGE_ROUTE_TO_ALL，其他Role看不到memory。要改一下 _observe
class TextbookRetriever(Role):
    name: str = "TextbookRetriever"
    profile: str = "Retriever"

    def __init__(self, textstore = None):
        super().__init__()
        self.textstore = textstore
        self.set_actions([TextbookRetrievalJudge])
        self._watch([GetMajorAndKeypoint])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self.rc.todo}")
        todo = self.rc.todo

        memory = self.get_memories()
        # logger.info(f"***memory is {memory}***")
        # for msg in memory:
        #     logger.info(f"***msg send_to is {type(msg.send_to)}***")
        memory_text = ''
        for msg in  memory:
            # logger.info(f"***msg.sent_from is {type(msg.sent_from)}***")
            if 'UserRequirement' in msg.sent_from:
                memory_text += f'User: {msg.content}'
        # logger.info(f"***memory_text is {memory_text}***")
        msgs = [msg.content for msg in memory if "TextbookRetriever" in msg.send_to]
        # logger.info(f"***msgs is {msgs}***")
        major = msgs[-2]
        key_resp = msgs[-1]

        text_rag_page_content, text_rag_content = self.textstore.query(key_resp, major)

        use_text_resp_bool = False
        if text_rag_page_content and text_rag_content:
            use_text_resp_bool = await TextbookRetrievalJudge().run(memory_text, text_rag_content)
        
        text_res = text_rag_content if use_text_resp_bool else ""
        logger.info(f"***text_res is {text_res}***")

        msg = Message(content=text_res, role=self.profile, cause_by=type(todo), 
            sent_from=self.name, send_to="Human")

        return msg

class VideoRetriever(Role):
    name: str = "VideoRetriever"
    profile: str = "Retriever"

    def __init__(self, videostore = None, **kwargs):
        super().__init__(**kwargs)
        self.videostore = videostore
        self.set_actions([VideoRetrievalJudge])
        self._watch([GetMajorAndKeypoint])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self.rc.todo}")
        todo = self.rc.todo

        memory = self.get_memories()
        memory_text = ''
        for msg in  memory:
            if 'UserRequirement' in msg.sent_from:
                memory_text += f'User: {msg.content}'
        msgs = [msg.content for msg in memory if "VideoRetriever" in msg.send_to]
        major = msgs[-2]
        key_resp = msgs[-1]
        video_rag_page_content, video_rag_url, video_rag_up = self.videostore.query(key_resp,major)
        
        use_video_resp_bool = False
        if video_rag_page_content:
            use_video_resp_bool = await VideoRetrievalJudge().run(memory_text, video_rag_page_content)
        
        video_res = f"可参考bilibili up主 {video_rag_up} 的视频：{video_rag_url}" if use_video_resp_bool else ""
        logger.info(f"***video_res is {video_res}***")
        msg = Message(content=video_res, role=self.profile, cause_by=type(todo), 
            sent_from=self.name, send_to="Human")

        return msg


class QARetriever(Role):
    name: str = "QARetriever"
    profile: str = "Retriever"

    def __init__(self, qastore = None, **kwargs):
        super().__init__(**kwargs)
        self.qastore = qastore
        self.set_actions([QARetrievalJudge])
        self._watch([GetMajorAndKeypoint])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self.rc.todo}")
        todo = self.rc.todo

        memory = self.get_memories()
        memory_text = ''
        for msg in  memory:
            if 'UserRequirement' in msg.sent_from:
                memory_text += f'User: {msg.content}'
        for msg in memory:
            if msg.role =="Human":
                instruction = msg.content
        msgs = [msg.content for msg in memory if "QARetriever" in msg.send_to]
        major = msgs[-2]
        key_resp = msgs[-1]

        qa_rag_q, qa_rag_a = self.qastore.query(instruction, major)
        
        use_qa_resp_bool = False
        if qa_rag_q:
            use_qa_resp_bool = await QARetrievalJudge().run(memory_text, qa_rag_q)
        
        qa_res = "\n".join(["相似题目/例题：", qa_rag_q, "解答：", qa_rag_a]) if use_qa_resp_bool else ""
        logger.info(f"***qa_res is {qa_res}***")
        msg = Message(content=qa_res, role=self.profile, cause_by=type(todo), 
            sent_from=self.name, send_to="Human")

        return msg

from metagpt.tools.search_engine import SearchEngine

class WebRetrieval(Action):
    name: str = "WebRetrieval"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_engine = SearchEngine.from_search_config(self.config.search, proxy=self.config.proxy)
    
    async def run(self, query: str):
        resp = await self.search_engine.run(query, as_string=False)

        return resp

class WebRetriever(Role):
    # https://docs.deepwisdom.ai/main/zh/guide/use_cases/agent/researcher.html
    name: str = "WebRetriever"
    profile: str = "Retriever"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WebRetrieval])
        self._watch([GetMajorAndKeypoint])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self.rc.todo}")
        todo = self.rc.todo

        # 这个instruction从分类员发送的最新Message里取
        instruction = ''

        resp = await WebRetrieval().run(instruction)
        msg = Message(content=resp, role=self.profile, cause_by=type(todo), 
            sent_from=self.name, send_to="Human")

        return msg

class TestRole(Role):
    name: str = "TestRole"
    profile: str = "TestRole"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([])
        self._watch([GetMajorAndKeypoint])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self.rc.todo}")
        
        return Message(content="dummy message", send_to=MESSAGE_ROUTE_TO_NONE) # 消息已发，所以return一个空消息就行



async def main(topic: str, n_round=3):
    embedding = HuggingFaceEmbeddings(
        model_name = '/root/model/bce-embedding-base_v1',
        encode_kwargs = {'normalize_embeddings': True}
    )
    reranker = HuggingFaceCrossEncoder(model_name = '/root/model/bce-reranker-base_v1')

    textstore = TextStore(embedding, reranker)
    videostore = VideoStore(embedding, reranker)
    # qastore = QAStore(embedding, reranker)

    classroom.add_roles([
        Classifier(use_text=True, use_video=True, use_qa=False),      # 先测试分类员能否分类
        TextbookRetriever(textstore=textstore), 
        VideoRetriever(videostore=videostore), 
        # QARetriever(qastore=qastore), 
        # WebRetriever()
        # TestRole()
    ])
    classroom.publish_message(
        Message(role="Human", content=topic, cause_by=UserRequirement,
                sent_from = UserRequirement, send_to=MESSAGE_ROUTE_TO_ALL),     # 'Classifier' 的话其他Role看不见
        peekable=False,
    )

    while n_round > 0:
        # self._save()
        n_round -= 1
        logger.debug(f"max {n_round=} left.")

        await classroom.run()
    return classroom.history

asyncio.run(main(topic='什么是氧化还原反应'))