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
# https://github.com/Cerebras/modelzoo/blob/Release_2.1.1/modelzoo/transformers/data_processing/slimpajama/preprocessing/normalize_text.py
# https://github.com/Cerebras/modelzoo/blob/Release_2.1.1/modelzoo/transformers/data_processing/slimpajama/preprocessing/filter.py
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
import argparse
import json
from itertools import repeat
from math import ceil
from multiprocessing import Pool, cpu_count
import os

import ftfy
import jsonlines
from tqdm import tqdm
import argparse
import re
import string
from utils import get_files
import logging


def clean(s):
    s = s.lower()
    s = s.translate(str.maketrans("", "", string.punctuation))
    s = re.sub(r"\s+", " ", s.strip())
    return s


def norm_dataset(params):
    """
    norm + clean short items
    """
    files, args = params
    pbar = tqdm(desc=f"Parsed 0 input files. Files written ", disable=False,)
    for file in files:
        input_path = os.path.join(args.input_dir, file)
        output_path = os.path.join(args.output_dir, file)
        cnt = 0
        tmp_cnt = 0
        with jsonlines.open(input_path) as rdr:
            with open(output_path, "w") as f:
                for ob in rdr:
                    tmp_cnt += 1
                    assert (set(args.cols).issubset(ob.keys())) == True
                    doc = [ob[key] for key in set(args.cols)]
                    doc = ["".join(x) if isinstance(x,list) else x for x in doc]
                    doc = "".join(doc)
                    # norm
                    doc = ftfy.fix_text(doc, normalization="NFC")
                    # clean short items
                    if len(clean(doc)) < args.threshold:
                        continue
                    record = {"text": doc}
                    f.write(json.dumps(record) + "\n")
                    cnt += 1
        logging.info(f"Filter {file} : {tmp_cnt} to {cnt}")
    return True


def normalize_text(args):
    os.makedirs(args.output_dir, exist_ok=True)
    files = get_files(args.input_dir)

    n_proc = cpu_count()
    n_chunks = ceil(len(files) / n_proc)
    remain = len(files) % n_proc
    if n_chunks == 1 and remain:
        n_proc = remain
    files = [files[i : i + n_chunks] for i in range(0, len(files), n_chunks)]

    with Pool(processes=n_proc) as pool:
        pbar = tqdm(
            pool.imap(
                norm_dataset, zip(files, repeat(args),),
            ),
            total=len(files),
        )
        for test in pbar:
            pbar.update()
            if test:
                continue

def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Path to directory containing data files.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Path to directory where normlaized data files will be stored.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=100,
        help="Length less than it will be ignored.",
    )

    parser.add_argument(
        "--cols",
        type=list,
        default=["text"],
        help="cols.",
    )

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    normalize_text(args)