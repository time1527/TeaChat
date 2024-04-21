import json
import re
from base import Directory


# page:[st,ed]
class PolDirectory(Directory):
    def __init__(self):
        super().__init__("politics")
        self.books =[
            "思想政治必修1中国特色社会主义.pdf",
            "思想政治必修2经济与社会.pdf",
            "思想政治必修3政治与法治.pdf",
            "思想政治必修4哲学与文化.pdf",
            "思想政治选择性必修1当代国际政治与经济.pdf",
            "思想政治选择性必修2法律与生活.pdf",
            "思想政治选择性必修3逻辑与思维.pdf"
            ]
        self.offsets = [4,4,4,4,4,4,4]


    def turn_main(self,book_idx):
        """
        第/综合探究：新页
        """
        offset = self.offsets[book_idx - 1]


        with open("politics/gpt_politics_" + str(book_idx) + ".jsonl", 'r', encoding='utf-8') as file:
            jsonl_data = file.readlines()

        mulu = []
        for line in jsonl_data:
            json_obj = json.loads(line.strip())
            mulu.append(json_obj)

        def check_unit(text):
            pattern = r'^第.+?单元\s*'
            return re.match(pattern, text) is not None

        def check_lesson(text):
            pattern = r'^第.+?课\s*'
            return re.match(pattern, text) is not None
        
        def check_zhtj(text):
            if len(text) >= 4 and text[0:4] == "综合探究":
                return True
            else:
                return False
        
        def check_header(text):
            if check_lesson(text):return False
            elif check_unit(text):return False
            elif check_zhtj(text):return False
            elif text == "END":return False
            else:return True
            
        post_mulu = []
        for idx,ob in enumerate(mulu):
            k = list(ob.keys())[0]
            v = int(list(ob.values())[0])
            if check_unit(k) or check_zhtj(k):continue
            if idx >= len(mulu) - 1:break

            """
            {"第二单元  经济发展与社会进步": 31}
            {"第三课  我国的经济发展": 32}
            {"贯彻新发展理念": 32}
            {"推动高质量发展": 38}
            {"第四课  我国的个人收入分配与社会保障": 44}
            {"我国的个人收入分配": 44}
            {"我国的社会保障": 49}
            {"综合探究  践行社会责任  促进社会进步": 56}

            考虑两类：
            1.第x课
            2.课内的某标题
            """
            # 1. 第x课：找到下一“第”/综合探究/END
            if check_lesson(k):
                nidx = idx + 1
                while nidx < len(mulu) - 1 and check_header(list(mulu[nidx].keys())[0]):
                    nidx += 1
                nv = int(list(mulu[nidx].values())[0]) - 1
                nk = list(mulu[nidx].keys())[0]
            elif not check_lesson(k):
                nidx = idx + 1
                nv = int(list(mulu[nidx].values())[0])
                nk = list(mulu[nidx].keys())[0]
                if check_lesson(nk) or check_unit(nk) or check_zhtj(nk):
                    nv -= 1
            else:
                print(k)
            if nv < v:nv = v

            pattern = r'^第.+?课\s*'
            match = re.match(pattern, k)
            if match:k = k[match.end():].strip()

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
    pol_dir = PolDirectory()
    pol_res = pol_dir.pipeline()
