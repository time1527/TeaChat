1. 整理垂直领域测试集

   ```bash
   cd data/
   # 修改generate_test.py的PREFIX变量为本地评测数据目录
   python generate_test.py
   ```

2. 修改`preprocess.sh`：

   ```bash
   python [prefix_path]/pt_main.py \
       --input_dir [data_prefix_path]/[dataset,eg.minpt]/ \
       --test_dir 同generate_test.py的PREFIX变量 \
       --nf_threshold 5
   
   python [prefix_path]/sft_main.py \
       --input_dir [data_prefix_path]/[dataset,eg.minsft]/ \
       --test_dir 同generate_test.py的PREFIX变量
   ```

3. 修改`pt_main.py`和`sft_main.py `的`ds_names`变量和`ds_cols`变量。其中，`sft_main.py `中的`ds_names`在`MAP.py`中对应了初步筛选数据的方法

4. 数据处理：

   ```bash
   bash preprocess.sh
   ```

   * 数据处理前文件目录：

     ```bash
     # minpt
     .
     ├── qq
     │   └── 2.jsonl
     └── ww
         └── 1.jsonl
     ```

     ```bash
     # minsft
     .
     └── ee
         └── 3.jsonl
     ```

   * 数据处理后文件目录：

     ```bash
     # minpt
     .
     ├── qq
     │   └── 2.jsonl
     ├── ww
     │   └── 1.jsonl
     ├── pt_final
     │   ├── qq
     │   │   └── 2.jsonl
     │   └── ww
     │       └── 1.jsonl
     └── pt_nf
         ├── 2024-04-12 19:15:06exact_remove.jsonl
         ├── 2024-04-12 19:15:06lsh.pickle
         ├── 2024-04-12 19:15:06remove.jsonl
         ├── 2024-04-12 19:15:16fuzzy_remove.jsonl
         ├── qq
         │   └── 2.jsonl
         └── ww
             └── 1.jsonl
     ```

     ```bash
     # minsft
     .
     ├── sft_filter
     │   ├── 2024-04-12 19:15:17exact_remove.jsonl
     │   ├── 2024-04-12 19:15:17lsh.pickle
     │   ├── 2024-04-12 19:15:17remove.jsonl
     │   ├── 2024-04-12 19:15:28fuzzy_remove.jsonl
     │   └── ee
     │       └── 3.jsonl
     ├── sft_final
     │   └── ee
     │       └── 3.jsonl
     └── ee
         └── 3.jsonl
     ```

     

