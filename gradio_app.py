# Copyright 2024 time1527
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# copy and modify from 
# https://github.com/InternLM/lmdeploy/blob/v0.3.0/lmdeploy/serve/gradio/app.py
# https://github.com/InternLM/lmdeploy/blob/v0.3.0/lmdeploy/serve/gradio/api_server_backend.py
# Copyright (c) OpenMMLab. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from threading import Lock
import gradio as gr
from typing import Sequence
import tempfile
# lmdeploy
from lmdeploy.serve.gradio.constants import CSS, THEME, disable_btn, enable_btn
from lmdeploy.serve.openai.api_client import get_model_list
# local
from rag.store import TextStore,VideoStore,QAStore,WebStore
from utils.chat import get_completion,get_streaming_response,get_output
from ocr.paddleocr import ocr
# langchain
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
# from langchain.memory import ConversationBufferMemory

embedding = HuggingFaceEmbeddings(
    model_name = '/home/pika/Model/bce-embedding-base_v1',
    encode_kwargs = {'normalize_embeddings': True}
)
reranker = HuggingFaceCrossEncoder(model_name = '/home/pika/Model/bce-reranker-base_v1')


textstore = TextStore(embedding, reranker)
videostore = VideoStore(embedding, reranker)
# qastore = QAStore(embedding, reranker)          # slow to load
# webstore = WebStore(embedding,reranker,api_key)
history = []


class InterFace:
    api_server_url: str = None
    global_session_id: int = 0
    lock = Lock()


CONDENSE_QUESTION_PROMPT_TEMPLATE: str = """给出以下聊天记录和后续问题，用中文将后续问题改写为一个独立的问题。
    聊天记录:{history}，
    后续问题:{instruction}，
    独立的问题:
    """
MAJOR_PROMPT_TEMPLATE: str = """请判断以下文本属于哪一学科，只能输出两个字的回答。
    文本：{standalone_question}，
    选项：{major_list}，
    答案：
    """
KEYPOINT_PROMPT_TEMPLATE: str = """请判断以下文本考察什么知识点。请只输出知识点，不需要输出分析步骤。字数在20字以内。字数在20字以内。字数在20字以内。
    文本：{standalone_question}，
    知识点：
    """

MSG_PROMPT_TEMPLATE: str = """请判断以下文本是否与聊天记录高度相关。只允许输出一个字“是”或者“否”。
        聊天记录:{messages}，
        文本:{text}，
        是否高度相关:
        """

STQ_PROMPT_TEMPLATE: str = """请判断以下文本是否与问题高度相关。只允许输出一个字“是”或者“否”。
        问题:{stq}，
        文本:{text}，
        是否高度相关:
        """


def get_info(instruction,model_name,session_id):
    standalone_question = get_output(
            model_name,
            [{"role":"user",
              "content":CONDENSE_QUESTION_PROMPT_TEMPLATE.format(
                  history = history,
                  instruction = instruction)}],
            f'{InterFace.api_server_url}/v1/chat/completions',
            session_id=session_id)
    print(f"standalone_question = {standalone_question}")

    major_list = ["语文","数学","英语","地理","历史","政治","物理","化学","生物"]
    major_resp = get_output(
            model_name,
            [{"role":"user",
              "content":MAJOR_PROMPT_TEMPLATE.format(
                  standalone_question=standalone_question,
                  major_list=major_list)}],
            f'{InterFace.api_server_url}/v1/chat/completions',
            session_id=session_id)
    found_majors = [major for major in major_list if major in major_resp]
    if len(found_majors) == 1:major = found_majors[0]
    else: major = ""
    print(f"major = {major}")


    key_resp = get_output(
            model_name,
            [{"role":"user","content":KEYPOINT_PROMPT_TEMPLATE.format(
                standalone_question=standalone_question)}],
            f'{InterFace.api_server_url}/v1/chat/completions',
            session_id=session_id,)
    print(f"keypoint = {key_resp}")
    return standalone_question,major,key_resp


