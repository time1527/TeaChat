from datasketch import MinHash
import jsonlines
import json
import time
import os
import pickle
import argparse
from dedup_train import split


num_perm = 128
remove_list = []

def dedup_test_text(params,col = "text"):
    args = params
    file = args.lsh_file
    test_path = args.test_file
    fp = open(file,"rb+")
    lsh = pickle.load(fp)
    test_path = test_path + ".jsonl"
    with jsonlines.open(test_path) as rdr:
        for idx,ob in enumerate(rdr):
            if isinstance(col,str):
                assert (col in ob.keys()) == True
                words = split(ob[col])
            elif isinstance(col,list):
                assert (set(col).issubset(ob.keys())) == True
                it = "\n".join([ob[c] for c in col])
                words = split(it)
            minhash = MinHash(num_perm=num_perm)
            [minhash.update(word.encode('utf-8')) for word in words]
            sim_item = lsh.query(minhash)
            if len(sim_item):
                remove_list.extend(sim_item)

def save(path):
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

    final_path = os.path.join(path,t + "test_remove.jsonl")
    with open(final_path, "w") as f:
        for k,v in remove_dict.items():
            record = {k:v}
            f.write(json.dumps(record) + "\n")

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
        "--test_file",
        type=str,
        required=True,
        help="Path to test file.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    dedup_test_text(args)