import os
import jsonlines
import json

        
def wanjuanqa(path,cols = ['高一','高二','高三']):
    output_path = "qa.jsonl"
    with jsonlines.open(path,"r") as rdr:
        with open(output_path, "w") as f:
            for item in rdr:
                if item["grade"] in cols:
                    record = dict()
                    doc = item["q_main"]
                    if len(item["option_a"]):doc = doc + "\n " + "A."+item["option_a"]
                    if len(item["option_b"]):doc = doc + "\n " + "B."+item["option_b"]
                    if len(item["option_c"]):doc = doc + "\n " + "C."+item["option_c"]
                    if len(item["option_d"]):doc = doc + "\n " + "D."+item["option_d"]
                    
                    record["text"] = doc
                    record['q_type'] = item['q_type']
                    record['keypoint'] = item['keypoint']
                    record['answer_detail'] = item['answer_detail']
                    record["major"] = item["major"]
                    record["answer"] = item['std_ans'] if len(item['std_ans']) else item['answer']
                    record['grade'] = item['grade']
        
                    f.write(json.dumps(record) + "\n")

if __name__== "__main__":
    wanjuanqa("/home/pika/Dataset/sft/wanjuan/part-003756-a894b46e.jsonl")    
