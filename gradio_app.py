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
from typing import Optional,Sequence,Iterable,List

import requests
import tempfile

from lmdeploy.serve.gradio.constants import CSS, THEME, disable_btn, enable_btn
from lmdeploy.serve.openai.api_client import get_model_list,json_loads

from rag.store import TextStore,VideoStore,QAStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
# from langchain.memory import ConversationBufferMemory
# from ocr.paddleocr import ocr


embedding = HuggingFaceEmbeddings(
     model_name = 'maidalun1020/bce-embedding-base_v1',
     encode_kwargs = {'normalize_embeddings': True})
reranker = HuggingFaceCrossEncoder(model_name = 'maidalun1020/bce-reranker-base_v1')

textstore = TextStore(embedding,reranker)
videostore = VideoStore(embedding,reranker)
qastore = QAStore(embedding,reranker)
# memory = ConversationBufferMemory()
memory = []


class InterFace:
    api_server_url: str = None
    global_session_id: int = 0
    lock = Lock()


def get_completion(
        model_name: str,
        messages: list,
        api_url: str,
        session_id: int,
        temperature: float = 0.1,
        repetition_penalty:float = 1.05,
        top_p: float = 0.8,
        max_tokens: int = 512,
        stream: bool = True,
        ignore_eos: bool = False,
        api_key: Optional[str] = None):
    """
    modify from lmdeploy.serve.openai.api_client.get_streaming_response & chat_completions_v1
    """   
    headers = {'User-Agent': 'Test Client'}
    if api_key is not None:
        headers['Authorization'] = f'Bearer {api_key}'
    pload = {
        'model':model_name,
        'messages': messages,
        'stream': stream,
        'session_id': session_id,
        'max_tokens': max_tokens,
        'ignore_eos': ignore_eos,
        'top_p': top_p,
        'temperature': temperature,
        "repetition_penalty":repetition_penalty
    }
    response = requests.post(api_url,
                             headers=headers,
                             json=pload,
                             stream=stream)
    all_outputs = ""
    for chunk in response.iter_lines(chunk_size=8192,
                                    decode_unicode=False,
                                    delimiter=b'\n'):
        if chunk:
            if stream:
                decoded = chunk.decode('utf-8')
                if decoded == 'data: [DONE]':
                    continue
                if decoded[:6] == 'data: ':
                    decoded = decoded[6:]
                output = json_loads(decoded)
                if "content" in output['choices'][0]['delta']:
                    all_outputs +=  output['choices'][0]['delta']['content']
            else:
                decoded = chunk.decode('utf-8')
                output = json_loads(decoded)
                if "content" in output['choices'][0]['delta']:
                    all_outputs +=  output['choices'][0]['delta']['content']

    return all_outputs


def get_streaming_response(
        prompt: str,
        api_url: str,
        session_id: int,
        request_output_len: int = 2048,
        stream: bool = True,
        interactive_mode: bool = False,
        ignore_eos: bool = False,
        cancel: bool = False,
        top_p: float = 0.8,
        temperature: float = 0.7,
        repetition_penalty:float = 1.05,
        api_key: Optional[str] = None) -> Iterable[List[str]]:
    headers = {'User-Agent': 'Test Client'}
    if api_key is not None:
        headers['Authorization'] = f'Bearer {api_key}'
    pload = {
        'prompt': prompt,
        'stream': stream,
        'session_id': session_id,
        'request_output_len': request_output_len,
        'interactive_mode': interactive_mode,
        'ignore_eos': ignore_eos,
        'cancel': cancel,
        'top_p': top_p,
        'temperature': temperature,
        "repetition_penalty":repetition_penalty
    }
    response = requests.post(api_url,
                             headers=headers,
                             json=pload,
                             stream=stream)
    for chunk in response.iter_lines(chunk_size=8192,
                                     decode_unicode=False,
                                     delimiter=b'\n'):
        if chunk:
            data = json_loads(chunk.decode('utf-8'))
            output = data.pop('text', '')
            tokens = data.pop('tokens', 0)
            finish_reason = data.pop('finish_reason', None)
            yield output, tokens, finish_reason



