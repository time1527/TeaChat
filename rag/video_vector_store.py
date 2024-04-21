import sys
import json
import jsonlines

from langchain_community.document_loaders import JSONLoader
from langchain.embeddings.huggingface import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain.retrievers import BM25Retriever


class VideoVectorStore:
    def __init__(self) -> None:
        self.jsonl_path = '../rag_data/video/biologic_video_urls.jsonl'
        self.embedding_path = ''
        self.faiss_path = './video_vector_db'
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

        faiss_db = FAISS.from_documents(
            documents = self.docs,
            embedding = embedding
        )
        faiss_db.save_local(self.faiss_path)

    def query(self):    # retriever reranker
        pass