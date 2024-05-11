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


from roles import Classifier, TextbookRetriever, VideoRetriever, QARetriever, WebRetriever
from actions import GetMajorAndKeypoint, TextbookRetrievalJudge, VideoRetrievalJudge, QARetrievalJudge, WebRetrieval

classroom = Environment()

import re

async def main(topic: str, n_round=3):
    embedding = HuggingFaceEmbeddings(
        model_name = '/root/model/bce-embedding-base_v1',
        encode_kwargs = {'normalize_embeddings': True}
    )
    reranker = HuggingFaceCrossEncoder(model_name = '/root/model/bce-reranker-base_v1')
    
    logger.info(f"00000000000000")
    textstore = TextStore(embedding, reranker)
    logger.info(f"--------------")
    videostore = VideoStore(embedding, reranker)
    logger.info(f"++++++++++++++")
    # qastore = QAStore(embedding, reranker)          # slow to load
    logger.info(f"11111111111111")
    
    classroom.add_roles([
        Classifier(use_text=True, use_video=True, use_qa=False, use_web=True),
        TextbookRetriever(textstore=textstore), 
        VideoRetriever(videostore=videostore), 
        # QARetriever(qastore=qastore), 
        WebRetriever()
    ])

    logger.info(f"222222222222222")
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

        pattern = r"(.*): (.*)\n"
        matches = re.findall(pattern, classroom.history)

        last_resp = {}
        for match in matches:
            role, resp = match
            last_resp[role] = resp
        print(last_resp)

        # # 输出每个角色说过的最后一句话
        # for role, dialogue in last_lines.items():
        #     print(f"{role}: {dialogue}")

    return classroom.history
    

asyncio.run(main(topic='什么是氧化还原反应'))