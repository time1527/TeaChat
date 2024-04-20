import json
import re
from base import Directory


# page:[st,ed]
class GeoDirectory(Directory):
    def __init__(self):
        super().__init__("geography")
        self.books =[
            "地理必修第一册.pdf",
            "地理必修第二册.pdf",
            "地理选择性必修1自然地理基础.pdf",
            "地理选择性必修2区域发展.pdf",
            "地理选择性必修3资源、环境与国家安全.pdf",
            ]


    def turn_main(self,book_idx):
        """
        第/附录/问题探究：新页
        每章起始页码=第一节页码
        """
        with open("geography/gpt_geography_" + str(book_idx) + ".jsonl", 'r', encoding='utf-8') as file:
            jsonl_data = file.readlines()

        mulu = []
        for line in jsonl_data:
            json_obj = json.loads(line.strip())
            mulu.append(json_obj)

        def check_chap(text):
            pattern = r'^第.+?章\s*'
            return re.match(pattern, text) is not None
        
        def check_appendix(text):
            if len(text) >= 2 and text[0:2] == "附录":
                return True
            else:
                return False
        
        def check_wtyj(text):
            if len(text) >= 4 and text[0:4] == "问题研究":
                return True
            else:
                return False
            
        post_mulu = []
        for idx,ob in enumerate(mulu):
            k = ob["content"]
            v = int(ob["page"])
            if check_chap(k) or check_wtyj(k) or check_appendix(k):continue

            if idx >= len(mulu) - 1:break
            nidx = idx + 1
            nv = int(mulu[nidx]["page"])- 1
            nk = mulu[nidx]["content"]
            if nv < v:nv = v

            pattern = r'^第.+?节\s*'
            match = re.match(pattern, k)
            if match:k = k[match.end():].strip()

            k = k.replace(' ', '')

            post_mulu.append({k:{"st":v,"ed":nv,"book":self.books[book_idx-1]}})
        return post_mulu


    def turn(self):
        for i in range(len(self.books)):
            self.dire.extend(self.turn_main(i+1))
        

    def pipeline(self):
        self.turn()
        self.dedup()
        self.save()
        return self.dire
    

if __name__ == "__main__":
    geo_dir = GeoDirectory()
    geo_res = geo_dir.pipeline()