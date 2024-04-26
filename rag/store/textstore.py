import os
import sys
sys.path.append("../.")


# loader
from langchain_community.document_loaders import JSONLoader
# retriver
from base import BaseStore


class TextStore(BaseStore):
    def __init__(self) -> None:
        super().__init__()
        # base 
        self.dir = "../../rag_data/text/"
        
        # faiss/bm25retriver
        self.use_bm25 = True
        self.use_faiss = True
        self.faiss_path = './text_faiss'
        self.bm25retriever_path = "./text_bm25.pkl"
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
            return ""
        else:
            return ret.metadata["content"]


if __name__ == "__main__":
    vb = TextStore()
    print(vb.query("氧化还原反应","生物"))
    print("*****"* 10)
    print(vb.query("氧化还原反应","化学"))
