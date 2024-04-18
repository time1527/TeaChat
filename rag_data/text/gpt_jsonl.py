import json
import re
import sys

class Directory:
    def __init__(self,major):
        self.major = major
        self.dire = []


    def turn(self):
        raise NotImplementedError("Subclass must implement abstract method")
    

    def dedup(self):
        final = []
        key_set = set()
        for ob in self.dire:
            k = list(ob.keys())[0]
            # print(k)
            if len(k) == 0:continue
            if k in key_set:
                print(ob)
                continue
            key_set.add(k)
            final.append(ob)
        print(f"dedup from {len(self.dire)} to {len(final)}.")
        self.dire = final.copy()
    

    def save(self):
        file_path = self.major + "_directory.json"
        with open(file_path, "w") as json_file:
            json.dump(self.dire, json_file, ensure_ascii=False, indent=4)
    
    def pipeline(self):
        raise NotImplementedError("Subclass must implement abstract method")


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
            nv = int(list(mulu[idx+1].values())[0])
            if list(mulu[idx+1].keys())[0][0] == "第" \
                or list(mulu[idx+1].keys())[0][0:2] == "附录":
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


class BioDirectory(Directory):
    def __init__(self):
        super().__init__("biology")
        self.books =[
            "生物学必修1分子与细胞.pdf",
            "生物学必修2遗传与进化.pdf",
            "生物学选择性必修1稳态与调节.pdf",
            "生物学选择性必修2生物与环境.pdf",
            "生物学选择性必修3生物技术与工程.pdf",]

    def turn_main(self,book_idx):
        with open("biology/gpt_biology_" + str(book_idx) + ".jsonl", 'r', encoding='utf-8') as file:
            jsonl_data = file.readlines()

        mulu = []
        for line in jsonl_data:
            json_obj = json.loads(line.strip())
            mulu.append(json_obj)

        post_mulu = []
        inlist = ['探究・实践','探究·实践',
                  '科学・技术・社会','科学·技术·社会',
                  '生物科技进展',
                  '生物科学史话',
                  '与生物学有关的职业',
                  '科学家的故事',
                  '拓展视野'
                  ]
        def check(text):
            for ins in inlist:
                if ins in text:
                    return True
                
        for idx,ob in enumerate(mulu):
            k = list(ob.keys())[0]
            v = int(list(ob.values())[0])
            if len(k) >= 3 and k[2] == "章":continue

            if idx >= len(mulu) - 1:break
            """
            {"第 1 节 植物细胞工程": 34}
            {"植物细胞工程的基本技术": 34}
            {"探究・实践菊花的组织培养": 35}
            {"植物细胞工程的应用": 39}
            {"第 2 节 动物细胞工程": 43}
            """
            if not check(k) and k[0] != "第":
                """
                {"植物细胞工程的基本技术": 34} 
                -> {"植物细胞工程的应用": 39} 
                -> {"第 2 节 动物细胞工程": 43}
                """
                nidx = idx + 1
                while nidx < len(mulu)-1 and check(list(mulu[nidx].keys())[0]):
                    nidx += 1
                nv = int(list(mulu[nidx].values())[0])
                if list(mulu[nidx].keys())[0][0] == "第":
                    nv -= 1
                if nv < v:nv = v
            elif not check(k) and k[0] == "第":
                """
                {"第 1 节 植物细胞工程": 34} 
                -> {"第 2 节 动物细胞工程": 43}
                """
                nidx = idx + 1
                while nidx < len(mulu)-1 \
                    and list(mulu[nidx].keys())[0][0] != "第" \
                    and "附录" not in list(mulu[nidx].keys())[0]:
                    nidx += 1
                nv = int(list(mulu[nidx].values())[0]) -1
                if nv < v:nv = v
            elif check(k):
                """
                {"探究・实践菊花的组织培养": 35}
                -> {"植物细胞工程的应用": 39}
                """
                nv = int(list(mulu[idx+1].values())[0])
                if list(mulu[idx+1].keys())[0][0] == "第":
                    nv -= 1
                if nv < v:nv = v + 1

            pattern = r'^第.+?节\s*'
            match = re.match(pattern, k)
            if match:k = k[match.end():].strip()

            k = re.sub(r'\d+', '', k)
            k = k.replace('科技探索之路', '')

            k = k.replace('探究・实践', '')
            k = k.replace('探究·实践', '')
            k = k.replace('生物科技进展', '')
            k = k.replace('生物科学史话', '')
            k = k.replace('科学・技术・社会', '')
            k = k.replace('科学·技术·社会', '')
            k = k.replace('与生物学有关的职业', '')
            k = k.replace('拓展视野', '')
            k = k.replace('科学家的故事', '')

            k = k.replace('附录', '')
            k = k.replace(' ', '')

            post_mulu.append({k:{"st":v,"ed":nv,"book":self.books[book_idx-1]}})
        return post_mulu

    def turn(self):
        for i in range(len(self.books)):
            self.dire.extend(self.turn_main(i+1))
        

    def pipeline(self):
        self.turn()
        self.save()
        return self.dire
    

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

    def turn_main(self,book_idx):
        with open("history/gpt_history_" + str(book_idx) + ".jsonl", 'r', encoding='utf-8') as file:
            jsonl_data = file.readlines()

        mulu = []
        for line in jsonl_data:
            json_obj = json.loads(line.strip())
            mulu.append(json_obj)

        def check(text):
            pattern = r'^第.+?单元\s*'
            return re.match(pattern, text) is not None
        
        post_mulu = []
        for idx,ob in enumerate(mulu):
            k = list(ob.keys())[0]
            v = int(list(ob.values())[0])
            if check(k):continue
            if idx >= len(mulu) - 1:break
            nv = int(list(mulu[idx+1].values())[0])
            nk = list(mulu[idx+1].keys())[0]
            if nk[0] == "第" or nk[0:2] == "附录" or nk[0:3] == "活动课":
                nv -= 1
            if nv <= v:nv = v + 1

            pattern = r'^第.+?课\s*'
            match = re.match(pattern, k)
            if match:k = k[match.end():].strip()

            k = k.replace('活动课', '')
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
    che_dir = CheDirectory()
    che_res = che_dir.pipeline()

    bio_dir = BioDirectory()
    bio_res = bio_dir.pipeline()

    his_dir = HisDirectory()
    his_res = his_dir.pipeline()
    
