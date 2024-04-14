import argparse
import os
import dedup_train
import dedup_test
import remove
from utils import rm_if_exists
from MAP import DATASET_FUNC_MAP
import logging

ds_names = [
    "wanjuan",
]

ds_cols = [
    ['高一','高二','高三']
]

logging.basicConfig(
    filename = "sft_main.log",
    filemode = "w",
    encoding = "utf8",
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s",
    datefmt = "%Y/%m/%d %H:%M:%S"
    )

def main(args):
    ds_dirs = ds_names.copy()

    assert len(ds_dirs) == len(ds_cols)
    sft_filter = os.path.join(args.input_dir, "sft_filter")
    rm_if_exists(sft_filter)
    
    # 1. filter
    for idx,dataset in enumerate(ds_dirs):
        filter_args = argparse.Namespace()
        filter_args.input_dir = os.path.join(args.input_dir, dataset)
        filter_args.output_dir = os.path.join(sft_filter, dataset)
        filter_args.cols = ds_cols[idx]
        logging.info(f"Start to filter {dataset}")
        DATASET_FUNC_MAP[dataset](filter_args)
        logging.info(f"Finish filter {dataset}")
    
    # 2. datasets deduplication
    for idx,dataset in enumerate(ds_dirs):
        mh_args = argparse.Namespace()
        mh_args.input_dir = os.path.join(sft_filter, dataset)
        logging.info(f"Start to deduplicate {dataset}")
        dedup_train.dedup_train_text(mh_args)
        logging.info(f"Finish deduplicate {dataset}")
        if idx == len(ds_dirs)-1:
            logging.info("Start to save remove.jsonl")
            dedup_train.save_list(sft_filter)
            logging.info("Finish save remove.jsonl")
            logging.info("Start to save lsh.pickle")
            dedup_train.save_lsh(sft_filter)
            logging.info("Finish save lsh.pickle")

    # 3. - test dataset
    # 3.1 find pickle
    files = os.listdir(sft_filter)
    pickle_files = [file for file in files if file.endswith('.pickle')]
    pickle_file_path = os.path.join(sft_filter, pickle_files[-1])
    # 3.2
    ts_args = argparse.Namespace()
    ts_args.lsh_file = pickle_file_path
    ts_args.train_dir = sft_filter
    ts_args.test_dir = args.test_dir
    logging.info("Start to dedup between train and test")
    dedup_test.dedup_test_text(ts_args)
    logging.info("Finish dedup between train and test")

    # 4. del 
    final = os.path.join(args.input_dir, "sft_final")
    rm_if_exists(final)
    os.makedirs(final, exist_ok=True)
    remove.merge(sft_filter)
    logging.info("Finish merge all removed indexs")
    for dataset in ds_dirs:
        rm_args = argparse.Namespace()
        rm_args.index_dir = sft_filter
        rm_args.train_dir = os.path.join(sft_filter, dataset)
        rm_args.final_dir = os.path.join(final, dataset)
        logging.info(f"Start to remove index in {dataset}")
        remove.remove_idx(rm_args)
        logging.info(f"Finish remove index in {dataset}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir",type = str, help="Dataset input directory.")
    parser.add_argument("--test_dir",type = str, help="Dataset test directory.")
    args = parser.parse_args()
    main(args)