def judge(messages,stq,text,model_name,session_id):
    use_resp1 = get_output(
        model_name,
        [{"role":"user","content":MSG_PROMPT_TEMPLATE.format(
        messages = messages,text = text)}],
        f'{InterFace.api_server_url}/v1/chat/completions',
        session_id=session_id)
    use_resp2 = get_output(
        model_name,
        [{"role":"user","content":STQ_PROMPT_TEMPLATE.format(
        stq = stq,text = text)}],
        f'{InterFace.api_server_url}/v1/chat/completions',
        session_id=session_id)
    if "是" in use_resp1 or "是" in use_resp2:return True
    else:return False


def chat_stream_restful(instruction: str, 
                        state_chatbot: Sequence,
                        cancel_btn: gr.Button, 
                        reset_btn: gr.Button,
                        session_id: int,
                        rag:list,
                        top_p: float, 
                        temperature: float,
                        request_output_len: int,
                        repetition_penalty:float,
                        serper_api_key:str):
    """Chat with AI assistant.

    Args:
        instruction (str): user's prompt
        state_chatbot (Sequence): the chatting history
        session_id (int): the session id
    """
    state_chatbot = state_chatbot + [(instruction, None)]

    yield (state_chatbot, state_chatbot, disable_btn, enable_btn)

    model_names = get_model_list(f'{InterFace.api_server_url}/v1/models')
    model_name = ''
    if isinstance(model_names, list) and len(model_names) > 0:
        model_name = model_names[0]
    else:
        raise ValueError('gradio can find a suitable model from restful-api')
    ########################### 检索 ################################
    text_res = ""
    video_res = ""
    qa_res = ""
    web_res = ""
    if len(rag):
        # get model name (used in get_completion)
        stq,major,keypoint = get_info(instruction,model_name,session_id)

        messages = history + [{"role":"user","content":instruction}]
        # retrieval
        if "Textbook" in rag:
            text_rag_pc,text_rag_content = textstore.query(keypoint,major)
            if text_rag_pc and text_rag_content:
                if judge(messages,stq,text_rag_content,model_name,session_id):
                    text_res = text_rag_content
                    print("===== RAG TEXT =====")
                    print(text_res)

        if "Video" in rag:
            video_rag_pc,video_rag_url,video_rag_up = videostore.query(keypoint,major)
            if video_rag_pc:
                if judge(messages,stq,video_rag_pc,model_name,session_id):
                    video_res = f"可参考bilibili up主 {video_rag_up} 的视频：{video_rag_url}"
                    print("===== RAG VIDEO =====")
                    print(video_res)

        # if "QA" in rag:
        #     qa_rag_q,qa_rag_a = qastore.query(instruction,major)
        #     if qa_rag_q:
        #         if judge(messages,stq,qa_rag_q,model_name,session_id):
        #             qa_res = "\n".join(["相似题目/例题：",qa_rag_q,"解答：",qa_rag_a])
        #             print("===== RAG QA =====")
        #             print(qa_res)

        if "Internet" in rag:
            assert serper_api_key != None
            webstore = WebStore(embedding,reranker,serper_api_key)
            web_rag = webstore.query(stq)
            if web_rag:
                if judge(messages,stq,web_rag,model_name,session_id):
                    web_res = web_rag
                    print("===== RAG WEB =====")
                    print(web_res)

    ########################### RAG ################################
    llm_output = ""
    if text_res and web_res:
        new_instruction = f"""使用以下两段上下文来回答最后的问题，尽可能贴近上下文且详细。如果不知道答案，就说不知道，不要试图编造答案。
        上下文1：{text_res}，
        上下文2：{web_res}，
        问题：{instruction}，
        你的回答：
        """
    elif text_res:
        new_instruction = f"""使用以下上下文来回答最后的问题，尽可能贴近上下文且详细。如果不知道答案，就说不知道，不要试图编造答案。
        上下文：{text_res}，
        问题：{instruction}，
        你的回答：
        """
    elif web_res:
        new_instruction = f"""使用以下上下文来回答最后的问题，尽可能贴近上下文且详细。如果不知道答案，就说不知道，不要试图编造答案。
        上下文：{web_res}，
        问题：{instruction}，
        你的回答：
        """
    else:
        new_instruction = instruction

    for response,finish_reason in get_completion(
            model_name,
            messages=history + [{"role":"user","content":new_instruction}],
            api_url=f'{InterFace.api_server_url}/v1/chat/completions',
            session_id = session_id,
            max_tokens = request_output_len,
            top_p = top_p,
            temperature = temperature,
            repetition_penalty = repetition_penalty
            ):
        if finish_reason == "length":
            print(f"finish reason:{finish_reason}")
        llm_output += response
        if state_chatbot[-1][-1] is None:
            state_chatbot[-1] = (state_chatbot[-1][0], response)
        else:
            state_chatbot[-1] = (state_chatbot[-1][0],
                                 state_chatbot[-1][1] + response
                                 )
        yield (state_chatbot, state_chatbot, enable_btn, disable_btn)

    history.append({"role":"user","content":instruction})
    history.append({"role":"assistant","content":llm_output})
    print(history)

    if len(video_res):
        state_chatbot = state_chatbot + [(None,video_res)]
    # if len(qa_res):
    #     state_chatbot = state_chatbot + [(None,qa_res)]

    yield (state_chatbot, state_chatbot, disable_btn, enable_btn)

