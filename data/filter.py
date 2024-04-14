import jsonlines
import json
from utils import get_files
import os
import argparse
import logging


def filter_wanjuan(args):
    input_dir = args.input_dir
    output_dir = args.output_dir
    cols = args.cols
    files = get_files(input_dir)

    os.makedirs(args.output_dir, exist_ok=True)

    for file in files:
        input_path = os.path.join(input_dir, file)
        output_path = os.path.join(output_dir,file)
        cnt = 0
        tmp_cnt = 0
        logging.info(f"Start to filter {file}")
        with jsonlines.open(input_path) as rdr:
            with open(output_path, "w") as f:
                for item in rdr:
                    tmp_cnt += 1
                    # 找到有答案解析且年级符合要求的项
                    if len(item["answer_detail"].replace('\n', '').replace(' ', '')) > 1 \
                        and item["grade"] in cols:
                        record = dict()
                        doc = item["q_main"].replace('\n', '').replace(' ', '')
                        if len(item["option_a"]):doc = doc + "\n " + "A."+item["option_a"]
                        if len(item["option_b"]):doc = doc + "\n " + "B."+item["option_b"]
                        if len(item["option_c"]):doc = doc + "\n " + "C."+item["option_c"]
                        if len(item["option_d"]):doc = doc + "\n " + "D."+item["option_d"]
                        
                        record["text"] = doc
                        # record["major"] = item["major"].replace('\n', '').replace(' ', '')
                        # record["keypoint"] = item["keypoint"].replace('\n', '').replace(' ', '') if item["keypoint"] != None else item["keypoint"]

                        # ans = ""
                        # if len(item["std_ans"].replace('\n', '').replace(' ', '')):
                        #     ans = item["std_ans"].replace('\n', '').replace(' ', '')
                        # elif len(item["answer"].replace('\n', '').replace(' ', '')):
                        #     ans = item["answer"].replace('\n', '').replace(' ', '')
                        
                        # record["ans"] = ans
                        # record["answer_detail"] = item["answer_detail"]
                        record["raw"] = item
            
                        f.write(json.dumps(record) + "\n")
                        cnt += 1
        logging.info(f"Filter {file} : {tmp_cnt} to {cnt}")


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
        help="Path to directory where filterd data files will be stored.",
    )
    parser.add_argument(
        "--cols",
        type=list,
        default=["text"],
        help="cols.",
    )

    return parser.parse_args()