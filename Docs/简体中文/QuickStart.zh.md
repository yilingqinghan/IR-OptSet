## IR-OptSet  快速入门

### 项目简介

**IR-OptSet** 是一个用于自动化构建、过滤和分析和制作 LLVM IR 数据集的工具链，主要功能：

- 构建并配置 LLVM & Alive2 环境
- 提取并预处理优化前后 LLVM IR
- 生成 Hugging Face 格式的数据集
- 校验 IR 正确性并分析优化 Pass
- 使用 `llvm-mca` 进行静态性能分析
- 合并与检查数据集

>建议您使用docker快速验证我们的环境，可以直接使用如下命令：
>
>```shell
>docker pull ghcr.io/yilingqinghan/llvm-alive2:fulllinux
>docker run -it ghcr.io/yilingqinghan/llvm-alive2:fulllinux
>```
>
>然后您会进入`/workspace`目录，在此目录内，请clone我的仓库。
>
>```shell
>unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY FTP_PROXY
>git clone https://github.com/yilingqinghan/IR-OptSet.git
>cd IR-OptSet
>```
>
>> 如果克隆失败，请使用 https://gitlab.com/759569457/IR-OptSet.git
> 
>如此条件下，您可以避免构建复杂的LLVM和Alive2环境，直接跳至[🔨 数据集生成流程](🔨 数据集生成流程)

### 🔧 先决条件

- **CMake**、**Ninja**、**Git**、**Python 3.8+**
- 建议使用 **conda** 管理 Python 环境
- ≈**10GB** 磁盘空间用于基础环境构建

------

### 🚀 安装步骤(约10~30分钟)

1. **克隆仓库**

   ```bash
   git clone https://github.com/yilingqinghan/IR-OptSet.git
   cd IR-OptSet
   ```

2. **构建 LLVM**

   ```bash
   git clone https://github.com/llvm/llvm-project.git
   cd llvm-project
   git checkout llvmorg-19.1.0
   mkdir build && cd build
   cmake -G Ninja \
       -DCMAKE_BUILD_TYPE=Release \
       -DLLVM_ENABLE_PROJECTS="clang;lld" \
       -DLLVM_ENABLE_RTTI=ON \
       -DLLVM_ENABLE_EH=ON \
       -DLLVM_INCLUDE_TESTS=OFF \
       -DLLVM_INCLUDE_EXAMPLES=OFF \
       -DLLVM_INCLUDE_BENCHMARKS=OFF \
       ../llvm
   ninja -j$(nproc)
   ```

3. **构建 Alive2**

   ```bash
   cd ../../alive2
   git checkout v19.0
   mkdir build && cd build
   cmake -DLLVM_DIR=../../llvm-project/build/ ..
   make
   ```

4. **配置 Python 环境**

   ```bash
   conda create -n ir-optset python=3.10 -y
   conda activate ir-optset
   pip install -r requirements.txt
   ```

5. **设置工具路径**
    修改 `IRDS/config/settings.yaml` ，并填写 LLVM/Alive2 可执行文件路径：

   例如：

   ```yaml
   clang: /path/to/llvm-project/build/bin/clang
   clangpp: /path/to/llvm-project/build/bin/clang++
   opt: /path/to/llvm-project/build/bin/opt
   llc: /path/to/llvm-project/build/bin/llc
   alive2: /path/to/alive2/build/alive-tv
   ```

------

### 🔨 数据集生成流程

​	数据集的生成流程按照前端后端的方式依次进行。

请先设置项目目录:

```shell
export DIR=$(pwd)
```

1. **生成 IR 数据**

   test文件夹里提供了一些测试文件，以供直接测试使用：

   ```bash
   cd $DIR/IRDS
   export PYTHONPATH=$(pwd):$PYTHONPATH
   python cli-frontend.py pipeline \
     --source-dir ../test/cfiles \
     --ext .c \
     --clang-flags "-S -emit-llvm -O3 -Xclang -disable-llvm-passes" \
     --compile-out ../test/tmp/UNOPT \
     --extract-dir ../test/tmp/EX \
     --opt-out ../test/tmp/OPT \
     --opt-flags "-passes='default<O3>' -S -print-changed -print-before-changed" \
     --sample-size 10 --seed 1 \
     --rules normalize_structs ensure_entry_block remove_blank remove_comments rename_blocks rename_locals \
     --where all \
     --log-out ../test/tmp/LOG \
     --pre-out ../test/tmp/PRE_EX \
     --post-out ../test/tmp/PRE_OPT
   ```

   **输出目录说明**：

   - **UNOPT**: 未优化 IR (.ll)
   - **EX**: 按函数提取 IR
   - **OPT**: 优化后 IR
   - **LOG**: 优化日志
   - **PRE_EX**: 预处理前 IR
   - **PRE_OPT**: 预处理后 IR

