import re
import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.store import TextStore,VideoStore,QAStore,WebStore
from multi_agent import *

from metagpt.actions import UserRequirement
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.const import MESSAGE_ROUTE_TO_ALL

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder


env = RecordEnvironment()


async def main(history:list,instruction:str, api_key=None,use_text=False, use_video=False, use_qa=False, use_web=False,n_round=3):
    embedding = HuggingFaceEmbeddings(
        model_name = '/home/pika/Model/bce-embedding-base_v1',
        encode_kwargs = {'normalize_embeddings': True}
    )
    reranker = HuggingFaceCrossEncoder(model_name = '/home/pika/Model/bce-reranker-base_v1')

    if use_web == True:assert api_key != None

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
        Message(role="Human", 
                    content=str({"history":"\n".join(f"{entry['role']}:{entry['content']}" for entry in history),"instruction":instruction}),
                    cause_by=UserRequirement,
                    sent_from = UserRequirement, 
                    send_to=MESSAGE_ROUTE_TO_ALL),
        peekable=False,
    )

    while n_round > 0:
        # self._save()
        n_round -= 1
        logger.debug(f"max {n_round=} left.")

        await env.run()
    for k,v in env.record.items():
        print(f"{k}:{v}")
    # print(env.record)
    return env.record
    

asyncio.run(main(history=[{"role":"user","content":"hello"},{"role":"assistant","content":"你好"}],
                 instruction='什么是氧化还原反应',
                #  api_key="478848b1b12bedc1d6d",
                 use_text=True, 
                 use_video=True,
                 use_qa=True,
                #  use_web=True
                 ))