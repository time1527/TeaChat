import streamlit as st
from rag.llm import InternLM
from rag.store import TextStore,VideoStore


def main():
    st.title('TeaChat')

    rag_text = st.sidebar.toggle('Activate Textbook RAG')
    rag_video = st.sidebar.toggle('Activate Video RAG')

    textstore = TextStore()
    videostore = VideoStore()
    st.session_state = dict()
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    slot1 = st.container(height=700, border=False)
    with st.container(height=200):
        text_tab, img_tab = st.tabs(["发送消息","发送图片"])


if __name__ == "__main__":
    main()
