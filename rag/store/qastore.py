import os
import sys
sys.path.append("../.")


# loader
from langchain_community.document_loaders import JSONLoader
# retriver
from base import BaseStore


class QAStore(BaseStore):
    def __init__(self) -> None:
        super().__init__()
        # base 
        self.dir = "../../rag_data/qa/"
        
        # faiss
        self.use_faiss = True
        self.faiss_path = './qa_faiss'
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
            return ""
        else:
            return ret


if __name__ == "__main__":
    vb = QAStore()
    print(vb.query("氧化还原反应","生物"))
    print("*****"* 10)
    print(vb.query("氧化还原反应","化学"))