2. **构建数据集**

   ```bash
   python cli-backend.py \
     --pre-dir ../test/tmp/PRE_EX \
     --post-dir ../test/tmp/PRE_OPT \
     --log-dir ../test/tmp/LOG \
     --filters func_body_changed token_limit_v3 \
     --vfilters keep_core dedupe_content \
     --out-dir ../test/tmp/FINAL \
     --make-dataset \
     --train-size 5 --test-size 1 --valid-size 1 --seed 1 \
     --prompt-template "[INST]Analyze IR:\n<code>{pre_ir}</code>[/INST]..." \
     --dataset-output ../test/tmp/dataset --token-limit 4096
   ```

   - **filters**: 初筛规则，如 `func_body_changed`（函数体有变化）、`token_limit_v3`（限制 Token 数量）
   - **vfilters**: 后筛规则，如 `keep_core`（保留可编译核心 IR）、`dedupe_content`（去重）
   - **prompt-template**: 定义模型输入格式
   
   至此则已经有了示范的一个数据集，您可以去`$DIR/test/tmp/dataset`查看。

------

### 🔍 其他工具链一览

​	我们同样提供了一些其他辅助工具，无论是用于正确性验证还是自动分析。

| 脚本                 | 功能描述                          |
| -------------------- | --------------------------------- |
| `alive2.py`          | 自动等价性验证（Alive2）          |
| `analyze_changed.py` | 提取并统计生效 Pass 序列          |
| `dataset_info.py`    | 查看数据集统计与样例              |
| `mca_cycles.py`      | 静态性能分析 (`llc` + `llvm-mca`) |
| `merge_dataset.py`   | 合并多数据集样本                  |
| `opt_verify.py`      | 批量验证 IR 语法正确性            |

------

#### 使用方法：mca_cyles.py

```bash
cd $DIR/IRDS/tools
python mca_cycles.py $DIR/test/tmp/PRE_OPT/ --suffix ".ll"
```

​	这样就会打印一个OptVerifier Summary表格：会显示平均周期数和正确和错误数量。还有其他后缀可以选择：

- `--csv 1.csv`：选择输出csv文件，包含具体想要的统计信息
- `--dispatch-width`：一个int，设置处理器调度宽度（默认为6）
- `--metric`：默认是cycle，可选rthroughput

> 整合一下就是
>
> ```shell
> python mca_cycles.py $DIR/test/tmp/PRE_OPT/ --suffix ".ll" --dispatch-width 1 --mcpu znver5 --metric rthroughput
> ```

#### 使用方法：analyze_changed.py

```shell
cd $DIR/IRDS/tools
python analyze_changed.py --input $DIR/test/tmp/LOG --csv tmp
```

​	这样就会打印一个Pass分析，包含Attempted Passes和Effective Passes。

- 如果你添加了`--sample <数字>`和`--seed <数字>`，则会随机挑选给定个文件进行分析，默认情况下是所有.log文件都参与分析

#### 使用方法：opt_verify.py

```shell
python opt_verify.py --folder $DIR/test/tmp/FINAL/ --log-errors --log-dir "./logs" --clean --suffix ".ll"
```

​	这样就会打印一个表格，捕捉指定后缀文件的数量以及通过opt语法测试的数量，在这里应该是100%正确率。

#### 使用方法：alive2.py

```shell
cd $DIR/IRDS/tools
python alive2.py --input-dir $DIR/test/alive --suffix ".model.predict.ll" --output-dir ./tmp
```

​	如果alive2等价性验证失败，则会打印具体错误，同时最终会输出Pass和失败的个数，以及记录到csv文件（请耐心等待，SMT求解器需要时间）。	

#### 使用方法：dataset_info.py

```shell
cd $DIR/IRDS/tools
python dataset_info.py --root-path $DIR/test/tmp/dataset --preview --split test --num-samples 1 --full-preview --draw-hist
```

​	这将列举出dataset的基本信息：优雅得可视化一个test数据集的数据项，并查看数据集的token数量的统计数据（最大、最小、中位数、平均等等）

### 📄 许可协议

MIT 许可证，详见 LICENSE 文件。

