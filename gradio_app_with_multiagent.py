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
import time
import asyncio

# lmdeploy
from lmdeploy.serve.gradio.constants import CSS, THEME, disable_btn, enable_btn
from lmdeploy.serve.openai.api_client import get_model_list

# local
from multi_agent import *
from rag.store import TextStore, VideoStore, QAStore, WebStore
from utils.chat import get_completion, get_streaming_response

# from ocr.paddleocr import ocr
# langchain
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

# from langchain.memory import ConversationBufferMemory
# metagpt
from metagpt.actions import UserRequirement
from metagpt.schema import Message
from metagpt.const import MESSAGE_ROUTE_TO_ALL

# path config
from settings import EMBEDDING, RERANKER


embedding = HuggingFaceEmbeddings(
    model_name=EMBEDDING, encode_kwargs={"normalize_embeddings": True}
)
reranker = HuggingFaceCrossEncoder(model_name=RERANKER)


textstore = TextStore(embedding, reranker)
videostore = VideoStore(embedding, reranker)
qastore = QAStore(embedding, reranker)  # slow to load
history = []


class InterFace:
    api_server_url: str = None
    global_session_id: int = 0
    lock = Lock()


async def chat_stream_restful(
    instruction: str,
    state_chatbot: Sequence,
    cancel_btn: gr.Button,
    reset_btn: gr.Button,
    session_id: int,
    rag: list,
    top_p: float,
    temperature: float,
    request_output_len: int,
    repetition_penalty: float,
    serper_api_key: str,
):
    """Chat with AI assistant.

    Args:
        instruction (str): user's prompt
        state_chatbot (Sequence): the chatting history
        session_id (int): the session id
    """

    state_chatbot = state_chatbot + [(instruction, None)]

    yield (state_chatbot, state_chatbot, disable_btn, enable_btn)

    ########################### 检索 ################################
    text_res = ""
    video_res = ""
    qa_res = ""
    web_res = ""
    if len(rag):
        use_text = "Textbook" in rag
        use_video = "Video" in rag
        use_qa = "QA" in rag
        use_web = "Internet" in rag

        if use_web:
            assert serper_api_key != None

        env = RecordEnvironment()
        roles = [
            Classifier(
                use_text=use_text, use_video=use_video, use_qa=use_qa, use_web=use_web
            )
        ]
        if use_text:
            roles.append(TextbookRetriever(textstore=textstore))
        if use_video:
            roles.append(VideoRetriever(videostore=videostore))
        if use_qa:
            roles.append(QARetriever(qastore=qastore))
        if use_web:
            roles.append(
                WebRetriever(
                    webstore=WebStore(
                        embedding=embedding,
                        reranker=reranker,
                        serper_api_key=serper_api_key,
                    )
                )
            )

        env.add_roles(roles)

        env.publish_message(
            Message(
                role="Human",
                content=str(
                    {
                        "history": "\n".join(
                            f"{entry['role']}:{entry['content']}" for entry in history
                        ),
                        "instruction": instruction,
                    }
                ),
                cause_by=UserRequirement,
                sent_from=UserRequirement,
                send_to=MESSAGE_ROUTE_TO_ALL,
            ),
            peekable=False,
        )

        n_round = 3
        while n_round > 0:
            # self._save()
            n_round -= 1
            await env.run()

        text_res = env.record["TextbookRetriever"] if use_text else ""
        video_res = env.record["VideoRetriever"] if use_video else ""
        qa_res = env.record["QARetriever"] if use_qa else ""
        web_res = env.record["WebRetriever"] if use_web else ""

    ########################### 检索 ################################
    ########################### 生成 ################################
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
    # Question: api chat history里会包含text_res、web_res内容，而不是纯对话，而且检索到的内容会增加总的input token

    # for response, tokens, finish_reason in get_streaming_response(
    #         new_instruction,
    #         f'{InterFace.api_server_url}/v1/chat/interactive',
    #         session_id=session_id,
    #         request_output_len=request_output_len,
    #         interactive_mode=True,
    #         top_p=top_p,
    #         temperature=temperature,
    #         repetition_penalty = repetition_penalty
    #         ):
    #     if finish_reason == "length":
    #         print(f"finish reason:{finish_reason},\ntokens:{tokens}")
    #     if finish_reason == 'length' and tokens == 0:
    #         gr.Warning('WARNING: exceed session max length.'
    #                    ' Please restart the session by reset button.')
    #     if tokens < 0:
    #         gr.Warning('WARNING: running on the old session.'
    #                    ' Please restart the session by reset button.')
    #     if state_chatbot[-1][-1] is None:
    #         state_chatbot[-1] = (state_chatbot[-1][0], response)
    #     else:
    #         state_chatbot[-1] = (state_chatbot[-1][0],
    #                              state_chatbot[-1][1] + response
    #                              )  # piece by piece
    #     yield (state_chatbot, state_chatbot, enable_btn, disable_btn)
    #     llm_output += response

    # A: use get_completion and `messages`
    model_names = get_model_list(f"{InterFace.api_server_url}/v1/models")
    model_name = ""
    if isinstance(model_names, list) and len(model_names) > 0:
        model_name = model_names[0]
    else:
        raise ValueError("gradio can find a suitable model from restful-api")

    for response, finish_reason in get_completion(
        model_name,
        messages=history + [{"role": "user", "content": new_instruction}],
        api_url=f"{InterFace.api_server_url}/v1/chat/completions",
        session_id=session_id,
        max_tokens=request_output_len,
        top_p=top_p,
        temperature=temperature,
        repetition_penalty=repetition_penalty,
    ):
        if finish_reason == "length":
            print(f"finish reason:{finish_reason}")
        llm_output += response
        if state_chatbot[-1][-1] is None:
            state_chatbot[-1] = (state_chatbot[-1][0], response)
        else:
            state_chatbot[-1] = (state_chatbot[-1][0], state_chatbot[-1][1] + response)
        yield (state_chatbot, state_chatbot, enable_btn, disable_btn)

    history.append({"role": "user", "content": instruction})
    history.append({"role": "assistant", "content": llm_output})
    print(history)

    if len(video_res):
        state_chatbot = state_chatbot + [(None, video_res)]
    if len(qa_res):
        state_chatbot = state_chatbot + [(None, qa_res)]

    yield (state_chatbot, state_chatbot, disable_btn, enable_btn)


