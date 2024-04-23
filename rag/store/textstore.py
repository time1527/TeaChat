import os
import sys
import torch
import pickle
sys.path.append("../.")


# loader
from langchain_community.document_loaders import JSONLoader
# embedding/reranker
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
# vectordb
from langchain_community.vectorstores import Chroma,FAISS
# retriver
from retriever.bm25filter import BM25FilterRetriever
# llm
from llm.internlm import InternLM
# qa chain
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA


class TextStore:
    def __init__(self) -> None:
        # base 
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedding = HuggingFaceEmbeddings(
                        model_name = 'maidalun1020/bce-embedding-base_v1',
                        encode_kwargs = {'normalize_embeddings': True})
        self.reranker = HuggingFaceCrossEncoder(
                        model_name = 'maidalun1020/bce-reranker-base_v1',
                        model_kwargs = {"device":self.device})
        self.model_path = "/home/pika/Model/Shanghai_AI_Laboratory/internlm2-chat-1_8b"
        self.json_path = "../../rag_data/text/all.json"
        
        # faiss/bm25retriver
        self.faiss = None
        self.bm25retriever = None
        self.faissretriever = None
        self.faiss_path = './text_faiss'
        self.bm25retriever_path = "./text_bm25.pkl"

        # have dumped db and documents
        if os.path.exists(self.faiss_path):
            self.bm25retriever = pickle.load(open(self.bm25retriever_path, "rb"))
            self.faiss = FAISS.load_local(self.faiss_path,
                                          self.embedding,
                                          allow_dangerous_deserialization = True
                                          )
        else:
            self._init_docs_and_db()

        # # use langchain QA chain
        # self.template = """使用以下参考资料来回答用户的问题。在回答的最后给出使用了的参考资料，例如：“参考book的st页到ed页”。总是使用中文回答。
        # 问题: {question}
        # 参考资料: 
        # ···
        # {context}
        # ···
        # 如果给定的上下文无法让你做出回答，请回答你不知道。
        # 有用的回答:"""
        # self.QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context","question"],template=self.template)

    def _metadata_func(self, record: dict, metadata: dict) -> dict:
        ob = record.get('info')
        metadata['st'] = ob["st"]
        metadata['ed'] = ob["ed"]
        metadata['book'] = ob["book"]
        metadata['content'] = ob["content"]
        metadata['major'] = ob["major"]
        return metadata
    
    def _init_docs_and_db(self) -> None:
        # json -> Document
        loader = JSONLoader(
            file_path = self.json_path,
            jq_schema = f'.directory.[]',
            content_key = 'name',
            metadata_func = self._metadata_func,
        )
        documents = loader.load()

        # bm25retriver
        self.bm25retriever = BM25FilterRetriever.from_documents(documents)
        pickle.dump(self.bm25retriever, open(self.bm25retriever_path, "wb"))

        # faiss
        self.faiss = FAISS.from_documents(
            documents = documents,
            embedding = self.embedding)
        self.faiss.save_local(self.faiss_path)


    # retriever reranker
    def query(self,question,major):
        """检索-增强-生成"""
        
        self.bm25retriever.k = 5
        self.faissretriever = self.faiss.as_retriever(search_kwargs={"k": 5,'filter': {'major':major}})
       
        # 检索
        docs = self.bm25retriever.invoke(question,filter={'major':major})
        for doc in docs:
            print("==="*10)
            print(doc.metadata["major"])

        faissdocs = self.faissretriever.invoke(question)
        for doc in faissdocs:
            print("==="*10)
            print(doc.metadata["major"])

        docs.extend(faissdocs)
        
        
        # 重排
        sentence_pairs = [(question,doc.page_content) for doc in docs]
        try:
            scores = self.reranker.score(sentence_pairs)
            ret = docs[scores.argmax()]
            context = ret.metadata['content']
        except Exception as e:
            print("An error occurred while scoring:", e)
            context = ""

        # prompt = f"""使用以下参考资料来回答用户的问题。在回答的最后给出使用了的参考资料，例如：“参考book的st页到ed页”。总是使用中文回答。
        # 问题: {question}
        # 参考资料: 
        # ···
        # {context}
        # ···
        # 如果给定的上下文无法让你做出回答，请回答你不知道。
        # 有用的回答:"""
        print("==="*10)
        print(context)
        print("==="*10)

        prompt = f"""使用以下参考资料来回答用户的问题。总是使用中文回答。回答在100字以内。
        问题: {question}
        参考资料: 
        {context}
        如果给定的上下文无法让你做出回答，请回答你不知道。
        有用的回答:"""

        # 加载llm
        llm = InternLM(model_path=self.model_path)
        return llm(prompt)

        ## langchain QAChain检索-问答
        # llm = InternLM(model_path="/root/share/new_models/Shanghai_AI_Laboratory/internlm2-chat-1_8b")
        # qa_chain = RetrievalQA.from_chain_type(
        #     llm,
        #     retriever=self.vectordb.as_retriever(),
        #     return_source_documents=True,
        #     chain_type_kwargs={"prompt":self.QA_CHAIN_PROMPT}
        # )
        # result = qa_chain({"query": question})
        # return result["result"]

if __name__ == "__main__":
    vb = TextStore()
    print(vb.query("氧化还原反应","生物"))
    print("*****"* 10)
    print(vb.query("氧化还原反应","化学"))
