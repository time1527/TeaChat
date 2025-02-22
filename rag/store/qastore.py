import os
import sys
from langchain_community.document_loaders import JSONLoader  # loader

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

from rag.store import BaseStore  # retriver


class QAStore(BaseStore):
    def __init__(self, embedding, reranker) -> None:
        super().__init__(embedding, reranker)
        # base
        self.dir = os.path.join(root_path, "rag_data", "qa")

        # embedding/reranker
        self.embedding = embedding
        self.reranker = reranker

        # faiss
        self.use_faiss = True
        self.faiss_path = os.path.join(root_path, "rag", "store", "qa_faiss")
        self._get_retriever()

    def _metadata_func(self, record: dict, metadata: dict) -> dict:
        metadata["q_type"] = record["q_type"]
        metadata["keypoint"] = record["keypoint"]
        metadata["answer_detail"] = record["answer_detail"]
        metadata["answer"] = record["answer"]
        metadata["major"] = record["major"]
        return metadata

    def _init_docs(self) -> None:
        # json -> Document
        files = sorted(os.listdir(self.dir))
        json_files = list(filter(lambda file: ".json" in file, files))
        documents = []
        for file in json_files:
            json_path = os.path.join(self.dir, file)
            loader = JSONLoader(
                file_path=json_path,
                jq_schema=f".",
                content_key="text",
                metadata_func=self._metadata_func,
                json_lines=True,
            )
            documents.extend(loader.load())
        return documents

    # retriever reranker
    def query(self, question, major=""):
        ret = self.get(question, major)
        if ret is None:
            return []
        else:
            return [
                [
                    r.page_content,
                    r.metadata["answer"],
                    r.metadata["answer_detail"],
                ]
                for r in ret
            ]

    def rerank(self, question, docs):
        """重排"""
        sentence_pairs = [(question, doc.page_content) for doc in docs]
        try:
            scores = self.reranker.score(sentence_pairs)
            sorted_indices = scores.argsort()[::-1]
            top_3_indices = sorted_indices[:3]
            top_3_docs = [docs[i] for i in top_3_indices]
            return top_3_docs
        except:
            return None
