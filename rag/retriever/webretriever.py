# copy and modify from: 
# langchain.retrievers.web_search(Version: 0.0.34)
# https://github.com/geekan/MetaGPT/blob/main/metagpt/tools/search_engine_serper.py
import logging
import re
from typing import List, Optional

from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.callbacks import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.pydantic_v1 import Field
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter, TextSplitter
from langchain_community.cross_encoders import BaseCrossEncoder
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)


class WebSerperRetriever(BaseRetriever):
    """`Google Search API` retriever."""

    # Inputs
    vectorstore: VectorStore = Field(
        ..., description="Vector store for storing web pages"
    )
    search: GoogleSerperAPIWrapper = Field(..., description="Google Serper API Wrapper")
    text_splitter: TextSplitter = Field(
        RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=50),
        description="Text splitter for splitting web pages into chunks",
    )



    def clean_search_query(self, query: str) -> str:
        # Some search tools (e.g., Google) will
        # fail to return results if query has a
        # leading digit: 1. "LangCh..."
        # Check if the first character is a digit
        if query[0].isdigit():
            # Find the position of the first quote
            first_quote_pos = query.find('"')
            if first_quote_pos != -1:
                # Extract the part of the string after the quote
                query = query[first_quote_pos + 1 :]
                # Remove the trailing quote if present
                if query.endswith('"'):
                    query = query[:-1]
        return query.strip()


    def search_tool(self, query: str) -> List[dict]:
        """Returns num_search_results pages per Google search."""
        query_clean = self.clean_search_query(query)
        res = self.search.results(query_clean)

        """Process response from SerpAPI."""
        # logger.debug(res)
        focus = ["title", "snippet", "link"]

        def get_focused(x):
            return {i: j for i, j in x.items() if i in focus}

        if "error" in res.keys():
            raise ValueError(f"Got error from SerpAPI: {res['error']}")
        if "answer_box" in res.keys() and "answer" in res["answer_box"].keys():
            toret = res["answer_box"]["answer"]
        elif "answer_box" in res.keys() and "snippet" in res["answer_box"].keys():
            toret = res["answer_box"]["snippet"]
        elif "answer_box" in res.keys() and "snippet_highlighted_words" in res["answer_box"].keys():
            toret = res["answer_box"]["snippet_highlighted_words"][0]
        elif "sports_results" in res.keys() and "game_spotlight" in res["sports_results"].keys():
            toret = res["sports_results"]["game_spotlight"]
        elif "knowledge_graph" in res.keys() and "description" in res["knowledge_graph"].keys():
            toret = res["knowledge_graph"]["description"]
        elif "snippet" in res["organic"][0].keys():
            toret = res["organic"][0]["snippet"]
        else:
            toret = "No good search result found"

        toret_l = []
        if "answer_box" in res.keys() and "snippet" in res["answer_box"].keys():
            toret_l += [get_focused(res["answer_box"])]
        if res.get("organic"):
            toret_l += [get_focused(i) for i in res.get("organic")]

        return  toret_l

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> List[Document]:
        """Search Google for documents related to the query input.

        Args:
            query: user query

        Returns:
            Relevant documents from all various urls.
        """

        # Get urls
        urls = []
        search_results = self.search_tool(query)
        # logger.info("Searching for relevant urls...")
        # logger.info(f"Search results: {search_results}")
        for res in search_results:
            if res.get("link", None):
                urls.append(res["link"])

        logger.info(f"URLs to load: {urls}")
        print(urls)
        # Load, split, and add new urls to vectorstore
        urls = [url for url in urls if "wikipedia" not in url]
        if len(urls):
            loader = AsyncHtmlLoader(urls, ignore_load_errors=True)
            html2text = Html2TextTransformer()
            logger.info("Indexing urls...")
            docs = loader.load()
            docs = list(html2text.transform_documents(docs))
            docs = self.text_splitter.split_documents(docs)
            self.vectorstore.add_documents(docs)


        # Search for relevant splits
        # TODO: make this async
        logger.info("Grabbing most relevant splits from urls...")
        docs = self.vectorstore.similarity_search(query)

        # Get unique docs
        unique_documents_dict = {
            (doc.page_content, tuple(sorted(doc.metadata.items()))): doc for doc in docs
        }
        unique_documents = list(unique_documents_dict.values())
        return unique_documents

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: AsyncCallbackManagerForRetrieverRun,
    ) -> List[Document]:
        raise NotImplementedError
