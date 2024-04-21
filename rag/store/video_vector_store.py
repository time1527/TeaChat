import os
import sys
import json

from langchain_community.document_loaders import JSONLoader
# from langchain.embeddings.huggingface import HuggingFaceBgeEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain_community.retrievers.bm25 import BM25Retriever


class VideoVectorStore:
    def __init__(self, major:str) -> None:
        self.major = major
        self.json_path = f'../../rag_data/video/{self.major}_video_urls.json'
        # self.embedding_path = '/Users/wanpengxu/Github/bge-base-zh-v1.5'
        self.embedding = HuggingFaceEmbeddings(
                                model_name = 'maidalun1020/bce-embedding-base_v1',
                                encode_kwargs = {'normalize_embeddings': True})
        self.db_path = f'./{self.major}_video_db'
        self.docs = None

        self.vectordb = None
        if os.path.exists(self.db_path):
            self.vectordb = Chroma(
                persist_directory=self.db_path, 
                embedding_function=self.embedding
            )
        else:
            self._init_docs_and_db()

    def _metadata_func(self, record: dict, metadata: dict) -> dict:
        metadata['url'] = record.get('url')
        return metadata

    def _init_docs_and_db(self) -> None:
        loader = JSONLoader(
            file_path = self.json_path,
            jq_schema = f'.{self.major}_video_urls.[]',
            content_key = 'name',
            metadata_func = self._metadata_func,
        )

        self.docs = loader.load()

        self.vectordb = Chroma.from_documents(
            documents = self.docs,
            embedding = self.embedding,
            persist_directory = self.db_path
        )
        self.vectordb.persist()

    def query(self,question):
        ## 检索
        # 有些资料有两份
        retriever=self.vectordb.as_retriever(search_kwargs={"k": 1})

        retrieval_info = retriever.get_relevant_documents(question)[0].metadata

        url = retrieval_info['url']
        name = retrieval_info['name']
        
        prompt = f"""使用以下参考资料来回答用户的问题。在回答的最后告诉用户可以具体可以参见哪些参考资料，如“具体可见教学视频：name，其链接为：url”。总是使用中文回答。
        问题: {question}
        参考资料: 
        ···
        教学视频：{name}
        连接：{url}
        ···
        如果给定的上下文无法让你做出回答，请回答你不知道。
        有用的回答:"""

        ## 放到 Prompt 里进行 QA
        llm = InternLM(model_path="/root/share/new_models/Shanghai_AI_Laboratory/internlm2-chat-1_8b")
        return llm(prompt)

if __name__ == "__main__":
    vb = VideoVectorStore("chemistry")
    print(vb.query("氧化还原反应"))
