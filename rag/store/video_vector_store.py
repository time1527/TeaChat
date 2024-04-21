import sys
import json
import jsonlines

from langchain_community.document_loaders import JSONLoader
from langchain.embeddings.huggingface import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain_community.retrievers.bm25 import BM25Retriever


class VideoVectorStore:
    def __init__(self) -> None:
        self.jsonl_path = '../rag_data/video/biologic_video_urls.jsonl'
        self.embedding_path = '/Users/wanpengxu/Github/bge-base-zh-v1.5'
        self.db_path = './video_vector_db'
        self.bm25retriever = BM25Retriever.from_documents(self.docs)
        self.docs = None

    def _metadata_func(self, record: dict, metadata: dict) -> dict:
        metadata['url'] = record.get('url')
        return metadata

    def add(self) -> None:
        loader = JSONLoader(
            file_path = self.jsonl_path,
            jq_schema = '.',
            content_key = 'name',
            metadata_func = self._metadata_func,
            text_content=False,
            json_lines=True
        )

        self.docs = loader.load()

        embedding = HuggingFaceBgeEmbeddings(
            model_name = self.embedding_path,
            encode_kwargs = {'normalize_embeddings': True},
            query_instruction=""
        )

        vectordb = FAISS.from_documents(
            documents = self.docs,
            embedding = embedding,
            # persist_directory = self.db_path
        )
        vectordb.save_local(self.db_path)

        # vectordb.persist()

    def query(self, question):    # retriever reranker
        result = self.bm25retriever.get_relevant_documents(question)
        # result = self.retriever.get_relevant_documents(question)
        return result