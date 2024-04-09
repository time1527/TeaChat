import jieba
import re
from datasketch import MinHash, MinHashLSH
import jsonlines
import string
import json
import time
import os
import pickle
import argparse


threshold = 0.8
num_perm = 128
lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
remove_list = []


def split(s):
    regex = re.compile("，|。|？|！")
    s = s.lower()
    s = s.translate(str.maketrans("", "", string.punctuation))
    s = re.sub(r"\s+", " ", s.strip())
    ss = [w for w in jieba.lcut(re.sub(regex, '', s)) if w.strip()]
    return  ss# list(map(lambda x: "".join(x), ngrams(split, width)))


def get_files(path):
    files = sorted(os.listdir(path))
    files = list(filter(lambda file: '.jsonl' in file, files))
    return files


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

    final_path = os.path.join(path,t + "remove.jsonl")
    with open(final_path, "w") as f:
        for k,v in remove_dict.items():
            record = {k:v}
            f.write(json.dumps(record) + "\n")


def save_lsh(path):
    t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    with open(os.path.join(path,t + "lsh.pickle"), "wb") as f:
        pickle.dump(lsh, f)


def dedup_train_text(args,col = "text"):
    """minhash+计算重复项+去重"""
    # get .jsonl
    files = get_files(args.input_dir)
    # print(f"in {args.input_dir},there are {files}")
    for file in files:
        file_path = f"{args.input_dir}/{file}"
        print(f"begin to minhah {file_path}")
        with jsonlines.open(file_path) as rdr:
            for idx,ob in enumerate(rdr):
                # print(ob)
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
                    [lsh.remove(sim_idx) for sim_idx in sim_item]
                lsh.insert(f"{file}_{idx}", minhash)


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