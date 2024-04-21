import os
import sys
sys.path.append("../.")
from langchain_community.document_loaders import JSONLoader
from langchain_community.vectorstores import Chroma
# from langchain_community.retrievers import BM25Retriever
# from retriever import EnsembleRetriverReranker

from LangChain_LLM import InternLM
from langchain.prompts import PromptTemplate

from langchain.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
# import langchain.chains.retrieval_qa.base

class TextStore:
    def __init__(self, major) -> None:
        self.major = major
        self.json_path = f'../../rag_data/text/{self.major}_directory.json'
        # self.embedding_path = '/Users/wanpengxu/Github/bge-base-zh-v1.5'
        self.embedding = HuggingFaceEmbeddings(
                                model_name = 'maidalun1020/bce-embedding-base_v1',
                                encode_kwargs = {'normalize_embeddings': True})
        self.db_path = f'./{self.major}_text_db'
        self.docs = None

        self.vectordb = None
        if os.path.exists(self.db_path):
            self.vectordb = Chroma(
                persist_directory=self.db_path, 
                embedding_function=self.embedding
            )
        else:
            self._init_docs_and_db()
        
        # self.bm25retriever = BM25Retriever.from_documents(self.docs)
        # self.retriever = EnsembleRetriverReranker(self.docs)

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

        pdf_path = f'../../rag_data/textbook/{ob["book"]}'

        # 如果 json 里有就不需要在这里 extract
        content = ''

        with open(pdf_path, 'rb') as input_file:
            pdf_reader = PyPDF2.PdfReader(input_file)

            for page_number in range(ob["st"], ob["ed"]+1):
                page = pdf_reader.pages[page_number]
                page_content = page.extract_text()

                content += page_content
        
        metadata['content'] = content

        return metadata

    def _init_docs_and_db(self) -> None:
        loader = JSONLoader(
            file_path = self.json_path,
            jq_schema = f'.{self.major}_directory.[]',
            content_key = 'name',
            metadata_func = self._metadata_func,
        )

        self.docs = loader.load()

        self.vectordb = Chroma.from_documents(
            documents = self.docs,
            embedding = self.embedding,
            persist_directory = self.db_path
        )
        self.vectordb.persist()

    # retriever reranker
    def query(self,question):
        # result = self.bm25retriever.get_relevant_documents(question)
        # # result = self.retriever.get_relevant_documents(question)
        # return result

        ## 检索-提取-问答
        ## 检索
        retriever=self.vectordb.as_retriever(search_kwargs={"k": 1})

        retrieval_info = retriever.get_relevant_documents(question)[0].metadata

        ## 从 metadata 中提取 st 和 ed，PyPDF2 抽取文字
        pdf_name = retrieval_info['book']
        st = retrieval_info['st']
        ed = retrieval_info['ed']
        context = retrieval_info['content']
        
        prompt = f"""使用以下参考资料来回答用户的问题。在回答的最后给出使用了的参考资料，例如：“参考book的st页到ed页”。总是使用中文回答。
        问题: {question}
        参考资料: 
        ···
        {context}
        ···
        如果给定的上下文无法让你做出回答，请回答你不知道。
        有用的回答:"""

        ## 放到 Prompt 里进行 QA
        llm = InternLM(model_path="/root/share/new_models/Shanghai_AI_Laboratory/internlm2-chat-1_8b")
        return llm(prompt)

        ## 检索-问答
        # llm = InternLM(model_path = "/root/model/Shanghai_AI_Laboratory/internlm-chat-7b")
        # llm = InternLM(model_path="/root/share/new_models/Shanghai_AI_Laboratory/internlm2-chat-1_8b")
        # qa_chain = RetrievalQA.from_chain_type(
        #     llm,
        #     retriever=self.vectordb.as_retriever(),
        #     return_source_documents=True,
        #     chain_type_kwargs={"prompt":self.QA_CHAIN_PROMPT}
        # )

        # result = qa_chain({"query": question})
        # # res = result["result"]
        # print(f"===================={result}===========")
        # return result["result"]

if __name__ == "__main__":
    vb = TextStore("chemistry")
    print(vb.query("氧化还原反应"))
