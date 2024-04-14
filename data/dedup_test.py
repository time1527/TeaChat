# copy and modify from:
# https://github.com/Cerebras/modelzoo/blob/main/modelzoo/transformers/data_processing/slimpajama/dedup/dedup_train.py
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
import jsonlines
import json
import time
import os
import pickle
import argparse
import os
from glob import glob
from tqdm import tqdm
from utils import split_word,get_files
from datasketch import MinHash
import hashlib
import logging


def sha256str(s):
    h = hashlib.sha256()
    try:
        h.update(s.encode("utf-8"))
    except UnicodeEncodeError:
        # to avoid things like \ud809\udc50\ud808\udefc\ud808\udedb
        h.update(s.encode("utf-8", "replace"))
    return h.hexdigest()


def save(l,path,is_exact = True):
    remove_dict = dict()
    for i in l:
        k = "_".join(i.split("_")[:-1])
        v = int(i.split("_")[-1])
        if k in remove_dict:
            remove_dict[k].append(v)
        else:
            remove_dict[k] = [v]
    t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    suffix = "exact_remove.jsonl" if is_exact else "fuzzy_remove.jsonl"
    output_path = os.path.join(path,t + suffix)
    with open(output_path, "w") as f:
        for k,v in remove_dict.items():
            record = {k:v}
            f.write(json.dumps(record) + "\n")


def dedup_test_exact(args):
    train_dir = args.train_dir
    test_dir = args.test_dir
    
    seen = set()
    if os.path.exists("hashes.txt"):
        logging.info("hashes.txt has existed")
        with open("hashes.txt") as fh:
            for line in tqdm(fh):
                seen.add(line.strip())
    else:
        logging.info("Start to generate hashes.txt")
        hashf = open("hashes.txt", "w")
        files = get_files(test_dir)
        for file in files:
            file_path = os.path.join(test_dir,file)
            with jsonlines.open(file_path) as rdr:
                for idx,ob in enumerate(rdr):
                    text = ob["text"]
                    hash = sha256str(text)
                    hashf.write(hash + "\n")
                    seen.add(hash)
        hashf.close()
    logging.info(f"Finished collecting {len(seen)} hashes for test")

    # Remove elements from train set with hashes seen in eval set.
    remove_set = set()
    for f in tqdm(glob(f"{train_dir}/*/*.jsonl")):
        file_name = f.split("/")[-1]
        logging.info(f"Start {file_name} test exact dedup")
        with jsonlines.open(f) as rdr:
            for idx,ob in enumerate(rdr):
                text = ob["text"]
                hash = sha256str(text)
                if hash in seen:
                    remove_set.add(f"{file_name}_{idx}")
        logging.info(f"Finish {file_name} test exact dedup")
    save(remove_set,train_dir,is_exact=True)
    

def dedup_test_fuzzy(args):
    file = args.lsh_file
    train_dir = args.train_dir
    test_dir = args.test_dir
    fp = open(file,"rb+")
    lsh = pickle.load(fp)

    remove_set = set()
    num_perm = 128
    files = get_files(test_dir)
    for file in files:
        logging.info(f"Start {file} test fuzzy dedup")
        file_path = os.path.join(test_dir,file)
        with jsonlines.open(file_path) as rdr:
            for idx,ob in enumerate(rdr):
                words = split_word(ob["text"])
                minhash = MinHash(num_perm=num_perm)
                [minhash.update(word.encode('utf-8')) for word in words]
                sim_item = lsh.query(minhash)
                if len(sim_item):
                    remove_set.update(set(sim_item))
        logging.info(f"Finish {file} test fuzzy dedup")
    save(remove_set,train_dir,is_exact=False)


def dedup_test_text(args):
    logging.info("Start test exact dedup")
    dedup_test_exact(args)
    logging.info("Finish test exact dedup")
    logging.info("Start test fuzzy dedup")
    dedup_test_fuzzy(args)
    logging.info("Finish test fuzzy dedup")


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--lsh_file",
        type=str,
        required=True,
        help="Path to lsh files.",
    )
    parser.add_argument(
        "--train_dir",
        type=str,
        required=True,
        help="Path to directory of train file.",
    )
    parser.add_argument(
        "--test_dir",
        type=str,
        required=True,
        help="Path to directory of test file.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    dedup_test_text(args)