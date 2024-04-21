import json
import os

def merge(path):
    files = sorted(os.listdir(path))
    files = list(filter(lambda file: '.json' in file, files))
    data = []
    for file in files:
        major = file.split("_")[0]
        k = f"{major}_directory"
        input_path = os.path.join(path,file)
        print(input_path)
        with open(input_path,"r") as f:
            item = json.load(f)[k]
            data.extend(item)
    data_dict = dict()
    data_dict["directory"] = data
    with open(os.path.join(path,"all.json"), "w") as json_file:
        json.dump(data_dict, json_file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))
    merge(path)