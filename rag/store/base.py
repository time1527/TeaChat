import os
import sys
import torch
import pickle
sys.path.append("../.")


# loader
from langchain_community.document_loaders import JSONLoader
# embedding/reranker
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
# vectordb
from langchain_community.vectorstores import FAISS
# retriver
from retriever.bm25filter import BM25FilterRetriever
# llm
from llm.internlm import InternLM
# qa chain
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA


MAJORMAP = {
    "数学":"数学",
    "语文":"语文",
    "英语":"英语",
    "外语":"英语",
    "生物学":"生物",
    "生物":"生物",
    "化学":"化学",
    "物理":"物理",
    "物理学":"物理",
    "历史":"历史",
    "历史学":"历史",
    "地理":"地理",
    "地理学":"地理",
    "政治":"政治",
    "思想政治":"政治"
}


class BaseStore:
    def __init__(self) -> None:
        # base 
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedding = HuggingFaceEmbeddings(
                        model_name = 'maidalun1020/bce-embedding-base_v1',
                        encode_kwargs = {'normalize_embeddings': True})
        self.reranker = HuggingFaceCrossEncoder(
                        model_name = 'maidalun1020/bce-reranker-base_v1',
                        model_kwargs = {"device":self.device})
        self.dir = None
        self.use_faiss = False
        self.use_bm25 = False
        
        # faiss/bm25retriver
        self.faiss = None
        self.bm25retriever = None
        self.faissretriever = None
        self.faiss_path = None
        self.bm25retriever_path = None
        

    def _metadata_func(self, record: dict, metadata: dict) -> dict:
        raise NotImplementedError
    

    def _init_docs(self):
        raise NotImplementedError
    

    def _init_bm25_retriever(self,documents) -> None:
        # bm25retriver
        self.bm25retriever = BM25FilterRetriever.from_documents(documents)
        pickle.dump(self.bm25retriever, open(self.bm25retriever_path, "wb"))


    def _init_faiss_retriever(self,documents):
        # faiss
        self.faiss = FAISS.from_documents(
            documents = documents,
            embedding = self.embedding)
        self.faiss.save_local(self.faiss_path)


    def _get_retriever(self):
        documents = self._init_docs()
        if self.use_bm25 and os.path.exists(self.bm25retriever_path):
            self.bm25retriever = pickle.load(open(self.bm25retriever_path, "rb"))
        elif self.use_bm25:    
            self._init_bm25_retriever(documents)
            
        if self.use_faiss and os.path.exists(self.faiss_path):
            self.faiss = FAISS.load_local(self.faiss_path,
                                        self.embedding,
                                        allow_dangerous_deserialization = True
                                        )
        elif self.use_faiss:
            self._init_faiss_retriever(documents)


    # retriever reranker
    def get(self,question,major):
        """检索-增强-生成"""
        major = MAJORMAP[major]


        docs = []
        if self.use_bm25:
            bm25docs = self.bm25retriever.invoke(question,k = 5,filter={'major':major})
            print(f"bm25 retriever return :")
            print([doc.metadata["major"] for doc in bm25docs])
            docs.extend(bm25docs)
        
        if self.use_faiss:
            self.faissretriever = self.faiss.as_retriever(search_kwargs={"k": 5,'filter': {'major':major}})
            faissdocs = self.faissretriever.invoke(question)
            print(f"faiss retriever return :")
            print([doc.metadata["major"] for doc in faissdocs])
            docs.extend(faissdocs)
        
        # 重排
        sentence_pairs = [(question,doc.page_content) for doc in docs]
        try:
            scores = self.reranker.score(sentence_pairs)
            ret = docs[scores.argmax()]
        except Exception as e:
            print("An error occurred while scoring:", e)
            ret = None
        return ret
    
    def query(self,question,major):
        raise NotImplementedError