import json
import jsonlines
import time
import os
import random

wanjuan_badcase = ['BkQQZR_xK3xjTFaMdcNA','BkQQV5jxK3xjS9Dqbm00']
wanjuan_all_format = [
    "这道题的答案是：{ans}，本题考察了{major}的“{keypoint}”，具体来说，{answer_detail}.",
    "答案是：{ans}，这道题考察了{major}的“{keypoint}”，具体来说，{answer_detail}.",
    "这道题考察{major}的“{keypoint}”，{answer_detail}，因此，这道题的答案是：{ans}.",
    "这道题探索了{major}中的“{keypoint}”，{answer_detail}，因此答案为：{ans}.",
    "这道题深入探讨了{major}的“{keypoint}”，通过分析：{answer_detail}，可以得出答案：{ans}.",
    "这道题考察了{major}的“{keypoint}”，具体来说，{answer_detail}，因此答案是：{ans}.",
    "{answer_detail}，这道题考察了{major}的“{keypoint}”，答案是：{ans}.",
    "答案是：{ans}，这道题考察了{major}的“{keypoint}”，其中：{answer_detail}.",
]

wanjuan_wo_major_format = [
    "这道题的答案是：{ans}，本题考察了“{keypoint}”，具体来说，{answer_detail}.",
    "答案是：{ans}，这道题考察了“{keypoint}”，具体来说，{answer_detail}.",
    "这道题考察“{keypoint}”，{answer_detail}，因此，这道题的答案是：{ans}.",
    "这道题探索了“{keypoint}”，{answer_detail}，因此答案为：{ans}.",
    "这道题深入探讨了“{keypoint}”，通过分析：{answer_detail}，可以得出答案：{ans}.",
    "这道题考察了“{keypoint}”，具体来说，{answer_detail}，因此答案是：{ans}.",
    "{answer_detail}，这道题考察了“{keypoint}”，答案是：{ans}.",
    "答案是：{ans}，这道题考察了“{keypoint}”，其中{answer_detail}.",    
]

wanjuan_wo_ans_format = [
    "本题考察了{major}的“{keypoint}”，具体来说，{answer_detail}.",
    "这道题考察了{major}的“{keypoint}”，具体来说，{answer_detail}.",
    "这道题考察{major}的“{keypoint}”，{answer_detail}.",
    "这道题探索了{major}中的“{keypoint}”，{answer_detail}.",
    "这道题深入探讨了{major}的“{keypoint}”，分析：{answer_detail}.",
    "{answer_detail}，这道题考察了{major}的“{keypoint}”.",
    "这道题重点在于{major}的“{keypoint}”，{answer_detail}."  
]

wanjuan_wo_keypoint_format = [
    "这道题的答案是：{ans}，本题考察了{major}的知识点，具体来说，{answer_detail}.",
    "答案是：{ans}，这道题考察了{major}的知识点，具体来说，{answer_detail}.",
    "这道题考察{major}的知识点，{answer_detail}，因此，这道题的答案是：{ans}.",
    "这道题探索了{major}的知识点，{answer_detail}，因此答案为：{ans}.",
    "这道题深入探讨了{major}的知识点，通过分析：{answer_detail}，可以得出答案：{ans}.",
    "这道题考察了{major}的知识点，具体来说，{answer_detail}，因此答案是：{ans}.",
    "{answer_detail}，这道题考察了{major}的知识点，答案是：{ans}.",
    "答案是：{ans}，这道题考察了{major}的知识点，其中{answer_detail}.",
]

wanjuan_w_major_format = [
    "本题考察了{major}的知识点，具体来说，{answer_detail}.",
    "这道题考察了{major}的知识点，具体来说，{answer_detail}.",
    "这道题考察{major}的知识点，{answer_detail}.",
    "这道题探索了{major}的知识点，{answer_detail}.",
    "这道题深入探讨了{major}的知识点，通过分析：{answer_detail}.",
    "{answer_detail}，这道题考察了{major}的知识点.",
    "这道题考察了{major}的知识点，其中{answer_detail}.",
]