def reset_restful_func(
    instruction_txtbox: gr.Textbox, state_chatbot: gr.State, session_id: int
):
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
        gr.Textbox.update(value=""),
    )


# Deprecated
def cancel_restful_func(
    state_chatbot: gr.State,
    cancel_btn: gr.Button,
    reset_btn: gr.Button,
    session_id: int,
):
    """stop the session.

    Args:
        instruction_txtbox (str): user's prompt
        state_chatbot (Sequence): the chatting history
        session_id (int): the session id
    """
    yield (state_chatbot, disable_btn, disable_btn)
    # stop the session
    for out in get_streaming_response(
        "",
        f"{InterFace.api_server_url}/v1/chat/interactive",
        session_id=session_id,
        request_output_len=0,
        cancel=True,
        interactive_mode=True,
    ):
        pass
    # end the session
    for out in get_streaming_response(
        "",
        f"{InterFace.api_server_url}/v1/chat/interactive",
        session_id=session_id,
        request_output_len=0,
        interactive_mode=False,
    ):
        pass
    # resume the session
    # TODO this is not proper if api server is running pytorch backend
    messages = []
    for qa in state_chatbot:
        # video/qa
        # user:None
        # assistant: balabala
        if qa[0] is not None:
            messages.append(dict(role="user", content=qa[0]))
            if qa[1] is not None:
                messages.append(dict(role="assistant", content=qa[1]))
    # messages 与 history的区别：messages里包含了被打断的对话
    for out in get_streaming_response(
        messages,
        f"{InterFace.api_server_url}/v1/chat/interactive",
        session_id=session_id,
        request_output_len=0,
        interactive_mode=True,
    ):
        pass
    yield (state_chatbot, disable_btn, enable_btn)


