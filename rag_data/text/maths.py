import json
import re
from base import Directory


# page:[st,ed]
class MatDirectory(Directory):
    def __init__(self):
        super().__init__("maths")
        self.books =[
            "数学必修第一册.pdf",
            "数学必修第二册.pdf",
            "数学选择性必修第一册.pdf",
            "数学选择性必修第二册.pdf",
            "数学选择性必修第三册.pdf",
            ]


    def turn_main(self,book_idx):
        """
        第x章\小结\复习参考题：新页，不考虑
        x.x\数学探究\数学建模:新页，考虑
        探究与发现\阅读与思考\信息技术应用：不一定，考虑
        文献阅读与数学写作：不一定，不考虑
        """
        with open("maths/gpt_maths_" + str(book_idx) + ".jsonl", 'r', encoding='utf-8') as file:
            jsonl_data = file.readlines()

        mulu = []
        for line in jsonl_data:
            json_obj = json.loads(line.strip().replace('\\', '\\\\'),strict=False)
            mulu.append(json_obj)

        def check_chap(text):
            pattern = r'^第.+?章\s*'
            if re.match(pattern, text) is not None:return True
            if len(text) >= 2 and text[0:2] == "小结":return True
            if len(text) >= 5 and text[0:5] == "复习参考题":return True
            if text == "部分中英文词汇索引":return True
            return False
        
        def check_session(text):
            pattern = r'^\d+\.\d+.*'
            if re.match(pattern, text) is not None: return True
            if len(text) >= 4 and text[0:4] == "数学探究":return True
            if len(text) >= 4 and text[0:4] == "数学建模":return True
            return False
        
        def check_in(text):
            in_list = ["探究与发现","阅读与思考","信息技术应用"]
            for inl in in_list:
                if inl in text:return True
            return False
        
        def check_out(text):
            if len(text) >= 9 and text[0:9] == "文献阅读与数学写作":return True
            return False
            
        post_mulu = []
        for idx,ob in enumerate(mulu):
            k = ob["content"]
            v = int(ob["page"])
            if check_chap(k) or check_out(k):continue

            if idx >= len(mulu) - 1:break

            nidx = idx + 1
            if check_session(k):
                while nidx < len(mulu)-1 and \
                    not (check_chap(mulu[nidx]["content"]) or check_session(mulu[nidx]["content"])):
                    nidx += 1
                nv = int(mulu[nidx]["page"])- 1
            elif check_in(k):
                nv = int(mulu[nidx]["page"])
                nk = mulu[nidx]["content"]
                if check_chap(nk) or check_session(nk):
                    nv -= 1
            if nv < v:nv = v

            pattern = r'^\d+\.\d+\s*'
            k = re.sub(pattern, '', k)

            k = k.replace('数学探究', '')
            k = k.replace('数学建模', '')
            k = k.replace('探究与发现', '')
            k = k.replace('阅读与思考', '')
            k = k.replace('信息技术应用', '')
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
    mat_dir = MatDirectory()
    mat_res = mat_dir.pipeline()