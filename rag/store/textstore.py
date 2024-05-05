import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# /root/github/TeaChat
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# loader
from langchain_community.document_loaders import JSONLoader
# retriver
from rag.store import BaseStore


class TextStore(BaseStore):
    def __init__(self,embedding,reranker) -> None:
        super().__init__(embedding,reranker)
        # base 
        self.dir = os.path.join(root_path, "rag_data", "text")

        # embedding/reranker
        self.embedding = embedding
        self.reranker = reranker
        
        # faiss/bm25retriver
        self.use_bm25 = True
        self.use_faiss = True
        self.faiss_path = os.path.join(root_path, "rag", "store", "text_faiss")
        self.bm25retriever_path = os.path.join(root_path, "rag", "store", "text_bm25.pkl")
        self._get_retriever()

    def _metadata_func(self, record: dict, metadata: dict) -> dict:
        ob = record.get('info')
        metadata['st'] = ob["st"]
        metadata['ed'] = ob["ed"]
        metadata['book'] = ob["book"]
        metadata['content'] = ob["content"]
        metadata['major'] = ob["major"]
        return metadata
    
    def _init_docs(self) -> None:
        # json -> Document
        files = sorted(os.listdir(self.dir))
        json_files = list(filter(lambda file: '.json' in file, files))
        documents = []
        # biology_directory
        for file in json_files:
            major = file.split("_")[0]
            json_path = os.path.join(self.dir,file)
            # print(json_path)
            loader = JSONLoader(
                file_path = json_path,
                jq_schema = f'.{major}_directory.[]',
                content_key = 'name',
                metadata_func = self._metadata_func,
            )
            documents.extend(loader.load())
        return documents

    # retriever reranker
    def query(self,question,major):
        ret = self.get(question,major)
        if ret == None:
            return "",""
        else:
            return ret.page_content,ret.metadata["content"]

