from rag.store import TextStore
from rag.llm import InternLM


if __name__ == '__main__':
    query = ''  # 前端获取得到
    major = ''  # Agent 分析得到

    text_store = TextStore()
    llm = InternLM()

    context = text_store.query(query, major)

    prompt = f'''
    xxxx{query}xxxx
    xxxx{major}xxxx
    xxxx{context}xxxx
    '''

    answer = llm(prompt)