def chat_stream_restful_file(file:tempfile._TemporaryFileWrapper, 
                        state_chatbot: Sequence,
                        cancel_btn: gr.Button, 
                        reset_btn: gr.Button,
                        session_id: int,
                        rag:list,
                        top_p: float, 
                        temperature: float,
                        request_output_len: int,
                        repetition_penalty:float,
                        serper_api_key:str):
    """Chat with AI assistant.

    Args:
        instruction (str): user's prompt
        state_chatbot (Sequence): the chatting history
        session_id (int): the session id
    """
    state_chatbot = state_chatbot + [((file.name,), None)]

    yield (state_chatbot, state_chatbot, disable_btn, enable_btn)

    model_names = get_model_list(f'{InterFace.api_server_url}/v1/models')
    model_name = ''
    if isinstance(model_names, list) and len(model_names) > 0:
        model_name = model_names[0]
    else:
        raise ValueError('gradio can find a suitable model from restful-api')
    
    instruction = ocr(file.name)
    ########################### 检索 ################################
    text_res = ""
    video_res = ""
    qa_res = ""
    web_res = ""
    if len(rag):
        # get model name (used in get_completion)
        stq,major,keypoint = get_info(instruction,model_name,session_id)

        messages = history + [{"role":"user","content":instruction}]
        # retrieval
        if "Textbook" in rag:
            text_rag_pc,text_rag_content = textstore.query(keypoint,major)
            if text_rag_pc and text_rag_content:
                if judge(messages,stq,text_rag_content,model_name,session_id):
                    text_res = text_rag_content
                    print("===== RAG TEXT =====")
                    print(text_res)

        if "Video" in rag:
            video_rag_pc,video_rag_url,video_rag_up = videostore.query(keypoint,major)
            if video_rag_pc:
                if judge(messages,stq,video_rag_pc,model_name,session_id):
                    video_res = f"可参考bilibili up主 {video_rag_up} 的视频：{video_rag_url}"
                    print("===== RAG VIDEO =====")
                    print(video_res)

        # if "QA" in rag:
        #     qa_rag_q,qa_rag_a = qastore.query(instruction,major)
        #     if qa_rag_q:
        #         if judge(messages,stq,qa_rag_q,model_name,session_id):
        #             qa_res = "\n".join(["相似题目/例题：",qa_rag_q,"解答：",qa_rag_a])
        #             print("===== RAG QA =====")
        #             print(qa_res)

        if "Internet" in rag:
            assert serper_api_key != None
            webstore = WebStore(embedding,reranker,serper_api_key)
            web_rag = webstore.query(stq)
            if web_rag:
                if judge(messages,stq,web_rag,model_name,session_id):
                    web_res = web_rag
                    print("===== RAG WEB =====")
                    print(web_res)

    ########################### RAG ################################
    llm_output = ""
    if text_res and web_res:
        new_instruction = f"""使用以下两段上下文来回答最后的问题，尽可能贴近上下文且详细。如果不知道答案，就说不知道，不要试图编造答案。
        上下文1：{text_res}，
        上下文2：{web_res}，
        问题：{instruction}，
        你的回答：
        """
    elif text_res:
        new_instruction = f"""使用以下上下文来回答最后的问题，尽可能贴近上下文且详细。如果不知道答案，就说不知道，不要试图编造答案。
        上下文：{text_res}，
        问题：{instruction}，
        你的回答：
        """
    elif web_res:
        new_instruction = f"""使用以下上下文来回答最后的问题，尽可能贴近上下文且详细。如果不知道答案，就说不知道，不要试图编造答案。
        上下文：{web_res}，
        问题：{instruction}，
        你的回答：
        """
    else:
        new_instruction = instruction

    for response,finish_reason in get_completion(
            model_name,
            messages=history + [{"role":"user","content":new_instruction}],
            api_url=f'{InterFace.api_server_url}/v1/chat/completions',
            session_id = session_id,
            max_tokens = request_output_len,
            top_p = top_p,
            temperature = temperature,
            repetition_penalty = repetition_penalty
            ):
        if finish_reason == "length":
            print(f"finish reason:{finish_reason}")
        llm_output += response
        if state_chatbot[-1][-1] is None:
            state_chatbot[-1] = (state_chatbot[-1][0], response)
        else:
            state_chatbot[-1] = (state_chatbot[-1][0],
                                 state_chatbot[-1][1] + response
                                 )
        yield (state_chatbot, state_chatbot, enable_btn, disable_btn)

    history.append({"role":"user","content":instruction})
    history.append({"role":"assistant","content":llm_output})
    print(history)

    if len(video_res):
        state_chatbot = state_chatbot + [(None,video_res)]
    # if len(qa_res):
    #     state_chatbot = state_chatbot + [(None,qa_res)]

    yield (state_chatbot, state_chatbot, disable_btn, enable_btn)


