import argparse
import os
import dedup_train
import dedup_test
import remove
from utils import rm_if_exists
from MAP import DATASET_FUNC_MAP

ds_names = [
    "wanjuan",
]

ds_cols = [
    ['高一','高二','高三']
]


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
        DATASET_FUNC_MAP[dataset](filter_args)
    
    # 2. datasets deduplication
    for idx,dataset in enumerate(ds_dirs):
        mh_args = argparse.Namespace()
        mh_args.input_dir = os.path.join(sft_filter, dataset)
        dedup_train.dedup_train_text(mh_args)
        if idx == len(ds_dirs)-1:
            dedup_train.save_list(sft_filter)
            dedup_train.save_lsh(sft_filter)

    # 3. - test dataset
    # 3.1 find pickle
    files = os.listdir(sft_filter)
    pickle_files = [file for file in files if file.endswith('.pickle')]
    pickle_file_path = os.path.join(sft_filter, pickle_files[0])
    # 3.2
    ts_args = argparse.Namespace()
    ts_args.lsh_file = pickle_file_path
    ts_args.train_dir = sft_filter
    ts_args.test_dir = args.test_dir
    dedup_test.dedup_test_text(ts_args)

    # 4. del 
    final = os.path.join(args.input_dir, "sft_final")
    rm_if_exists(final)
    os.makedirs(final, exist_ok=True)
    for dataset in ds_dirs:
        rm_args = argparse.Namespace()
        rm_args.index_dir = sft_filter
        rm_args.train_dir = os.path.join(sft_filter, dataset)
        rm_args.final_dir = os.path.join(final, dataset)
        remove.remove_idx(rm_args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir",type = str, help="Dataset input directory.")
    parser.add_argument("--test_dir",type = str, help="Dataset test directory.")
    args = parser.parse_args()
    main(args)