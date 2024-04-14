import os
import jsonlines
from collections import defaultdict
from utils import get_files
import json
import argparse
import logging
import pickle


def merge(path):
    files = get_files(path)
    merged_idx = defaultdict(set)
    for file in files:
        file_path = os.path.join(path,file)
        with jsonlines.open(file_path) as rdr:
            for ob in rdr:
                for k,v in ob.items():
                    merged_idx[k].update(v)
    for k,v in merged_idx.items():
        logging.info(f"There are {len(v)} items to be removed from {k}")
    
    output_path = os.path.join(path,"all_remove_idx.pkl")
    with open(output_path, 'wb') as f:
        pickle.dump(merged_idx, f)
    return merged_idx


def remove_idx(args):
    index_dir = args.index_dir
    index_path = os.path.join(index_dir,"all_remove_idx.pkl")
    with open(index_path, 'rb') as f:
        merged_idx = pickle.load(f)
    # print(merged_idx)

    train_dir = args.train_dir
    final_dir = args.final_dir
    os.makedirs(final_dir, exist_ok=True)
    files = get_files(train_dir)

    for file in files:
        input_path = os.path.join(train_dir,file)
        output_path = os.path.join(final_dir,file)
        tmp_cnt = 0
        cnt = 0
        with jsonlines.open(input_path) as rdr:
            with open(output_path, "w") as f:
                for idx,ob in enumerate(rdr):
                    tmp_cnt += 1
                    if idx in merged_idx[file]:
                        continue
                    f.write(json.dumps(ob) + "\n")
                    cnt += 1
        logging.info(f"Finish final-clean of {file} :{tmp_cnt} to {cnt}")


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--index_dir",
        type=str,
        required=True,
        help="Path to directory containing removed index files.",
    )
    parser.add_argument(
        "--train_dir",
        type=str,
        required=True,
        help="Path to directory where filterd data files will be stored.",
    )
    parser.add_argument(
        "--final_dir",
        type=str,
        required=True,
        help="Path to directory where final data files will be stored.",
    )
    return parser.parse_args()