import os
import sys
from langchain_community.document_loaders import JSONLoader  # loader

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

from rag.store import BaseStore  # retriver


class VideoStore(BaseStore):
    def __init__(self, embedding, reranker) -> None:
        super().__init__(embedding, reranker)
        # base
        self.dir = os.path.join(root_path, "rag_data", "video")

        # embedding/reranker
        self.embedding = embedding
        self.reranker = reranker

        # faiss/bm25retriver
        self.use_bm25 = True
        self.use_faiss = True
        self.faiss_path = os.path.join(root_path, "rag", "store", "video_faiss")
        self.bm25retriever_path = os.path.join(
            root_path, "rag", "store", "video_bm25.pkl"
        )
        self._get_retriever()

    def _metadata_func(self, record: dict, metadata: dict) -> dict:
        metadata["url"] = record["url"]
        metadata["author"] = record["author"]
        metadata["uid"] = record["uid"]
        metadata["major"] = record["major"]
        return metadata

    def _init_docs(self) -> None:
        # json -> Document
        files = sorted(os.listdir(self.dir))
        json_files = list(filter(lambda file: ".json" in file, files))
        documents = []
        for file in json_files:
            major = file.split("_")[0]
            json_path = os.path.join(self.dir, file)
            loader = JSONLoader(
                file_path=json_path,
                jq_schema=f".{major}_video_urls.[]",
                content_key="name",
                metadata_func=self._metadata_func,
            )
            docs = loader.load()
            documents.extend(docs)
        return documents

    # retriever reranker
    def query(self, question, major=""):
        ret = self.get(question, major)
        if ret == None:
            return "", "", ""
        else:
            return ret.page_content, ret.metadata["url"], ret.metadata["author"]
