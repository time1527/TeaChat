from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain.retrievers import EnsembleRetriever
from langchain.embeddings import HuggingFaceEmbeddings


class EnsembleRetriverReranker():
    def __init__(self,documents,embedding = None,bm25_params = None):
        self.documents = documents
        self.bm25retriever = BM25Retriever.from_documents(
            documents=self.documents,
            bm25_params=bm25_params)
        self.embedding = embedding or \
                            HuggingFaceEmbeddings(
                                model_name = 'maidalun1020/bce-embedding-base_v1',
                                encode_kwargs = {'normalize_embeddings': True})
                            
        self.faissvb = FAISS.from_documents(
            documents=self.documents,
            embedding=self.embedding)
        self.faissretriever = self.faissvb.as_retriever()
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.bm25retriever, self.faissretriever], 
            weights=[0.5, 0.5])
        

    def get_relevant_documents(self,question):
        res = self.ensemble_retriever.invoke(question)
        return res
        
