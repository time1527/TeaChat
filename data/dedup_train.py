import os
from datasketch import MinHash, MinHashLSH
import jsonlines
import json
import time
import pickle
import argparse
from utils import split_word,get_files
import logging


threshold = 0.8
num_perm = 128
lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
remove_list = []

def save_list(path):
    l = remove_list.copy()
    remove_dict = dict()
    for i in l:
        k = "_".join(i.split("_")[:-1])
        v = int(i.split("_")[-1])
        if k in remove_dict:
            remove_dict[k].append(v)
        else:
            remove_dict[k] = [v]
    t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    output_path = os.path.join(path,t + "remove.jsonl")
    with open(output_path, "w") as f:
        for k,v in remove_dict.items():
            record = {k:v}
            f.write(json.dumps(record) + "\n")


def save_lsh(path):
    t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    with open(os.path.join(path,t + "lsh.pickle"), "wb") as f:
        pickle.dump(lsh, f)


def dedup_train_text(args,col = "text"):
    """minhash+计算重复项+去重"""
    files = get_files(args.input_dir)
    for file in files:
        logging.info(f"Start to minhash and dedup {file}")
        file_path = os.path.join(args.input_dir,file)
        with jsonlines.open(file_path) as rdr:
            for idx,ob in enumerate(rdr):
                words = split_word(ob["text"])
                minhash = MinHash(num_perm=num_perm)
                [minhash.update(word.encode('utf-8')) for word in words]
                sim_item = lsh.query(minhash)
                if len(sim_item):
                    remove_list.extend(sim_item)
                    [lsh.remove(sim_idx) for sim_idx in sim_item]
                lsh.insert(f"{file}_{idx}", minhash)
        logging.info(f"Finish {file} minhash and dedup")


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
    # parser.add_argument(
    #     "--threshold",
    #     type=int,
    #     default=0.8,
    #     help="minhash threshold.",
    # )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    dedup_train_text(args)