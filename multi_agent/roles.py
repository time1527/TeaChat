import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from metagpt.actions import UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.const import  MESSAGE_ROUTE_TO_NONE

from .actions import GetMajorAndKeypoint, Judge#TextbookRetrievalJudge, VideoRetrievalJudge, QARetrievalJudge#, WebRetrieval

class Classifier(Role):
    name: str = "Classifier"
    profile: str = "Classifier"

    def __init__(self, use_text = False, use_video = False, use_qa = False, use_web = False , **kwargs):
        super().__init__(**kwargs)
        self.use_text = use_text
        self.use_video = use_video
        self.use_qa = use_qa
        self.use_web = use_web
        self.set_actions([GetMajorAndKeypoint])
        self._watch([UserRequirement])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self.rc.todo}")
        todo = self.rc.todo

        memory = self.get_memories()
        logger.info(f"MEMORY: {memory}***")

        for msg in memory:
            if msg.role =="Human":
                # 这就相当于取最后一条输入，最新的输入
                instruction = msg.content
        logger.info(f"INSTRUCTION: {instruction}***")

        stq,major,keypoint= await GetMajorAndKeypoint().run(memory, instruction)

        send_roles = []
        if self.use_text:
            send_roles.append("TextbookRetriever")
        if self.use_video:
            send_roles.append("VideoRetriever")
        if self.use_qa:
            send_roles.append("QARetriever")
        if self.use_web:
            send_roles.append("WebRetriever")
        logger.info(f'messages will be sent to {send_roles}')

        msg_stq = Message(content=stq, role=self.profile, cause_by=type(todo), 
                sent_from = self.name, send_to=send_roles)
        msg_major = Message(content=major, role=self.profile, cause_by=type(todo), 
                sent_from = self.name, send_to=send_roles)
        msg_keypoint = Message(content=keypoint, role=self.profile, cause_by=type(todo), 
                sent_from = self.name, send_to=send_roles)
        
        self.rc.env.publish_message(msg_stq)
        self.rc.env.publish_message(msg_major)
        self.rc.env.publish_message(msg_keypoint)

        return Message(content="dummy message", send_to=MESSAGE_ROUTE_TO_NONE)
    

# 如果每个人都能watch到消息，那不就都能被触发了，但如果不send_to=MESSAGE_ROUTE_TO_ALL，其他Role看不到memory。要改一下 _observe
class TextbookRetriever(Role):
    name: str = "TextbookRetriever"
    profile: str = "TextbookRetriever"

    def __init__(self, textstore,**kwargs):
        super().__init__(**kwargs)
        self.textstore = textstore
        self.set_actions([Judge])
        self._watch([GetMajorAndKeypoint])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self.rc.todo}")
        todo = self.rc.todo

        memory = self.get_memories()
        # logger.info(f"***memory is {memory}***")
        # for msg in memory:
        #     logger.info(f"***msg send_to is {type(msg.send_to)}***")
        memory_text = ''
        for msg in memory:
            # logger.info(f"***msg.sent_from is {type(msg.sent_from)}***")
            if 'UserRequirement' in msg.sent_from:
                memory_text += f'User: {msg.content}'
        # logger.info(f"***memory_text is {memory_text}***")
        msgs = [msg.content for msg in memory if "TextbookRetriever" in msg.send_to]
        # logger.info(f"***msgs is {msgs}***")
        major = msgs[-2]
        keypoint = msgs[-1]

        text_rag_page_content, text_rag_content = self.textstore.query(keypoint, major)

        use_text = False
        if text_rag_page_content and text_rag_content:
            use_text = await Judge().run(memory_text, text_rag_content)
        
        text_res = text_rag_content if use_text else ""
        logger.info(f"RAG TEXT: {text_res}")

        msg = Message(content=text_res, role=self.profile, cause_by=type(todo), 
            sent_from=self.name, send_to="Human")
        return msg

class VideoRetriever(Role):
    name: str = "VideoRetriever"
    profile: str = "VideoRetriever"

    def __init__(self, videostore, **kwargs):
        super().__init__(**kwargs)
        self.videostore = videostore
        self.set_actions([Judge])
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
        keypint = msgs[-1]

        video_rag_page_content, video_rag_url, video_rag_up = self.videostore.query(keypint,major)
        
        use_video = False
        if video_rag_page_content:
            use_video = await Judge().run(memory_text, video_rag_page_content)
        
        video_res = f"可参考bilibili up主 {video_rag_up} 的视频：{video_rag_url}" if use_video else ""
        logger.info(f"RAG VIDEO: {video_res}")
        msg = Message(content=video_res, role=self.profile, cause_by=type(todo), 
            sent_from=self.name, send_to="Human")
        return msg


class QARetriever(Role):
    name: str = "QARetriever"
    profile: str = "QARetriever"

    def __init__(self, qastore, **kwargs):
        super().__init__(**kwargs)
        self.qastore = qastore
        self.set_actions([Judge])
        self._watch([GetMajorAndKeypoint])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self.rc.todo}")
        todo = self.rc.todo

        memory = self.get_memories()
        memory_text = ''
        for msg in memory:
            if 'UserRequirement' in msg.sent_from:
                memory_text += f'User: {msg.content}'
        for msg in memory:
            if msg.role =="Human":
                instruction = msg.content
        msgs = [msg.content for msg in memory if "QARetriever" in msg.send_to]
        major = msgs[-2]

        qa_rag_q, qa_rag_a = self.qastore.query(instruction, major)
        
        use_qa = False
        if qa_rag_q:
            use_qa = await Judge().run(memory_text, qa_rag_q)
        
        qa_res = "\n".join(["相似题目/例题：", qa_rag_q, "解答：", qa_rag_a]) if use_qa else ""
        logger.info(f"RAG QA: {qa_res}")
        msg = Message(content=qa_res, role=self.profile, cause_by=type(todo), 
            sent_from=self.name, send_to="Human")

        return msg


class WebRetriever(Role):
    name: str = "WebRetriever"
    profile: str = "WebRetriever"

    def __init__(self, webstore, **kwargs):
        super().__init__(**kwargs)
        self.webstore = webstore
        self.set_actions([Judge])
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

        web_rag = self.webstore.query(instruction)
        
        use_web = False
        if web_rag:
            use_web = await Judge().run(memory_text, web_rag)
        
        web_res = web_rag if use_web else ""
        logger.info(f"RAG TEXT: {web_res}")
        msg = Message(content=web_rag, role=self.profile, cause_by=type(todo), 
            sent_from=self.name, send_to="Human")

        return msg


# class WebRetriever(Role):
#     # https://docs.deepwisdom.ai/main/zh/guide/use_cases/agent/researcher.html
#     name: str = "WebRetriever"
#     profile: str = "WebRetriever"
    
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.set_actions([WebRetrieval])
#         self._watch([GetMajorAndKeypoint])

#     async def _act(self) -> Message:
#         logger.info(f"{self._setting}: ready to {self.rc.todo}")
#         todo = self.rc.todo

#         memory = self.get_memories()
#         memory_text = ''
#         for msg in  memory:
#             if 'UserRequirement' in msg.sent_from:
#                 memory_text += f'User: {msg.content}'
#         for msg in memory:
#             if msg.role =="Human":
#                 instruction = msg.content
#         msgs = [msg.content for msg in memory if "WebRetriever" in msg.send_to]
#         major = msgs[-2]
#         key_resp = msgs[-1]

#         resp = await WebRetrieval().run(instruction)
#         # TODO： 信息筛选
#         msg = Message(content=resp, role=self.profile, cause_by=type(todo), 
#             sent_from=self.name, send_to="Human")

#         return msg
