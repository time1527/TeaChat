import json
import re
from base import Directory


class BioDirectory(Directory):
    def __init__(self):
        super().__init__("biology")
        self.books =[
            "生物学必修1分子与细胞.pdf",
            "生物学必修2遗传与进化.pdf",
            "生物学选择性必修1稳态与调节.pdf",
            "生物学选择性必修2生物与环境.pdf",
            "生物学选择性必修3生物技术与工程.pdf",]

        self.offsets = [8,8,8,8,8]


    def turn_main(self,book_idx):
        """
        第/附录：新页
        """
        offset = self.offsets[book_idx-1]


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
        def check_in(text):
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

            有三类：
            1.第x节/附录/END
            2.属于inlist
            3.节内的某标题
            """
            # 1.节内的某个标题：找到非inlist的任意一个
            if not check_in(k) and not (k[0] == "第" or k[0:2] == "附录" or k == "END"):
                """
                {"植物细胞工程的基本技术": 34} 
                -> {"植物细胞工程的应用": 39} 
                -> {"第 2 节 动物细胞工程": 43}
                """
                nidx = idx + 1
                while nidx < len(mulu)-1 and check_in(list(mulu[nidx].keys())[0]):
                    nidx += 1
                nv = int(list(mulu[nidx].values())[0])
                if list(mulu[nidx].keys())[0][0] == "第" \
                    or list(mulu[nidx].keys())[0][0:2] == "附录":
                    nv -= 1
            # 2.第x节：找到下一节/附录/END
            elif not check_in(k) and (k[0] == "第" or k[0:2] == "附录" or k == "END"):
                """
                {"第 1 节 植物细胞工程": 34} 
                -> {"第 2 节 动物细胞工程": 43}
                """
                nidx = idx + 1
                while nidx < len(mulu)-1 \
                    and list(mulu[nidx].keys())[0][0] != "第" \
                    and "附录" not in list(mulu[nidx].keys())[0] \
                    and list(mulu[nidx].keys())[0] != "END":
                    nidx += 1
                nv = int(list(mulu[nidx].values())[0])
                if list(mulu[nidx].keys())[0][0] == "第" \
                    or list(mulu[nidx].keys())[0][0:2] == "附录":
                    nv -= 1
            # 3.inlist的内容：任意下一个都可
            elif check_in(k):
                """
                {"探究・实践菊花的组织培养": 35}
                -> {"植物细胞工程的应用": 39}
                """
                nidx = idx + 1
                nv = int(list(mulu[nidx].values())[0])
                if list(mulu[nidx].keys())[0][0] == "第" \
                    or list(mulu[nidx].keys())[0][0:2] == "附录":
                    nv -= 1
            # 4.看看是否落下了哪个
            else:
                print(k)

            if nv < v:nv = v
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

            post_mulu.append({k:{"st":v+offset,"ed":nv+offset,"book":self.books[book_idx-1]}})
        return post_mulu


    def turn(self):
        for i in range(len(self.books)):
            self.dire.extend(self.turn_main(i+1))
        

    def pipeline(self):
        self.turn()
        self.save()
        return self.dire


if __name__ == "__main__":
    bio_dir = BioDirectory()
    bio_res = bio_dir.pipeline()