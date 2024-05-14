import re
import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.store import TextStore,VideoStore,QAStore,WebStore
from multi_agent import *

from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.environment import Environment
from metagpt.const import MESSAGE_ROUTE_TO_ALL, MESSAGE_ROUTE_TO_NONE

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_community.vectorstores import Chroma


env = Environment()


async def main(topic: str, api_key,use_text=True, use_video=False, use_qa=False, use_web=True,n_round=3):
    embedding = HuggingFaceEmbeddings(
        model_name = '/root/model/bce-embedding-base_v1',
        encode_kwargs = {'normalize_embeddings': True}
    )
    reranker = HuggingFaceCrossEncoder(model_name = '/root/model/bce-reranker-base_v1')

    roles = [Classifier(use_text=use_text, use_video=use_video, use_qa=use_qa, use_web=use_web)]
    if use_text:
        logger.info(f"loading textstore")
        textstore = TextStore(embedding, reranker)
        roles.append(TextbookRetriever(textstore=textstore))
    if use_video:
        logger.info(f"loading videostore")
        videostore = VideoStore(embedding, reranker)
        roles.append(VideoRetriever(videostore=videostore))
    if use_qa:
        logger.info(f"loading qastore")
        qastore = QAStore(embedding, reranker)
        roles.append(QARetriever(qastore=qastore))
    if use_web:
        logger.info(f"loading webstore")
        webstore = WebStore(embedding,reranker,api_key)
        roles.append(WebRetriever(webstore=webstore))
    
    env.add_roles(roles)

    env.publish_message(
        Message(role="Human", content=topic, cause_by=UserRequirement,
                sent_from = UserRequirement, send_to=MESSAGE_ROUTE_TO_ALL),
        peekable=False,
    )

    while n_round > 0:
        # self._save()
        n_round -= 1
        logger.debug(f"max {n_round=} left.")

        await env.run()

    pattern = r"(.*): (.*)\n"
    matches = re.findall(pattern, env.history)

    last_resp = {}
    for match in matches:
        role, resp = match
        last_resp[role] = resp
    print(last_resp)

        # # 输出每个角色说过的最后一句话
        # for role, dialogue in last_lines.items():
        #     print(f"{role}: {dialogue}")
    return env.history
    

asyncio.run(main(topic='什么是氧化还原反应',api_key="478848b1b12bedc1d6d10d4f6fd3a"))