import sys
import json
import jsonlines

from langchain_community.document_loaders import JSONLoader
from langchain_community.retrievers import BM25Retriever
# from retriever import EnsembleRetriverReranker

class TextStore:
    def __init__(self,major) -> None:
        self.major = major
        self.json_path = f'../../rag_data/text/{self.major}_directory.json'
        self.docs = None
        self._init_docs()
        self.bm25retriever = BM25Retriever.from_documents(self.docs)
        # self.retriever = EnsembleRetriverReranker(self.docs)

    def _metadata_func(self, record: dict, metadata: dict) -> dict:
        metadata['info'] = record.get('info')
        return metadata

    def _init_docs(self) -> None:
        loader = JSONLoader(
            file_path = self.json_path,
            jq_schema = f'.{self.major}_directory.[]',
            content_key = 'name',
            metadata_func = self._metadata_func,
        )

        self.docs = loader.load()

    def query(self,question):    # retriever reranker
        result = self.bm25retriever.get_relevant_documents(question)
        # result = self.retriever.get_relevant_documents(question)
        return result
    

if __name__ == "__main__":
    vb = TextStore("chemistry")
    print(vb.query("氧化还原反应"))
