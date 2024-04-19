import json
import jsonlines
import time
import os

wanjuan_badcase = ['BkQQZR_xK3xjTFaMdcNA','BkQQV5jxK3xjS9Dqbm00']


def generate_wanjuan_openai(path):
    t = time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime())

    output_path = os.path.join("/root/dataset",t + "_wanjuan_openai.json")
    # cnt = 0
    with jsonlines.open(path) as rdr:
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
                if len(prefix):a = a + prefix + "\n"
                a = a + answer_detail + "\n"
                if len(ans):a = a + f"综上所述，这道题的答案是：{ans}."
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
                # cnt += 1
                # if cnt % 10000 == 0:
                #     print(record)
                f.write(json.dumps(record,ensure_ascii=False) + "\n")


if __name__ == "__main__":
    input_path = "/root/dataset/clean_sft/wanjuan/part-003756-a894b46e.jsonl"
    generate_wanjuan_openai(input_path)