import json

MAJORMAP = {
    "chemistry":"化学",
    "biology":"生物学",
    "geography":"地理",
    "history":"历史",
    "maths":"数学",
    "physics":"物理",
    "politics":"思想政治",
}
# page:[st,ed]
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
    
    def _format(self):
        for i,ob in enumerate(self.dire):
            record = dict()
            record["name"] = list(ob.keys())[0]
            record["info"] = list(ob.values())[0]
            record["info"]["major"] = MAJORMAP[self.major]
            self.dire[i] = record

    def save(self):
        self._format()
        file_path = self.major + "_directory.json"
        item = dict()
        item[f"{self.major}_directory"] = self.dire
        with open(file_path, "w") as json_file:
            json.dump(item, json_file, ensure_ascii=False, indent=4)
    
    def pipeline(self):
        raise NotImplementedError("Subclass must implement abstract method")