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

    for item_dict in items_dict['data']['View']['pages']:
        new_item_dict = {}
        new_item_dict['url'] = f'{base_url}?p={item_dict["page"]}'
        new_item_dict['name'] = item_dict['part']
        
        yield new_item_dict

def write_item_to_json(item):
    # with open("chemistry_video_urls.json", 'a') as f:
    #     f.writelines((',\n' if item['url'].split('=')[-1] != '1' else '')  + json.dumps(item, ensure_ascii=False))
    
    with open("chemistry_video_urls.jsonl", 'a') as f:
        f.writelines(json.dumps(item, ensure_ascii=False) + '\n')

if __name__ == '__main__':
    base_url = 'https://www.bilibili.com/video/BV1Qi4y1R7tW'
    list_api_url = 'https://api.bilibili.com/x/web-interface/wbi/view/detail?aid=550216398&need_view=1&isGaiaAvoided=false&web_location=1315873&w_rid=50034e487e64ce33b2d8b6ded3a8151e&wts=1713271692'
    
    list_json = request_url(list_api_url)

    # with open("chemistry_video_urls.json", 'w') as f:
    #     f.writelines('{"chemistry_video_urls":[\n')
    
    items = parse_json(base_url, list_json)
    for item in items:
        write_item_to_json(item)
    
    # with open("chemistry_video_urls.json", 'a') as f:
    #     f.writelines('\n]}\n')