def reset_restful_func(instruction_txtbox: gr.Textbox, state_chatbot: gr.State,
                       session_id: int):
    """reset the session.

    Args:
        instruction_txtbox (str): user's prompt
        state_chatbot (Sequence): the chatting history
        session_id (int): the session id
    """
    state_chatbot = []
    history = []
    # # end the session
    # for response, tokens, finish_reason in get_streaming_response(
    #         '',
    #         f'{InterFace.api_server_url}/v1/chat/interactive',
    #         session_id=session_id,
    #         request_output_len=0,
    #         interactive_mode=False):
    #     pass

    return (
        state_chatbot,
        state_chatbot,
        gr.Textbox.update(value=''),
    )

# # Deprecated
# def cancel_restful_func(state_chatbot: gr.State, cancel_btn: gr.Button,
#                         reset_btn: gr.Button, session_id: int):
#     """stop the session.

#     Args:
#         instruction_txtbox (str): user's prompt
#         state_chatbot (Sequence): the chatting history
#         session_id (int): the session id
#     """
#     yield (state_chatbot, disable_btn, disable_btn)
#     # stop the session
#     for out in get_streaming_response(
#             '',
#             f'{InterFace.api_server_url}/v1/chat/interactive',
#             session_id=session_id,
#             request_output_len=0,
#             cancel=True,
#             interactive_mode=True):
#         pass
#     # end the session
#     for out in get_streaming_response(
#             '',
#             f'{InterFace.api_server_url}/v1/chat/interactive',
#             session_id=session_id,
#             request_output_len=0,
#             interactive_mode=False):
#         pass
#     # resume the session
#     # TODO this is not proper if api server is running pytorch backend
#     messages = []
#     for qa in state_chatbot:
#         messages.append(dict(role='user', content=qa[0]))
#         if qa[1] is not None:
#             messages.append(dict(role='assistant', content=qa[1]))
#     for out in get_streaming_response(
#             messages,
#             f'{InterFace.api_server_url}/v1/chat/interactive',
#             session_id=session_id,
#             request_output_len=0,
#             interactive_mode=True):
#         pass
#     yield (state_chatbot, disable_btn, enable_btn)