wanjuan_w_keypoint_format = [
    "本题考察了“{keypoint}”，具体来说，{answer_detail}.",
    "这道题考察了“{keypoint}”，具体来说，{answer_detail}.",
    "这道题考察“{keypoint}”，{answer_detail}.",
    "这道题探索了“{keypoint}”，{answer_detail}.",
    "这道题深入探讨了“{keypoint}”，分析：{answer_detail}.",
    "{answer_detail}，这道题考察了“{keypoint}”.",
    "这道题重点在于“{keypoint}”，{answer_detail}."  
]

wanjuan_w_ans_format = [
    "这道题的答案是：{ans}，具体来说，{answer_detail}.",
    "答案是：{ans}，具体来说，{answer_detail}.",
    "{answer_detail}，因此，这道题的答案是：{ans}.",
    "{answer_detail}，因此答案为：{ans}.",
    "通过分析：{answer_detail}，可以得出答案：{ans}.",
    "具体来说，{answer_detail}，因此答案是：{ans}.",
    "{answer_detail}，答案是{ans}.",
    "答案是：{ans}，其中{answer_detail}.",
]


def choose_wanjuanformat(major, keypoint, answer_detail, ans):

    if len(major) and len(keypoint) and len(ans):
        chosen_format = random.choice(wanjuan_all_format)
        ff = chosen_format.format(major = major, keypoint = keypoint, answer_detail = answer_detail, ans = ans)
    elif len(keypoint) and len(ans):
        chosen_format = random.choice(wanjuan_wo_major_format)
        ff = chosen_format.format(keypoint = keypoint, answer_detail = answer_detail, ans = ans)
    elif len(major) and len(keypoint):
        chosen_format = random.choice(wanjuan_wo_ans_format)
        ff = chosen_format.format(major = major, keypoint = keypoint, answer_detail = answer_detail)
    elif len(major) and len(ans):
        chosen_format = random.choice(wanjuan_wo_keypoint_format)
        ff = chosen_format.format(major = major,answer_detail = answer_detail, ans = ans)
    elif len(major):
        chosen_format = random.choice(wanjuan_w_major_format)
        ff = chosen_format.format(major = major,answer_detail = answer_detail)
    elif len(keypoint):
        chosen_format = random.choice(wanjuan_w_keypoint_format)
        ff = chosen_format.format(answer_detail = answer_detail,keypoint = keypoint)
    elif len(ans):
        chosen_format = random.choice(wanjuan_w_ans_format)
        ff = chosen_format.format(answer_detail = answer_detail,ans = ans)
    else:
        ff = answer_detail
    return ff


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
                if keypoint == "80104":keypoint = "氧化还原反应"
                if item["id"] == 'BkQQV5jxK3xjS9Dqbm00':major = "生物"

                ans = ""
                if len(item["std_ans"].replace('\n', '').replace(' ', '')):
                    ans = item["std_ans"].replace('\n', '')
                elif len(item["answer"].replace('\n', '').replace(' ', '')):
                    ans = item["answer"].replace('\n', '')
                
                answer_detail = item["answer_detail"]

                # prefix = ""
                # if len(major) and len(keypoint):prefix = f"这道题考察{major}的“{keypoint}”."
                # elif len(major):prefix = f"这道题考察{major}的知识."
                # elif len(keypoint):prefix = f"这道题考察“{keypoint}”."
                
                # a = ""
                # if len(prefix):a = a + prefix + "\n"
                # a = a + answer_detail + "\n"
                # if len(ans):a = a + f"因此，这道题的答案是：{ans}."
                

                # print(a)
                record =     {
                    "messages": [
                        {
                            "role": "user",
                            "content": "请回答以下问题：\n {}".format(q)
                        },
                        {
                            "role": "assistant",
                            "content": "{}".format(choose_wanjuanformat(major=major,
                                                                        keypoint=keypoint,
                                                                        ans=ans,
                                                                        answer_detail=answer_detail))
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