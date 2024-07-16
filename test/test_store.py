import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from rag.store import TextStore,VideoStore,QAStore,WebStore


embedding = HuggingFaceEmbeddings(
     model_name = '/home/pika/Model/bce-embedding-base_v1',
     encode_kwargs = {'normalize_embeddings': True})
reranker = HuggingFaceCrossEncoder(model_name = '/home/pika/Model/bce-reranker-base_v1')


def test_textstore(query):
     print("begin to test textstore")
     store = TextStore(embedding,reranker)
     res = store.query(query)
     print(res)


def test_videostore(query):
     print("begin to test videostore")
     store = VideoStore(embedding,reranker)
     res = store.query(query)
     print(res)


def test_qastore(query):
     print("begin to test qastore")
     store = QAStore(embedding,reranker)
     res = store.query(query)
     print(res)


def test_webstore(query,api_key,**kwargs):
     print("begin to test webstore")
     store = WebStore(embedding,reranker,api_key,**kwargs)
     res = store.query("什么是氧化还原反应")
     print(res)


if __name__ == "__main__":
     query = "什么是氧化还原反应"
     test_textstore(query)
     # test_videostore(query)
     # test_qastore(query)
     test_webstore(query,"478848b1b12bedc1d6d",**{"page":2})
