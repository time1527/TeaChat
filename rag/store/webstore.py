import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# /root/github/TeaChat
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# loader
from langchain_community.document_loaders import JSONLoader
# retriver
from rag.retriever import WebSerperRetriever
from rag.store import BaseStore
# vectordb
from langchain_community.vectorstores import Chroma
# 
from langchain_community.utilities import GoogleSerperAPIWrapper

class WebStore(BaseStore):
    def __init__(self,embedding,reranker,serper_api_key,k = 10,**kwargs) -> None:
        super().__init__(embedding,reranker)
        # base 
        self.api_key = serper_api_key
        self.k = k
        # **kwargs:{"page":2}
        self._get_retriever(**kwargs)


    def _get_retriever(self,**kwargs):
        self.vectorstore = Chroma(embedding_function=self.embedding)
        self.search = GoogleSerperAPIWrapper(
            k=self.k,
            gl="cn",
            hl="zh-cn",
            serper_api_key=self.api_key,
            **kwargs) 
        self.retriever = WebSerperRetriever(
            vectorstore=self.vectorstore,
            search=self.search
            )

    def get(self,question):
        docs = self.retriever.get_relevant_documents(question)
        # 重排
        sentence_pairs = [(question,doc.page_content) for doc in docs]
        try:
            scores = self.reranker.score(sentence_pairs)
            ret = docs[scores.argmax()]
        except Exception as e:
            print("An error occurred while scoring:", e)
            ret = None
        return ret

    def query(self,question):
        ret = self.get(question)
        if ret == None:
            return ""
        else:
            return ret.page_content

