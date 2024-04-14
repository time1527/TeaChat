import csv
import json
import jsonlines
import os


# PREFIX = "/root/download/opencompass/data"
PREFIX = "/home/pika/Dataset/opencompass/data"

def find_files_with_extension_and_prefix(folder_path, extension, prefix=None):
    matching_files = []
    # 遍历文件夹
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            # 检查文件扩展名是否与指定扩展名匹配
            if file_name.endswith('.' + extension):
                # 如果指定了前缀，则检查文件名是否以指定前缀开头
                if prefix is not None:
                    if file_name.startswith(prefix):
                        file_path = os.path.join(root, file_name)
                        matching_files.append(file_path)
                else:
                    file_path = os.path.join(root, file_name)
                    matching_files.append(file_path)
    return matching_files


def write_to_jsonl(data,output_file):
    print(f"There are {len(data)} items in data.")
    with jsonlines.open(os.path.join(PREFIX,output_file), 'w') as writer:
        writer.write_all(data)
    print(f"data have been written to {output_file}.")


def generate_gaokao_bench():
    dir = os.path.join(PREFIX,"GAOKAO-BENCH")
    gaokao_bench = []
    files = find_files_with_extension_and_prefix(dir,"json")
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            try:
                data = json.load(json_file)['example']
                # 对 JSON 数据进行处理
                for item in data:
                    gaokao_bench.append({'text':item['question']})
                
            except json.JSONDecodeError as e:
                print("Error decoding JSON file:", file_path)
                print(e)

    write_to_jsonl(gaokao_bench,'gaokao_bench_all.jsonl')


def generate_ceval():
    dir = os.path.join(PREFIX,"ceval")
    ceval = []
    files = find_files_with_extension_and_prefix(dir,"csv","high")
    for file_path in files:
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                item = " ".join([row["question"],
                                "A." + row["A"],
                                "B." + row["B"],
                                "C." + row["C"],
                                "D." + row["D"]])
                ceval.append({"text":item})
    write_to_jsonl(ceval,"ceval_high_school_all.jsonl")


def generate_cmmlu():
    dir = os.path.join(PREFIX,"cmmlu")
    cmmlu = []
    files = find_files_with_extension_and_prefix(os.path.join(dir,"test"),"csv","high")
    files.extend(find_files_with_extension_and_prefix(os.path.join(dir,"dev"),"csv","high"))
    for file_path in files:
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                item = " ".join([row["Question"],
                                "A." + row["A"],
                                "B." + row["B"],
                                "C." + row["C"],
                                "D." + row["D"]])
                cmmlu.append({"text":item})
    write_to_jsonl(cmmlu,"cmmlu_high_school_all.jsonl")


def generate_agieval():
    def is_valid_key(ddict,key):
        if key not in ddict.keys():return False
        if ddict[key] == None:return False
        if len(ddict[key]) == 0:return False
        return True
    
    dir = os.path.join(PREFIX,"AGIEval/data/v1")
    agieval = []
    files = find_files_with_extension_and_prefix(dir,"jsonl","gaokao")
    for file_path in files:
        with jsonlines.open(file_path) as reader:
            for item in reader:
                text = ""
                if is_valid_key(item,"passage"):text += item["passage"]
                if is_valid_key(item,"question"):text += item["question"]
                if is_valid_key(item,"options"):text += "".join(item["options"])

                agieval.append({'text':text})

    write_to_jsonl(agieval,"agieval_high_school_all.jsonl")


if __name__ == "__main__":
    prefix = ""
    generate_gaokao_bench()
    generate_ceval()
    generate_cmmlu()
    generate_agieval()