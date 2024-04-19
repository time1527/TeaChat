import json

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
    

    def save(self):
        file_path = self.major + "_directory.json"
        with open(file_path, "w") as json_file:
            json.dump(self.dire, json_file, ensure_ascii=False, indent=4)
    
    def pipeline(self):
        raise NotImplementedError("Subclass must implement abstract method")