def chat_stream_restful(instruction: str, state_chatbot: Sequence,
                        cancel_btn: gr.Button, reset_btn: gr.Button,
                        session_id: int,rag:list):
    """Chat with AI assistant.

    Args:
        instruction (str): user's prompt
        state_chatbot (Sequence): the chatting history
        session_id (int): the session id
    """

    state_chatbot = state_chatbot + [(instruction, None)]

    yield (state_chatbot, state_chatbot, disable_btn, enable_btn)
    ########################### img ##############################
    # if type(instruction) == tempfile._TemporaryFileWrapper:
    #     instruction = "".join(ocr(instruction.name))
    ########################### RAG ################################
    if len(rag):
        # get model name (used in get_completion)
        model_names = get_model_list(f'{InterFace.api_server_url}/v1/models')
        model_name = ''
        if isinstance(model_names, list) and len(model_names) > 0:
            model_name = model_names[0]
        else:
            raise ValueError('gradio can find a suitable model from restful-api')

        # condense question
        CONDENSE_QUESTION_PROMPT = f"""给出以下聊天记录和后续问题，用原来的语言将后续问题改写为一个独立的问题。
        聊天记录:{memory}
        后续输入:{instruction}
        独立的问题:
        """
        standalone_question = get_completion(
            model_name,
            [{"role":"user","content":CONDENSE_QUESTION_PROMPT}],
            f'{InterFace.api_server_url}/v1/chat/completions',
            session_id=session_id,
            )
        print(CONDENSE_QUESTION_PROMPT)
        print(standalone_question)
        # get major
        major_list = ["语文","数学","英语","地理","历史","政治","物理","化学","生物"]
        major_prompt = f"""请判断以下文本属于哪一学科，只能输出两个字的回答。
        文本：{standalone_question}，
        选项：{major_list}，
        答案：
        """
        major_resp = get_completion(
            model_name,
            [{"role":"user","content":major_prompt}],
            f'{InterFace.api_server_url}/v1/chat/completions',
            session_id=session_id
            )
        # TODO:use first major
        found_majors = [major for major in major_list if major in major_resp]
        print(f"found majors = {found_majors}")
        if len(found_majors) == 1:major = found_majors[0]
        else: major = ""
        print(f"major = {major}")

        # get keypoint
        key_prompt = f"""请判断以下文本考察什么知识点。请只输出知识点，不需要输出分析步骤。
        文本：{standalone_question}，
        知识点：
        """
        key_resp = get_completion(
            model_name,
            [{"role":"user","content":key_prompt}],
            f'{InterFace.api_server_url}/v1/chat/completions',
            session_id=session_id,
            )
        print(f"keypoint = {key_resp}")

        # retrieval
        if "Textbook" in rag:
            text_rag_pc,text_rag_content = textstore.query(key_resp,major)
            if len(text_rag_pc) == 0 or len(text_rag_content) == 0:
                text_res = ""
            else:
                use_text_prompt = f"""请判断以下聊天记录是否与文本高度相关。只允许输出一个字“是”或者“否”。
                聊天记录:{memory}
                文本:{text_rag_content}
                是否高度相关:"""
                use_text_resp = get_completion(
                    model_name,
                    [{"role":"user","content":use_text_prompt}],
                    f'{InterFace.api_server_url}/v1/chat/completions',
                    session_id=session_id,
                )
                if  "是" in use_text_resp:
                    text_res = text_rag_content
                else:
                    text_res = ""
        else:
            text_res = ""
        
        if "Video" in rag:
            video_rag_pc,video_rag_url,video_rag_up = videostore.query(key_resp,major)
            if len(video_rag_pc) == 0:
                video_res = ""
            else:
                use_video_prompt = f"""请判断以下聊天记录是否与文本高度相关。只允许输出一个字“是”或者“否”。
                聊天记录:{memory}
                文本:{video_rag_pc}
                是否高度相关:"""
                use_video_resp = get_completion(
                    model_name,
                    [{"role":"user","content":use_video_prompt}],
                    f'{InterFace.api_server_url}/v1/chat/completions',
                    session_id=session_id,
                )
                if  "是" in use_video_resp:
                    video_res = f"可参考bilibili up主 {video_rag_up} 的视频：{video_rag_url}"
                else:
                    video_res = ""
        else:
            video_res = ""
        
        if "QA" in rag:
            qa_rag_q,qa_rag_a = qastore.query(instruction,major)
            if len(qa_rag_q) == 0:
                qa_res = ""
            else:
                use_qa_prompt = f"""请判断以下聊天记录是否与文本高度相关。只允许输出一个字“是”或者“否”。
                聊天记录:{memory}
                文本:{qa_rag_q}
                是否高度相关:"""
                use_qa_resp = get_completion(
                    model_name,
                    [{"role":"user","content":use_qa_prompt}],
                    f'{InterFace.api_server_url}/v1/chat/completions',
                    session_id=session_id,
                )
                if  "是" in use_qa_resp:
                    qa_res = "\n".join(["相似题目/例题：",qa_rag_q,"解答：",qa_rag_a])
                else:
                    qa_res = ""
        else:
            qa_res = ""


    ########################### RAG ################################
    llm_output = ""
    new_instruction = f"""使用以下上下文来回答最后的问题。如果不知道答案，就说不知道，不要试图编造答案。
    上下文：{text_res}，
    问题：{instruction}，
    你的回答：
    """
    print(new_instruction)
    for response, tokens, finish_reason in get_streaming_response(
            new_instruction,
            f'{InterFace.api_server_url}/v1/chat/interactive',
            session_id=session_id,
            interactive_mode=True,
            temperature=0.2,
            repetition_penalty = 1.1
            ):
        if finish_reason == 'length' and tokens == 0:
            gr.Warning('WARNING: exceed session max length.'
                       ' Please restart the session by reset button.')
        if tokens < 0:
            gr.Warning('WARNING: running on the old session.'
                       ' Please restart the session by reset button.')
        if state_chatbot[-1][-1] is None:
            state_chatbot[-1] = (state_chatbot[-1][0], response)
        else:
            state_chatbot[-1] = (state_chatbot[-1][0],
                                 state_chatbot[-1][1] + response
                                 )  # piece by piece
        yield (state_chatbot, state_chatbot, enable_btn, disable_btn)
        llm_output += response
    memory.append({"role":"user","content":instruction})
    memory.append({"role":"assistant","content":llm_output})

    if len(video_res):
        state_chatbot = state_chatbot + [(None,video_res)]
    if len(qa_res):
        state_chatbot = state_chatbot + [(None,qa_res)]

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
    memory = []
    # end the session
    for response, tokens, finish_reason in get_streaming_response(
            '',
            f'{InterFace.api_server_url}/v1/chat/interactive',
            session_id=session_id,
            request_output_len=0,
            interactive_mode=False):
        pass

    return (
        state_chatbot,
        state_chatbot,
        gr.Textbox.update(value=''),
    )


