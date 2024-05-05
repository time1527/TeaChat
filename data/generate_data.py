import json
import jsonlines
import time
import os
import random

wanjuan_badcase = ['BkQQZR_xK3xjTFaMdcNA','BkQQV5jxK3xjS9Dqbm00']


def generate_wanjuan_openai(dir,path):
    t = time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime())

    output_path = os.path.join(dir,"wanjuan_openai.jsonl")
    cnt = 0
    input_path = os.path.join(dir,path)
    with jsonlines.open(input_path) as rdr:
        with open(output_path, 'w') as f:
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

                # 纠正
                # if keypoint == "80104":keypoint = "氧化还原反应"
                # if item["id"] == 'BkQQV5jxK3xjS9Dqbm00':major = "生物"

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
                if len(prefix):a = a + prefix + "\n"
                a = a + answer_detail + "\n"
                if len(ans):a = a + f"因此，这道题的答案是：{ans}."
                
                # print(a)
                record =     {
                    "messages": [
                        {
                            "role": "user",
                            "content": "请一步步认真思考，回答以下问题：\n {}".format(q)
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
                f.write(json.dumps(record) + "\n")


def generate_cot_openai(dir,path):
    t = time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime())

    output_path = os.path.join(dir,"cot_openai.json")
    cnt = 0
    input_path = os.path.join(dir,path)
    with jsonlines.open(input_path) as rdr:
        with open(output_path, 'w') as f:
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
                    print("=====" * 10)
                f.write(json.dumps(record) + "\n")


def generate_firefly_openai(dir,path):
    t = time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime())

    output_path = os.path.join(dir,"firefly_openai.jsonl")
    cnt = 0
    input_path = os.path.join(dir,path)
    with jsonlines.open(input_path) as rdr:
        with open(output_path, 'w') as f:
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
                    print("=====" * 10)
                f.write(json.dumps(record) + "\n")


def shuffle_gen(dir,path_list):
    data = []
    name = []
    assert len(path_list) > 0
    for path in path_list:
        file_path = os.path.join(dir,path)
        name.append(path.split(".")[0])
        with jsonlines.open(file_path,"r") as rdr:
            for ob in rdr:
                data.append(ob)
    random.shuffle(data)
    random.shuffle(data)
    random.shuffle(data)
    print(data[1000])
    out_name = f'{"_".join(name)}.json'
    with open(os.path.join(dir,out_name), 'w') as file:
        json.dump(data, file, ensure_ascii=False)


if __name__ == "__main__":
    path_prefix = "/home/pika/Dataset/sft/sft_final"
    wanjuan_path = "wanjuan/part-003756-a894b46e.jsonl"
    generate_wanjuan_openai(path_prefix,wanjuan_path)
    cot_path = "Alpaca-CoT/CoT_data.json"
    generate_cot_openai(path_prefix,cot_path)
    firefly_path = "firefly-train-1.1M/firefly-train-1.1M.jsonl"
    generate_firefly_openai(path_prefix,firefly_path)
    shuffle_gen(path_prefix,["cot_openai.json","wanjuan_openai.jsonl","firefly_openai.jsonl"])