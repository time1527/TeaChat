import os
import sys
import json
import jsonlines

from langchain_community.document_loaders import JSONLoader
from langchain_community.vectorstores import Chroma
# from langchain_community.retrievers import BM25Retriever
# from retriever import EnsembleRetriverReranker

from LangChain_LLM import InternLM
from langchain.prompts import PromptTemplate

from langchain.chains import RetrievalQA
# import langchain.chains.retrieval_qa.base

class TextStore:
    def __init__(self, major) -> None:
        self.major = major
        self.json_path = f'../../rag_data/text/{self.major}_directory.json'
        self.embedding_path = '/Users/wanpengxu/Github/bge-base-zh-v1.5'
        self.db_path = './text_vector_db'   # 这应该只是个 db 文件夹
        self.docs = None

        self.vectordb = None
        # 具体到某学科向量数据库是否存在
        if os.path.exists(self.db_path):
            self.vectordb = Chroma(
                persist_directory=self.db_path, 
                embedding_function=self.embedding_path
            )
        else:
            self._init_docs_and_db()
        
        # self.bm25retriever = BM25Retriever.from_documents(self.docs)
        # self.retriever = EnsembleRetriverReranker(self.docs)

        self.template = """使用以下上下文来回答用户的问题。如果你不知道答案，就说你不知道。总是使用中文回答。
        问题: {question}
        可参考的上下文：
        ···
        {context}
        ···
        如果给定的上下文无法让你做出回答，请回答你不知道。
        有用的回答:"""

        self.QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context","question"],template=self.template)

    def _metadata_func(self, record: dict, metadata: dict) -> dict:
        metadata['info'] = record.get('info')
        return metadata

    def _init_docs_and_db(self) -> None:
        loader = JSONLoader(
            file_path = self.json_path,
            jq_schema = f'.{self.major}_directory.[]',
            content_key = 'name',
            metadata_func = self._metadata_func,
        )

        self.docs = loader.load()

        self.vectordb = Chroma.from_documents(
            documents = self.docs,
            embedding = self.embedding_path,
            persist_directory = self.db_path
        )
        self.vectordb.persist()

    def query(self,question):    # retriever reranker
        # result = self.bm25retriever.get_relevant_documents(question)
        # # result = self.retriever.get_relevant_documents(question)
        # return result

        llm = InternLM(model_path = "/root/model/Shanghai_AI_Laboratory/internlm-chat-7b")
        qa_chain = RetrievalQA.from_chain_type(
            llm,
            retriever=self.vectordb.as_retriever(),
            return_source_documents=True,
            chain_type_kwargs={"prompt":self.QA_CHAIN_PROMPT}
        )

        result = qa_chain({"query": question})
        return result["result"]

if __name__ == "__main__":
    vb = TextStore("chemistry")
    print(vb.query("氧化还原反应"))