def run_api_server(api_server_url: str,
                   server_name: str = 'localhost',
                   server_port: int = 6006,
                   batch_size: int = 32):
    """chat with AI assistant through web ui.

    Args:
        api_server_url (str): restufl api url
        server_name (str): the ip address of gradio server
        server_port (int): the port of gradio server
        batch_size (int): batch size for running Turbomind directly
    """
    InterFace.api_server_url = api_server_url
    model_names = get_model_list(f'{api_server_url}/v1/models')
    model_name = ''
    if isinstance(model_names, list) and len(model_names) > 0:
        model_name = model_names[0]
    else:
        raise ValueError('gradio can find a suitable model from restful-api')

    with gr.Blocks(css=CSS, theme=THEME) as demo:
        state_chatbot = gr.State([])
        state_session_id = gr.State(0)

        with gr.Column(elem_id='container'):
            gr.Markdown('# TeaChat')
            gr.Markdown('**说明：项目应用，不作为实际问答参考**')

            chatbot = gr.Chatbot(elem_id='chatbot',
                                 show_label=False,
                                 latex_delimiters=[{"left": "$", "right": "$", "display": True}],
                                 avatar_images=("./assets/user_avatar.webp","./assets/avatar.webp"),
                                 show_copy_button=True)
            with gr.Row():
                txt = gr.Textbox(
                    scale=4,
                    show_label=False,
                    placeholder="Enter text and press enter, or upload an image",
                    container=False,
                )
                # https://www.gradio.app/3.50.2/docs/gradio/chatbot
                file = gr.UploadButton("📁", file_types=["image"])
            with gr.Row():
                cancel_btn = gr.Button(value='Cancel',
                                       interactive=False)
                reset_btn = gr.Button(value='Reset')
            with gr.Row():
                rag = gr.CheckboxGroup(["Textbook", "Video", "QA","Internet"], 
                                       label="Search in")
                serper_api_key = gr.Textbox(placeholder="Input your Serper Api Key if using Internet",label="Serper API KEY")
            with gr.Row():
                request_output_len = gr.Slider(1,
                                               32768,
                                               value=1024,
                                               step=1,
                                               label='Maximum new tokens')
                top_p = gr.Slider(0.01, 1, value=0.8, step=0.01, label='Top_p')
                temperature = gr.Slider(0.01,
                                        1.5,
                                        value=0.7,
                                        step=0.01,
                                        label='Temperature')
                repetition_penalty = gr.Slider(1.01,
                                        2.0,
                                        value=1.1,
                                        step=0.01,
                                        label='Repetition Penalty')
                
        send_event = txt.submit(chat_stream_restful, [
            txt, 
            state_chatbot, cancel_btn, reset_btn,
            state_session_id,
            rag,
            top_p,temperature,request_output_len,repetition_penalty,
            serper_api_key
            ], 
            [state_chatbot, chatbot, cancel_btn, reset_btn])
        txt.submit(
            lambda: gr.Textbox.update(value=''),
            [],
            [txt],
        )
        file_event = file.upload(chat_stream_restful_file, [
            file, 
            state_chatbot, cancel_btn, reset_btn,
            state_session_id,
            rag,
            top_p,temperature,request_output_len,repetition_penalty,
            serper_api_key
            ], 
            [state_chatbot, chatbot, cancel_btn, reset_btn])
        # cancel_btn.click(
        #     cancel_restful_func,
        #     [state_chatbot, cancel_btn, reset_btn, state_session_id],
        #     [state_chatbot, cancel_btn, reset_btn],
        #     cancels=[send_event])
        cancel_btn.click(fn=None, inputs=None, outputs=None, cancels=[send_event,file_event])


        reset_btn.click(reset_restful_func,
                [txt, state_chatbot, state_session_id],
                [state_chatbot, chatbot, txt],
                cancels=[send_event,file_event])

        def init():
            with InterFace.lock:
                InterFace.global_session_id += 1
            new_session_id = InterFace.global_session_id
            return new_session_id

        demo.load(init, inputs=None, outputs=[state_session_id])

    print(f'server is gonna mount on: http://{server_name}:{server_port}')
    demo.queue(concurrency_count=batch_size, max_size=100,
               api_open=True).launch(
                   max_threads=10,
                   share=True,
                   server_port=server_port,
                   server_name=server_name,
               )
    
if __name__ == "__main__":
    ## lsof -i :6006
    run_api_server("http://localhost:23333","127.0.0.1",6006)
    # run_api_server("http://localhost:23333","0.0.0.0",6006)