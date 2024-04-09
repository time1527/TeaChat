# modify from:
# https://github.com/Cerebras/modelzoo/blob/main/modelzoo/transformers/data_processing/slimpajama/main.py
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
import os
import norm_filter,dedup_train as dedup_train,dedup_test
import shutil

ds_names = [
    "educhat-sft-002-data-osm",
    "Chinese-pretraining-dataset",
]

ds_cols = [
    ["data"],
    ["text"]
]

test_ds_names = [
    "agieval_high_school_all",
    "ceval_high_school_all",
    "cmmlu_high_school_all",
    "gaokao_bench_all"
]

def main(args):
    ds_dirs = ds_names.copy()

    assert len(ds_dirs) == len(ds_cols)
    pt_nf = os.path.join(args.input_dir, "pt_nf")
    if os.path.exists(pt_nf):
        shutil.rmtree(pt_nf)
    
    # 1. norm + filter
    for idx,dataset in enumerate(ds_dirs):
        nf_args = argparse.Namespace()
        nf_args.input_dir = os.path.join(args.input_dir, dataset)
        nf_args.output_dir = os.path.join(pt_nf, dataset)
        nf_args.threshold = args.nf_threshold
        nf_args.cols = ds_cols[idx]
        norm_filter.normalize_text(nf_args)

    # 2. datasets deduplication
    for idx,dataset in enumerate(ds_dirs):
        mh_args = argparse.Namespace()
        mh_args.input_dir = os.path.join(pt_nf, dataset)
        dedup_train.dedup_train_text(mh_args)
        if idx == len(ds_dirs)-1:
            dedup_train.save_list(pt_nf)
            dedup_train.save_lsh(pt_nf)
        
    # 3. - test dataset
    ts_dirs = test_ds_names.copy()
    # 3.1 find pickle
    files = os.listdir(pt_nf)
    pickle_files = [file for file in files if file.endswith('.pickle')]
    pickle_file_path = os.path.join(pt_nf, pickle_files[0])
    # 3.2
    for idx,ts in enumerate(ts_dirs):
        ts_args = argparse.Namespace()
        ts_args.lsh_file = pickle_file_path
        ts_args.test_file = os.path.join(args.test_dir,ts)
        dedup_test.dedup_test_text(ts_args)
        if idx == len(ts_dirs)-1:
            dedup_test.save(pt_nf)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir",type = str, help="Dataset input directory.")
    parser.add_argument("--test_dir",type = str, help="Dataset test directory.")
    parser.add_argument("--nf_threshold", type = int,help="nf_threshold.")
    args = parser.parse_args()
    main(args)