#!/bin/bash

# 获取当前目录
# current_dir=$(pwd)
current_dir=$(dirname "$0")

# 定义文件路径
file_path="$current_dir/all.json"

# 检查文件是否存在
if [ -f "$file_path" ]; then
    # 如果文件存在，则删除
    rm "$file_path"
    echo "文件 $file_path 已删除。"
else
    # 如果文件不存在，则输出消息
    echo "文件 $file_path 不存在。"
fi


# 遍历当前目录中的所有文件
for filename in "$current_dir"/*.py; do
    # 获取文件名（不包括路径）
    base=$(basename "$filename")
    
    # 检查文件是否是base.py或all.py，如果是，则跳过
    if [ "$base" = "base.py" ] || [ "$base" = "all_in_one.py" ]; then
        continue
    fi
    
    # 在shell中运行.py文件
    python "$filename"
done

python "$current_dir/all_in_one.py"