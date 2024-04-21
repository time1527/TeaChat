from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain.retrievers import EnsembleRetriever
from langchain.embeddings import HuggingFaceEmbeddings
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class EnsembleRetriverReranker():
    def __init__(self,documents,embedding = None,bm25_params = None):
        self.documents = documents
        self.bm25retriever = BM25Retriever.from_documents(
            documents=self.documents,
            bm25_params=bm25_params)
        self.embedding = embedding or \
                            HuggingFaceEmbeddings(
                                model_name = 'maidalun1020/bce-embedding-base_v1',
                                encode_kwargs = {'normalize_embeddings': True})
                            
        self.faissvb = FAISS.from_documents(
            documents=self.documents,
            embedding=self.embedding)
        self.faissretriever = self.faissvb.as_retriever()
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.bm25retriever, self.faissretriever], 
            weights=[0.5, 0.5])
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.reranker = None
        

    def get_relevant_documents(self,question):
        res = self.ensemble_retriever.invoke(question)
        return res
        
    def _init_rerank(self):
    # init model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained('maidalun1020/bce-reranker-base_v1')
        self.reranker = AutoModelForSequenceClassification.from_pretrained('maidalun1020/bce-reranker-base_v1')
        self.reranker.to(self.device)

    def _rerank(self,question,documents:list,top = 5):
        # get inputs
        self._init_rerank()
        sentence_pairs = [(question,doc.page_content) for doc in documents]
        inputs = self.tokenizer(sentence_pairs, padding=True, truncation=True, max_length=512, return_tensors="pt")
        inputs_on_device = {k: v.to(self.device) for k, v in inputs.items()}

        # calculate scores
        with torch.no_grad():
            scores = self.reranker(**inputs_on_device, return_dict=True).logits.view(-1,).float()
            scores = torch.sigmoid(scores)
        top_indices = scores.cpu().numpy().argsort()[-top:][::-1]
        top_documents = [documents[i] for i in top_indices]
        return top_documents
    
    def get_relevant_documents_rerank(self,question):
        docs = self.ensemble_retriever.invoke(question)
        print(f"before rerank:{docs}")
        top_docs = self._rerank(question,docs)
        print(f"after rerank:{top_docs}")
        return top_docs

