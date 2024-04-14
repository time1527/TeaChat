import os
import jsonlines
from collections import defaultdict
from utils import get_files
import json
import argparse
import logging

def merge(path):
    files = get_files(path)
    merged_idx = defaultdict(set)
    for file in files:
        file_path = os.path.join(path,file)
        with jsonlines.open(file_path) as rdr:
            for ob in rdr:
                for k,v in ob.items():
                    merged_idx[k].update(v)
    return merged_idx


def remove_idx(args):
    index_dir = args.index_dir
    merged_idx = merge(index_dir)

    train_dir = args.train_dir
    final_dir = args.final_dir
    os.makedirs(final_dir, exist_ok=True)
    files = get_files(train_dir)
    for file in files:
        input_path = os.path.join(train_dir,file)
        output_path = os.path.join(final_dir,file)
        with jsonlines.open(input_path) as rdr:
            with open(output_path, "w") as f:
                for idx,ob in enumerate(rdr):
                    if idx in merged_idx[file]:
                        continue
                    f.write(json.dumps(ob) + "\n")
        logging.info(f"Finish final-clean of {file}")


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