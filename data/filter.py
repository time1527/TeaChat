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
                        doc = "".join([item["q_main"],
                                       item["option_a"],
                                       item["option_b"],
                                       item["option_c"],
                                       item["option_d"]])
                        
                        # 知识点
                        major = item["major"]
                        keypoint = item["keypoint"].replace('\n', '').replace(' ', '')
                        prefix = f"这道题考察的是{major}中的{keypoint}." if len(keypoint) else ""

                        # 最终答案：评测时找答案可通过rfind
                        ans = ""
                        if len(item["std_ans"].replace('\n', '').replace(' ', '')):
                            ans = item["std_ans"].replace('\n', '').replace(' ', '')
                        elif len(item["answer"].replace('\n', '').replace(' ', '')):
                            ans = item["answer"].replace('\n', '').replace(' ', '')
                        
                        suffix = f"因此，这道题的答案是：{ans}." if ans != "" else ""

                        # 回复：知识点 + 解析 + 重复最终答案
                        res = "".join([prefix,item["answer_detail"],suffix])
                        record = {"text": doc,"ans":res}
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