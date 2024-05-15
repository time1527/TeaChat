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
import requests
from typing import Optional,Iterable,List
from lmdeploy.serve.openai.api_client import json_loads

def get_completion(
        model_name: str,
        messages: list,
        api_url: str,
        session_id: int,
        temperature: float = 0.1,
        repetition_penalty:float = 1.05,
        top_p: float = 0.8,
        max_tokens: int = 512,
        stream: bool = False,
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
                print(output)
                if "content" in output['choices'][0]['message']:
                    all_outputs +=  output['choices'][0]['message']['content']

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