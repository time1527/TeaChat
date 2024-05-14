import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rag.loader import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer


if __name__ == "__main__":
    urls = ['http://pt.csust.edu.cn/meol/data/convert/2022/10/14/683fc1b1-3ee0-4b44-a5e7-241be64f50cf_5763474.html',
            'http://www.gaokao.com/e/20181212/5c10c62c9b234.shtml',
            'https://www.sohu.com/a/382124693_537996',
            'https://zh.wikipedia.org/zh-cn/%E6%B0%A7%E5%8C%96%E8%BF%98%E5%8E%9F%E5%8F%8D%E5%BA%94']
    loader = AsyncHtmlLoader(urls, ignore_load_errors=True)
    html2text = Html2TextTransformer()
    docs = loader.load()
    docs = list(html2text.transform_documents(docs))
    print(docs)