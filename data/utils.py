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

# copy and modify from:
# https://github.com/Cerebras/modelzoo/blob/Release_2.1.1/modelzoo/transformers/data_processing/slimpajama/utils/utils.py
# https://github.com/Cerebras/modelzoo/blob/Release_2.1.1/modelzoo/transformers/data_processing/slimpajama/preprocessing/normalize_text.py
# https://github.com/Cerebras/modelzoo/blob/Release_2.1.1/modelzoo/transformers/data_processing/slimpajama/dedup/to_hash.py
# Copyright 2022 Cerebras Systems.
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
import jieba
import re
import string
import os
import shutil


def get_files(path):
    """查找目录下的所有jsonl文件"""
    files = sorted(os.listdir(path))
    files = list(filter(lambda file: '.jsonl' in file, files))
    return files


def split_word(s):
    """分词"""
    regex = re.compile("，|。|？|！")
    s = s.lower()
    s = s.translate(str.maketrans("", "", string.punctuation))
    s = re.sub(r"\s+", " ", s.strip())
    ss = [w for w in jieba.lcut(re.sub(regex, '', s)) if w.strip()]
    return  ss# list(map(lambda x: "".join(x), ngrams(split, width)))


def rm_if_exists(path):
    """删除目录"""
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
    except NotADirectoryError:
        os.remove(path)