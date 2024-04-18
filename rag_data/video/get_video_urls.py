import json
import requests

def request_url(url):
    headers = {
        "Cookie": "",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
    }
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(e)
        return None

def parse_json(base_url, items_json):
    items_dict = items_json

    # 分节-分集视频
    # 不太好判断写入条目是否是 p1，所以目前 json 文件 p1 前会多一个逗号分隔符
    if items_dict['data']['View'].get('ugc_season') :
        for section in items_dict['data']['View']['ugc_season']['sections']:
            for item_dict in section['episodes'] :
                new_item_dict = {}
                new_item_dict['url'] = f'https://www.bilibili.com/video/{item_dict["bvid"]}'
                new_item_dict['name'] = item_dict['title']
            
                yield new_item_dict
    # 分集视频
    else :
        for item_dict in items_dict['data']['View']['pages']:
            new_item_dict = {}
            new_item_dict['url'] = f'{base_url}?p={item_dict["page"]}'
            new_item_dict['name'] = item_dict['part']
            
            yield new_item_dict


def write_item_to_json(file_name, item):
    with open(f"{file_name}.json", 'a') as f:
        f.writelines((',\n' if item['url'].split('=')[-1] != '1' else '')  + json.dumps(item, ensure_ascii=False))
    
    with open(f"{file_name}.jsonl", 'a') as f:
        f.writelines(json.dumps(item, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    # 化学 chemistry
    # file_name = 'chemistry_video_urls'
    # base_url = 'https://www.bilibili.com/video/BV1Qi4y1R7tW'
    # list_api_url = 'https://api.bilibili.com/x/web-interface/wbi/view/detail?aid=550216398&need_view=1&isGaiaAvoided=false&web_location=1315873&w_rid=50034e487e64ce33b2d8b6ded3a8151e&wts=1713271692'
    
    # 地理 geography
    # file_name = 'geography_video_urls'
    # base_url = 'https://www.bilibili.com/video/BV1RN4y1f7Hn'
    # list_api_url = 'https://api.bilibili.com/x/web-interface/wbi/view/detail?aid=874248249&need_view=1&isGaiaAvoided=false&web_location=1315873&w_rid=8b1ea504906b2f09f808c6186c40298a&wts=1713456325'

    # 数学 mathematic
    # file_name = 'mathematic_video_urls'
    # base_url = 'https://www.bilibili.com/video/BV147411K7xu'
    # list_api_url = 'https://api.bilibili.com/x/web-interface/wbi/view/detail?aid=91849600&need_view=1&isGaiaAvoided=false&web_location=1315873&w_rid=6e9c51559eab40073a8a2f364cf&wts=1713456010'

    # 生物 biologic
    file_name = 'biologic_video_urls'
    base_url = 'https://www.bilibili.com/video/BV1g14y1X7eB'
    list_api_url = 'https://api.bilibili.com/x/web-interface/wbi/view/detail?aid=786321348&need_view=1&isGaiaAvoided=false&web_location=1315873&w_rid=ad1321db71f0bda65acba2dfab43ef7f&wts=1713456432'

    list_json = request_url(list_api_url)

    with open(f"{file_name}.json", 'w') as f:
        f.writelines('{"chemistry_video_urls":[\n')

    with open(f"{file_name}.jsonl", "w") as f:
        f.write("")

    items = parse_json(base_url, list_json)
    for item in items:
        write_item_to_json(file_name, item)

    with open(f"{file_name}.json", 'a') as f:
        f.writelines('\n]}\n')