import jsonlines
import json
from utils import get_files
import os
import argparse


def filter_wanjuan(args):
    input_dir = args.input_dir
    output_dir = args.output_dir
    cols = args.cols
    files = get_files(input_dir)

    os.makedirs(args.output_dir, exist_ok=True)

    for file in files:
        input_path = os.path.join(input_dir, file)
        output_path = os.path.join(output_dir,file)
        with jsonlines.open(input_path) as rdr:
            with open(output_path, "w") as f:
                for item in rdr:
                    # 找到有答案解析且年级符合要求的项
                    if len(item["answer_detail"].replace('\n', '').replace(' ', '')) > 1 \
                        and item["grade"] in cols:
                        record = dict()

                        if len(item["option_a"]) or len(item["option_b"]) or len(item["option_c"]) or len(item["option_d"]):
                            doc = "\n".join([item["q_main"],
                                        item["option_a"],
                                        item["option_b"],
                                        item["option_c"],
                                        item["option_d"]])
                        else:
                            doc = item["q_main"]
                        
                        record["text"] = doc
                        record["major"] = item["major"].replace('\n', '').replace(' ', '')
                        record["keypoint"] = item["keypoint"].replace('\n', '').replace(' ', '')

                        ans = ""
                        if len(item["std_ans"].replace('\n', '').replace(' ', '')):
                            ans = item["std_ans"].replace('\n', '').replace(' ', '')
                        elif len(item["answer"].replace('\n', '').replace(' ', '')):
                            ans = item["answer"].replace('\n', '').replace(' ', '')
                        
                        record["ans"] = ans
                        record["answer_detail"] = item["answer_detail"]                                    
                        f.write(json.dumps(record) + "\n")


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