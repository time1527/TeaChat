# modifified from langchain_community.retrievers.BM25Retriever
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional,Union

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.pydantic_v1 import Field
from langchain_core.retrievers import BaseRetriever
import jieba

def default_preprocessing_func(text: str) -> List[str]:
    return jieba.lcut(text)


class BM25FilterRetriever(BaseRetriever):
    """
    `BM25` retriever without Elasticsearch.
    can filter Documents by metadata
    """

    vectorizer: Any
    """ BM25 vectorizer."""
    docs: List[Document] = Field(repr=False)
    """ List of documents."""
    k: int = 4
    """ Number of documents to return."""
    filter_k :int = 20
    preprocess_func: Callable[[str], List[str]] = default_preprocessing_func
    """ Preprocessing function to use on the text before BM25 vectorization."""
    _expects_other_args:bool=True
    
    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    @classmethod
    def from_texts(
        cls,
        texts: Iterable[str],
        metadatas: Optional[Iterable[dict]] = None,
        bm25_params: Optional[Dict[str, Any]] = None,
        preprocess_func: Callable[[str], List[str]] = default_preprocessing_func,
        **kwargs: Any,
    ) -> BM25FilterRetriever:
        """
        Create a BM25Retriever from a list of texts.
        Args:
            texts: A list of texts to vectorize.
            metadatas: A list of metadata dicts to associate with each text.
            bm25_params: Parameters to pass to the BM25 vectorizer.
            preprocess_func: A function to preprocess each text before vectorization.
            **kwargs: Any other arguments to pass to the retriever.

        Returns:
            A BM25Retriever instance.
        """
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError(
                "Could not import rank_bm25, please install with `pip install "
                "rank_bm25`."
            )

        texts_processed = [preprocess_func(t) for t in texts]
        bm25_params = bm25_params or {}
        vectorizer = BM25Okapi(texts_processed, **bm25_params)
        metadatas = metadatas or ({} for _ in texts)
        docs = [Document(page_content=t, metadata=m) for t, m in zip(texts, metadatas)]
        return cls(
            vectorizer=vectorizer, docs=docs, preprocess_func=preprocess_func, **kwargs
        )

    @classmethod
    def from_documents(
        cls,
        documents: Iterable[Document],
        *,
        bm25_params: Optional[Dict[str, Any]] = None,
        preprocess_func: Callable[[str], List[str]] = default_preprocessing_func,
        **kwargs: Any,
    ) -> BM25FilterRetriever:
        """
        Create a BM25Retriever from a list of Documents.
        Args:
            documents: A list of Documents to vectorize.
            bm25_params: Parameters to pass to the BM25 vectorizer.
            preprocess_func: A function to preprocess each text before vectorization.
            **kwargs: Any other arguments to pass to the retriever.

        Returns:
            A BM25Retriever instance.
        """
        texts, metadatas = zip(*((d.page_content, d.metadata) for d in documents))
        return cls.from_texts(
            texts=texts,
            bm25_params=bm25_params,
            metadatas=metadatas,
            preprocess_func=preprocess_func,
            **kwargs,
        )

    @staticmethod
    def _create_filter_func(
        filter: Optional[Union[Callable, Dict[str, Any]]],
    ) -> Callable[[Dict[str, Any]], bool]:
        """
        Create a filter function based on the provided filter.

        Args:
            filter: A callable or a dictionary representing the filter
            conditions for documents.

        Returns:
            Callable[[Dict[str, Any]], bool]: A function that takes Document's metadata
            and returns True if it satisfies the filter conditions, otherwise False.
        """
        if callable(filter):
            return filter

        if not isinstance(filter, dict):
            raise ValueError(
                f"filter must be a dict of metadata or a callable, not {type(filter)}"
            )

        def filter_func(metadata: Dict[str, Any]) -> bool:
            return all(
                metadata.get(key) in value
                if isinstance(value, list)
                else metadata.get(key) == value
                for key, value in filter.items()  # type: ignore
            )

        return filter_func
    

    def get_relevant_documents(
        self, 
        query: str, 
        k:int = 4,
        filter: Optional[Union[Callable, Dict[str, Any]]] = None,
        fetch_k:int = 20,
        *, 
        run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        processed_query = self.preprocess_func(query)
        return_docs = self.vectorizer.get_top_n(processed_query, self.docs,  k if filter is None else fetch_k)

        docs = []

        if filter is not None:
            filter_func = self._create_filter_func(filter)
        for doc in return_docs:
            if filter is not None:
                if filter_func(doc.metadata):
                    docs.append(doc)
            else:
                docs.append(doc)
        return docs[:k]
