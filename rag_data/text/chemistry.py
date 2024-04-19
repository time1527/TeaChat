import json
import re
from base import Directory


# page:[st,ed]
class CheDirectory(Directory):
    def __init__(self):
        super().__init__("chemistry")
        self.books =[
            "化学必修第一册.pdf",
            "化学必修第二册.pdf",
            "化学选择性必修1化学反应原理.pdf",
            "化学选择性必修2物质结构与性质.pdf",
            "化学选择性必修3有机化学基础.pdf"]
        
        self.offset = []


    def turn_main(self,book_idx):
        """
        第/附录/整理与提升：新页
        实验活动：不保证是
        """
        with open("chemistry/gpt_chemistry_" + str(book_idx) + ".jsonl", 'r', encoding='utf-8') as file:
            jsonl_data = file.readlines()

        mulu = []
        for line in jsonl_data:
            json_obj = json.loads(line.strip())
            mulu.append(json_obj)

        post_mulu = []
        for idx,ob in enumerate(mulu):
            k = list(ob.keys())[0]
            v = int(list(ob.values())[0])
            if len(k) >= 3 and k[2] == "章":continue
            if k == "整理与提升":continue

            if idx >= len(mulu)-1:break
            nidx = idx + 1
            nv = int(list(mulu[nidx].values())[0])
            nk = list(mulu[nidx].keys())[0]
            if nk[0] == "第" or nk[0:2] == "附录" \
                or (len(nk) >= 5 and nk[0:5] == "整理与提升"):
                nv -= 1
            
            if nv < v:nv = v

            pattern = r'^第.+?节\s*'
            match = re.match(pattern, k)
            if match:k = k[match.end():].strip()

            k = k.replace('实验活动', '')
            k = k.replace('名词索引', '')
            k = k.replace('附录', '')
            
            k = re.sub(r'[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ]', '', k)
            k = re.sub(r'^\s*\d+\s*', '', k)

            kl = k.split(" ")
            if len(kl) > 1:
                for klob in kl:
                    post_mulu.append({klob:{"st":v,"ed":nv,"book":self.books[book_idx-1]}})
            else:
                post_mulu.append({k:{"st":v,"ed":nv,"book":self.books[book_idx-1]}})
        return post_mulu
    

    def turn_other(self,book_idx):
        with open("chemistry/gpt_chemistry_" + str(book_idx) + "_append.jsonl", 'r', encoding='utf-8') as file:
            jsonl_data = file.readlines()

        mulu = []
        for line in jsonl_data:
            json_obj = json.loads(line.strip())
            mulu.append(json_obj)

        post_mulu = []
        for idx,ob in enumerate(mulu):
            k = list(ob.keys())[0]
            k = k.replace(' ', '')
            v = int(list(ob.values())[0])
            nv = v + 1
            post_mulu.append({k:{"st":v,"ed":nv,"book":self.books[book_idx-1]}})
        return post_mulu


    def turn(self):
        for i in range(len(self.books)):
            self.dire.extend(self.turn_main(i+1))
            self.dire.extend(self.turn_other(i+1))
        

    def pipeline(self):
        self.turn()
        self.dedup()
        self.save()
        return self.dire
    

if __name__ == "__main__":
    che_dir = CheDirectory()
    che_res = che_dir.pipeline()