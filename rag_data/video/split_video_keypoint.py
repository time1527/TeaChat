import os
import re
import json

file_name = 'chemistry_video_urls'
file_path = f'{file_name}.json'

with open(file_path, 'r') as file:
    data = json.load(file)

for item in data[file_name]:
    right_bracket_index = item['name'].rfind('】')
    left_bracket_index = item['name'].find('（')
    if right_bracket_index != -1 and left_bracket_index != -1:
        item['description'] = item['name'][:right_bracket_index+1] + item['name'][left_bracket_index:]
        item['name'] = item['name'][right_bracket_index+1:left_bracket_index]
    elif right_bracket_index != -1:
        item['description'] = item['name'][:right_bracket_index+1]
        item['name'] = item['name'][right_bracket_index+1:]
    elif left_bracket_index != -1:
        item['description'] = item['name'][left_bracket_index:]
        item['name'] = item['name'][:left_bracket_index]
    else:
        item['description'] = ''
        item['name'] = item['name']
    
    # item['name'] = re.sub(r'^\d+\s*', '', item['name'])

    item['name'] = re.sub(r'^[\d\-]+\s*', '', item['name'])

    item['name'] = re.sub(r'^第[一二三四五六七八九十]+章\s*', '', item['name'])

    item['author'] = "一化儿"

    item['uid'] = "1526560679"

    item['major'] = "化学"

with open(file_path, 'w') as file:
    json.dump(data, file, indent=4, ensure_ascii=False)
