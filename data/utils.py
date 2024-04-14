import jieba
import re
import string
import os
import shutil
import logging

def get_files(path):
    """查找目录下的所有jsonl文件"""
    files = sorted(os.listdir(path))
    files = list(filter(lambda file: '.jsonl' in file, files))
    return files


def split_word(s):
    """分词"""
    regex = re.compile("，|。|？|！")
    s = s.lower()
    s = s.translate(str.maketrans("", "", string.punctuation))
    s = re.sub(r"\s+", " ", s.strip())
    ss = [w for w in jieba.lcut(re.sub(regex, '', s)) if w.strip()]
    return  ss# list(map(lambda x: "".join(x), ngrams(split, width)))


def rm_if_exists(path):
    """删除目录"""
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
    except NotADirectoryError:
        os.remove(path)