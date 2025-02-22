import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from metagpt.actions import UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.const import MESSAGE_ROUTE_TO_NONE

from .actions import GetMajorAndKeypoint, Judge


class Classifier(Role):
    name: str = "Classifier"
    profile: str = "Classifier"

    def __init__(
        self, use_text=False, use_video=False, use_qa=False, use_web=False, **kwargs
    ):
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
        for msg in memory:
            # 取"Human"最后一条输入
            if msg.role == "Human":
                data = msg.content
        # 提取前端chat的history和instruction
        history = eval(data)["history"]
        instruction = eval(data)["instruction"]
        logger.info(f"HISTORY: {history}")
        logger.info(f"INSTRUCTION: {instruction}")

        stq, major, keypoint = await GetMajorAndKeypoint().run(history, instruction)

        send_roles = []
        if self.use_text:
            send_roles.append("TextbookRetriever")
        if self.use_video:
            send_roles.append("VideoRetriever")
        if self.use_qa:
            send_roles.append("QARetriever")
        if self.use_web:
            send_roles.append("WebRetriever")
        logger.info(f"messages will be sent to {send_roles}")

        msg_stq = Message(
            content=stq,
            role=self.profile,
            cause_by=type(todo),
            sent_from=self.name,
            send_to=send_roles,
        )
        msg_major = Message(
            content=major,
            role=self.profile,
            cause_by=type(todo),
            sent_from=self.name,
            send_to=send_roles,
        )
        msg_keypoint = Message(
            content=keypoint,
            role=self.profile,
            cause_by=type(todo),
            sent_from=self.name,
            send_to=send_roles,
        )

        self.rc.env.publish_message(msg_stq)
        self.rc.env.publish_message(msg_major)
        self.rc.env.publish_message(msg_keypoint)

        return Message(content="dummy message", send_to=MESSAGE_ROUTE_TO_NONE)


class TextbookRetriever(Role):
    name: str = "TextbookRetriever"
    profile: str = "TextbookRetriever"

    def __init__(self, textstore, **kwargs):
        super().__init__(**kwargs)
        self.textstore = textstore
        self.set_actions([Judge])
        self._watch([GetMajorAndKeypoint])

    async def _act(self) -> Message:
        logger.info(f"{self._setting}: ready to {self.rc.todo}")
        todo = self.rc.todo

        memory = self.get_memories()
        for msg in memory:
            if msg.role == "Human":
                data = msg.content
        history = eval(data)["history"]
        instruction = eval(data)["instruction"]

        msgs = [
            msg.content
            for msg in memory
            if "TextbookRetriever" in msg.send_to and msg.sent_from == "Classifier"
        ]
        stq = msgs[-3]
        major = msgs[-2]
        keypoint = msgs[-1]

        text_rag_page_content, text_rag_content = self.textstore.query(keypoint, major)

        use_text = False
        if text_rag_page_content and text_rag_content:
            chat_messages = history + f"\nuser:{instruction}"
            use_text = await Judge().run(chat_messages, stq, text_rag_content)

        text_res = text_rag_content if use_text else ""
        logger.info(f"RAG TEXT: {text_res}")

        msg = Message(
            content=text_res,
            role=self.profile,
            cause_by=type(todo),
            sent_from=self.name,
            send_to="Human",
        )
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
        for msg in memory:
            if msg.role == "Human":
                data = msg.content
        history = eval(data)["history"]
        instruction = eval(data)["instruction"]

        msgs = [
            msg.content
            for msg in memory
            if "VideoRetriever" in msg.send_to and msg.sent_from == "Classifier"
        ]
        stq = msgs[-3]
        major = msgs[-2]
        keypint = msgs[-1]

        video_rag_page_content, video_rag_url, video_rag_up = self.videostore.query(
            keypint, major
        )

        use_video = False
        if video_rag_page_content:
            chat_messages = history + f"\nuser:{instruction}"
            use_video = await Judge().run(chat_messages, stq, video_rag_page_content)

        video_res = (
            f"知识点视频讲解：bilibili up主 **{video_rag_up}**  {video_rag_url}"
            if use_video
            else ""
        )
        logger.info(f"RAG VIDEO: {video_res}")
        msg = Message(
            content=video_res,
            role=self.profile,
            cause_by=type(todo),
            sent_from=self.name,
            send_to="Human",
        )
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
        for msg in memory:
            if msg.role == "Human":
                data = msg.content
        history = eval(data)["history"]
        instruction = eval(data)["instruction"]
        msgs = [
            msg.content
            for msg in memory
            if "QARetriever" in msg.send_to and msg.sent_from == "Classifier"
        ]
        stq = msgs[-3]
        major = msgs[-2]

        qa_ret = self.qastore.query(stq, major)

        use_qa = []
        for ie in qa_ret:
            chat_messages = history + f"\nuser:{instruction}"
            use_this_qa = await Judge().run(chat_messages, stq, ie[0])
            if use_this_qa:
                use_qa.append(
                    "\n".join(
                        [
                            "=====" * 10,
                            "**相似题目/例题**：",
                            ie[0],
                            "**解答**：",
                            ie[1],
                            "**题解**：",
                            ie[2],
                            "=====" * 10,
                        ]
                    )
                )

        qa_res = "\n\n".join(use_qa)
        logger.info(f"RAG QA: {qa_res}")
        msg = Message(
            content=qa_res,
            role=self.profile,
            cause_by=type(todo),
            sent_from=self.name,
            send_to="Human",
        )

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
        for msg in memory:
            if msg.role == "Human":
                data = msg.content
        history = eval(data)["history"]
        instruction = eval(data)["instruction"]
        msgs = [
            msg.content
            for msg in memory
            if "WebRetriever" in msg.send_to and msg.sent_from == "Classifier"
        ]
        stq = msgs[-3]

        web_rag = self.webstore.query(stq)

        use_web = False
        if web_rag:
            chat_messages = history + f"\nuser:{instruction}"
            use_web = await Judge().run(chat_messages, stq, web_rag)

        web_res = web_rag if use_web else ""
        logger.info(f"RAG WEB: {web_res}")
        msg = Message(
            content=web_rag,
            role=self.profile,
            cause_by=type(todo),
            sent_from=self.name,
            send_to="Human",
        )

        return msg
