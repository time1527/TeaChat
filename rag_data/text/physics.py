import json
import re
from base import Directory


# page:[st,ed]
class PhyDirectory(Directory):
    def __init__(self):
        super().__init__("physics")
        self.books =[
            "物理必修第一册.pdf",
            "物理必修第二册.pdf",
            "物理必修第三册.pdf",
            "物理选择性必修第一册.pdf",
            "物理选择性必修第二册.pdf",
            "物理选择性必修第三册.pdf"]


    def turn_main(self,book_idx):
        """
        ：新页
        """
        with open("physics/gpt_physics_" + str(book_idx) + ".jsonl", 'r', encoding='utf-8') as file:
            jsonl_data = file.readlines()

        mulu = []
        for line in jsonl_data:
            json_obj = json.loads(line.strip())
            mulu.append(json_obj)

        def check_chap(text):
            pattern = r'^第.+?章\s*'
            return re.match(pattern, text) is not None
        
        post_mulu = []
        for idx,ob in enumerate(mulu):
            k = list(ob.keys())[0]
            v = int(list(ob.values())[0])
            if check_chap(k):continue
            if k in ["课题研究","索引","学生实验"]:continue
            if idx >= len(mulu) - 1:break
            
            nidx = idx + 1
            nv = int(list(mulu[nidx].values())[0])
            nk = list(mulu[nidx].keys())[0]
            nv -= 1
            if nv < v:nv = v
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
    phy_dir = PhyDirectory()
    phy_res = phy_dir.pipeline()