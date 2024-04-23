import json
import jsonlines
import time
import os

wanjuan_badcase = ['BkQQZR_xK3xjTFaMdcNA','BkQQV5jxK3xjS9Dqbm00']


def generate_wanjuan_openai(dir,path):
    t = time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime())

    output_path = os.path.join(dir,t + "_wanjuan_openai.json")
    cnt = 0
    input_path = os.path.join(dir,path)
    with jsonlines.open(input_path) as rdr:
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in rdr:

                # delete bad case
                if item["id"] in wanjuan_badcase:continue

                q = item["q_main"]
                if len(item["option_a"]):q = q + "\n " + "A."+item["option_a"]
                if len(item["option_b"]):q = q + "\n " + "B."+item["option_b"]
                if len(item["option_c"]):q = q + "\n " + "C."+item["option_c"]
                if len(item["option_d"]):q = q + "\n " + "D."+item["option_d"]

                major = item["major"].replace('\n', '').replace(' ', '')
                keypoint = item["keypoint"].replace('\n', '').replace(' ', '') if item["keypoint"] != None else ""

                ans = ""
                if len(item["std_ans"].replace('\n', '').replace(' ', '')):
                    ans = item["std_ans"].replace('\n', '')
                elif len(item["answer"].replace('\n', '').replace(' ', '')):
                    ans = item["answer"].replace('\n', '')
                
                answer_detail = item["answer_detail"]

                prefix = ""
                if len(major) and len(keypoint):prefix = f"这道题考察{major}的“{keypoint}”."
                elif len(major):prefix = f"这道题考察{major}的知识."
                elif len(keypoint):prefix = f"这道题考察“{keypoint}”."
                
                a = ""
                if len(ans):a = a + f"这道题的答案是：{ans}." + "\n"
                if len(prefix):a = a + prefix + "\n"
                a = a + answer_detail

                # print(a)
                record =     {
                    "messages": [
                        {
                            "role": "user",
                            "content": "{}".format(q)
                        },
                        {
                            "role": "assistant",
                            "content": "{}".format(a)
                        }
                    ]
                }
                cnt += 1
                if cnt % 10000 == 0:
                    print(record)
                    print("=====" * 10)
                f.write(json.dumps(record,ensure_ascii=False) + "\n")


def generate_cot_openai(dir,path):
    t = time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime())

    output_path = os.path.join(dir,t + "_cot_openai.json")
    cnt = 0
    input_path = os.path.join(dir,path)
    with jsonlines.open(input_path) as rdr:
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in rdr:
                q = item['instruction']
                if len(item["input"]):q = q + "\n" + item["input"]
                a = item['output']
                # print(a)
                record =     {
                    "messages": [
                        {
                            "role": "user",
                            "content": "{}".format(q)
                        },
                        {
                            "role": "assistant",
                            "content": "{}".format(a)
                        }
                    ]
                }
                cnt += 1
                if cnt % 10000 == 0:
                    print(record)
                f.write(json.dumps(record,ensure_ascii=False) + "\n")


def generate_firefly_openai(dir,path):
    t = time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime())

    output_path = os.path.join(dir,t + "_firefly_openai.json")
    cnt = 0
    input_path = os.path.join(dir,path)
    with jsonlines.open(input_path) as rdr:
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in rdr:
                q = item['input']
                a = item['target']
                # print(a)
                record =     {
                    "messages": [
                        {
                            "role": "user",
                            "content": "{}".format(q)
                        },
                        {
                            "role": "assistant",
                            "content": "{}".format(a)
                        }
                    ]
                }
                cnt += 1
                if cnt % 10000 == 0:
                    print(record)
                f.write(json.dumps(record,ensure_ascii=False) + "\n")


if __name__ == "__main__":
    path_prefix = "/home/pika/Dataset/sft/sft_final"
    # wanjuan_path = "wanjuan/part-003756-a894b46e.jsonl"
    # generate_wanjuan_openai(path_prefix,wanjuan_path)
    # cot_path = "Alpaca-CoT/CoT_data.json"
    # generate_cot_openai(path_prefix,cot_path)
    firefly_path = "firefly-train-1.1M/firefly-train-1.1M.jsonl"
    generate_firefly_openai(path_prefix,firefly_path)