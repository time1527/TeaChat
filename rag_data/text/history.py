import json
import re
from base import Directory


# page:[st,ed]
class HisDirectory(Directory):
    def __init__(self):
        super().__init__("history")
        self.books =[
            "历史必修中外历史纲要（上）.pdf",
            "历史必修中外历史纲要（下）.pdf",
            "历史选择性必修1国家制度与社会治理.pdf",
            "历史选择性必修2经济与社会生活.pdf",
            "历史选择性必修3文化交流与传播.pdf",
            ]
        self.offsets = [6,6,4,4,4]


    def turn_main(self,book_idx):
        """
        第/附录/活动课：新页
        """
        offset = self.offsets[book_idx-1]


        with open("history/gpt_history_" + str(book_idx) + ".jsonl", 'r', encoding='utf-8') as file:
            jsonl_data = file.readlines()

        mulu = []
        for line in jsonl_data:
            json_obj = json.loads(line.strip())
            mulu.append(json_obj)

        def check_unit(text):
            pattern = r'^第.+?单元\s*'
            return re.match(pattern, text) is not None
        
        post_mulu = []
        for idx,ob in enumerate(mulu):
            k = list(ob.keys())[0]
            v = int(list(ob.values())[0])
            if check_unit(k):continue
            if idx >= len(mulu) - 1:break
            if len(k) >= 3 and k[0:3] == "活动课":continue
            nidx = idx + 1
            nv = int(list(mulu[nidx].values())[0])
            nk = list(mulu[nidx].keys())[0]
            if nk[0] == "第" or nk[0:2] == "附录" or nk[0:3] == "活动课":
                nv -= 1
            if nv < v:nv = v

            pattern = r'^第.+?课\s*'
            match = re.match(pattern, k)
            if match:k = k[match.end():].strip()

            k = k.replace('活动课', '')
            k = k.replace(' ', '')

            post_mulu.append({k:{"st":v+offset,"ed":nv+offset,"book":self.books[book_idx-1]}})
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
    his_dir = HisDirectory()
    his_res = his_dir.pipeline()