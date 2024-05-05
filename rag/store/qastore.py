import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# /root/github/TeaChat
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# loader
from langchain_community.document_loaders import JSONLoader
# retriver
from rag.store import BaseStore


class QAStore(BaseStore):
    def __init__(self,embedding,reranker) -> None:
        super().__init__(embedding,reranker)
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
        metadata['q_type'] = record['q_type']
        metadata['keypoint'] = record['keypoint']
        metadata['answer_detail'] = record['answer_detail']
        metadata["answer"] = record["answer"]
        metadata['major'] = record["major"]
        return metadata
    
    def _init_docs(self) -> None:
        # json -> Document
        files = sorted(os.listdir(self.dir))
        json_files = list(filter(lambda file: '.json' in file, files))
        documents = []
        for file in json_files:
            json_path = os.path.join(self.dir,file)
            loader = JSONLoader(
                file_path = json_path,
                jq_schema = f'.',
                content_key = 'text',
                metadata_func = self._metadata_func,
                json_lines=True
            )
            documents.extend(loader.load())
        return documents

    # retriever reranker
    def query(self,question,major):
        ret = self.get(question,major)
        if ret == None:
            return "",""
        else:
            return ret.page_content,ret.metadata['answer_detail']