def run_api_server(
    api_server_url: str,
    server_name: str = "localhost",
    server_port: int = 6006,
    batch_size: int = 32,
):
    """chat with AI assistant through web ui.

    Args:
        api_server_url (str): restufl api url
        server_name (str): the ip address of gradio server
        server_port (int): the port of gradio server
        batch_size (int): batch size for running Turbomind directly
    """
    InterFace.api_server_url = api_server_url
    model_names = get_model_list(f"{api_server_url}/v1/models")
    model_name = ""
    if isinstance(model_names, list) and len(model_names) > 0:
        model_name = model_names[0]
    else:
        raise ValueError("gradio can find a suitable model from restful-api")

    with gr.Blocks(css=CSS, theme=THEME) as demo:
        state_chatbot = gr.State([])
        state_session_id = gr.State(0)

        with gr.Column(elem_id="container"):
            gr.Markdown("# TeaChat")
            gr.Markdown("**说明：项目应用，不作为实际问答参考**")

            chatbot = gr.Chatbot(
                elem_id="chatbot",
                show_label=False,
                latex_delimiters=[{"left": "$", "right": "$", "display": True}],
                avatar_images=("./assets/user_avatar.webp", "./assets/avatar.webp"),
            )
            txt = gr.Textbox(
                scale=4,
                show_label=False,
                placeholder="Enter text and press enter",
                container=False,
            )

            with gr.Row():
                cancel_btn = gr.Button(value="Cancel", interactive=False)
                reset_btn = gr.Button(value="Reset")
            with gr.Row():
                rag = gr.CheckboxGroup(
                    ["Textbook", "Video", "QA", "Internet"], label="Search in"
                )
                serper_api_key = gr.Textbox(
                    placeholder="Input your Serper Api Key if using Internet",
                    label="Serper API KEY",
                )
            with gr.Row():
                request_output_len = gr.Slider(
                    1, 32768, value=1024, step=1, label="Maximum new tokens"
                )
                top_p = gr.Slider(0.01, 1, value=0.8, step=0.01, label="Top_p")
                temperature = gr.Slider(
                    0.01, 1.5, value=0.7, step=0.01, label="Temperature"
                )
                repetition_penalty = gr.Slider(
                    1.01, 2.0, value=1.1, step=0.01, label="Repetition Penalty"
                )
        send_event = txt.submit(
            chat_stream_restful,
            [
                txt,
                state_chatbot,
                cancel_btn,
                reset_btn,
                state_session_id,
                rag,
                top_p,
                temperature,
                request_output_len,
                repetition_penalty,
                serper_api_key,
            ],
            [state_chatbot, chatbot, cancel_btn, reset_btn],
        )

        txt.submit(
            lambda: gr.Textbox.update(value=""),
            [],
            [txt],
        )
        cancel_btn.click(fn=None, inputs=None, outputs=None, cancels=[send_event])
        # cancel_btn.click(
        #     cancel_restful_func,
        #     [state_chatbot, cancel_btn, reset_btn, state_session_id],
        #     [state_chatbot, cancel_btn, reset_btn],
        #     cancels=[send_event])

        reset_btn.click(
            reset_restful_func,
            [txt, state_chatbot, state_session_id],
            [state_chatbot, chatbot, txt],
            cancels=[send_event],
        )

        def init():
            with InterFace.lock:
                InterFace.global_session_id += 1
            new_session_id = InterFace.global_session_id
            return new_session_id

        demo.load(init, inputs=None, outputs=[state_session_id])

    print(f"server is gonna mount on: http://{server_name}:{server_port}")
    demo.queue(concurrency_count=batch_size, max_size=100, api_open=True).launch(
        max_threads=10,
        share=True,
        server_port=server_port,
        server_name=server_name,
    )


if __name__ == "__main__":
    run_api_server("http://127.0.0.1:23333", "127.0.0.1", 6006)
    # run_api_server("http://localhost:23333","0.0.0.0",6006)
