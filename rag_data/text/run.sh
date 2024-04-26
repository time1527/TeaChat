#!/bin/bash

# 获取当前目录
# current_dir=$(pwd)
current_dir=$(dirname "$0")

# 遍历当前目录中的所有文件
for filename in "$current_dir"/*.py; do
    # 获取文件名（不包括路径）
    base=$(basename "$filename")
    
    # 检查文件是否是base.py或all.py，如果是，则跳过
    if [ "$base" = "base.py" ]; then
        continue
    fi
    
    # 在shell中运行.py文件
    python "$filename"
done