import jsonlines
import json
import argparse
import os


def wanjuanqa(path, cols=["高一", "高二", "高三"]):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建输出文件的路径，使其与 Python 文件在同一目录
    output_path = os.path.join(script_dir, "qa.jsonl")
    with jsonlines.open(path, "r") as rdr:
        with open(output_path, "w") as f:
            for item in rdr:
                # 过滤掉没有答案的问题
                if (
                    len(item["std_ans"].strip()) == 0
                    and len(item["answer"].strip()) == 0
                ):
                    continue
                if item["grade"] in cols:
                    record = dict()
                    doc = item["q_main"]
                    if len(item["option_a"]):
                        doc = doc + "\n " + "A." + item["option_a"]
                    if len(item["option_b"]):
                        doc = doc + "\n " + "B." + item["option_b"]
                    if len(item["option_c"]):
                        doc = doc + "\n " + "C." + item["option_c"]
                    if len(item["option_d"]):
                        doc = doc + "\n " + "D." + item["option_d"]

                    record["text"] = doc
                    record["q_type"] = item["q_type"]
                    record["keypoint"] = item["keypoint"]
                    record["answer_detail"] = item["answer_detail"]
                    record["major"] = item["major"]
                    record["answer"] = (
                        item["std_ans"] if len(item["std_ans"]) else item["answer"]
                    )
                    record["grade"] = item["grade"]

                    f.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process wanjuanqa data.")
    parser.add_argument("input_path", type=str, help="Path to the input jsonl file")
    args = parser.parse_args()
    wanjuanqa(args.input_path)