def cancel_restful_func(state_chatbot: gr.State, cancel_btn: gr.Button,
                        reset_btn: gr.Button, session_id: int):
    """stop the session.

    Args:
        instruction_txtbox (str): user's prompt
        state_chatbot (Sequence): the chatting history
        session_id (int): the session id
    """
    yield (state_chatbot, disable_btn, disable_btn)
    # stop the session
    for out in get_streaming_response(
            '',
            f'{InterFace.api_server_url}/v1/chat/interactive',
            session_id=session_id,
            request_output_len=0,
            cancel=True,
            interactive_mode=True):
        pass
    # end the session
    for out in get_streaming_response(
            '',
            f'{InterFace.api_server_url}/v1/chat/interactive',
            session_id=session_id,
            request_output_len=0,
            interactive_mode=False):
        pass
    # resume the session
    # TODO this is not proper if api server is running pytorch backend
    messages = []
    for qa in state_chatbot:
        messages.append(dict(role='user', content=qa[0]))
        if qa[1] is not None:
            messages.append(dict(role='assistant', content=qa[1]))
    for out in get_streaming_response(
            messages,
            f'{InterFace.api_server_url}/v1/chat/interactive',
            session_id=session_id,
            request_output_len=0,
            interactive_mode=True):
        pass
    yield (state_chatbot, disable_btn, enable_btn)


# def add_text(history, text):
#     history = history + [(text, None)]
#     return history, gr.Textbox(value="", interactive=False)


# def add_file(history, file):
#     history = history + [((file.name,), None)]
#     return history


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
            gr.Markdown('## TeaChat')

            chatbot = gr.Chatbot(elem_id='chatbot',
                                 show_label=False,
                                 latex_delimiters=[{"left": "$", "right": "$", "display": True}],
                                 avatar_images=("./assets/user_avatar.webp","./assets/avatar.webp"))
            # instruction_txtbox = gr.Textbox(
            #     placeholder='Please input the question',
            #     show_label=False)
            txt = gr.Textbox(
                scale=4,
                show_label=False,
                placeholder="Enter text and press enter, or upload an image",
                container=False,
            )
            # btn = gr.UploadButton("📁", file_types=["image", "video", "audio"])
            
            with gr.Row():
                cancel_btn = gr.Button(value='Cancel',
                                       interactive=False)
                reset_btn = gr.Button(value='Reset')
            with gr.Row():
                rag = gr.CheckboxGroup(["Textbook", "Video", "QA","Internet"], 
                                       label="Search in")
        # send_event = instruction_txtbox.submit(chat_stream_restful, [
        #     instruction_txtbox, state_chatbot, cancel_btn, reset_btn,
        #     state_session_id,rag], [state_chatbot, chatbot, cancel_btn, reset_btn])
        # instruction_txtbox.submit(
        #     lambda: gr.Textbox.update(value=''),
        #     [],
        #     [instruction_txtbox],
        # )
        send_event = txt.submit(chat_stream_restful, [
            txt, state_chatbot, cancel_btn, reset_btn,
            state_session_id,rag], [state_chatbot, chatbot, cancel_btn, reset_btn])
        txt.submit(
            lambda: gr.Textbox.update(value=''),
            [],
            [txt],
        )
        # file_msg = btn.upload(chat_stream_restful, [
        #     txt, state_chatbot, cancel_btn, reset_btn,
        #     state_session_id,rag], [state_chatbot, chatbot, cancel_btn, reset_btn])
        cancel_btn.click(
            cancel_restful_func,
            [state_chatbot, cancel_btn, reset_btn, state_session_id],
            [state_chatbot, cancel_btn, reset_btn],
            cancels=[send_event])

        # reset_btn.click(reset_restful_func,
        #                 [instruction_txtbox, state_chatbot, state_session_id],
        #                 [state_chatbot, chatbot, instruction_txtbox],
        #                 cancels=[send_event])
        reset_btn.click(reset_restful_func,
                [txt, state_chatbot, state_session_id],
                [state_chatbot, chatbot, txt],
                cancels=[send_event])

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
    run_api_server("http://localhost:23333","127.0.0.1",6056)