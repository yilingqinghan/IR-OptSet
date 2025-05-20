## IR-OptSet Quick Start Guide

### Project Overview

**IR-OptSet** is a toolchain designed to automate the construction, filtering, analysis, and creation of LLVM IR datasets. Its core functionalities include:

* Building and configuring the LLVM & Alive2 environments
* Extracting and preprocessing LLVM IR before and after optimization
* Generating datasets in the Hugging Face format
* Verifying IR correctness and analyzing optimization passes
* Performing static performance analysis using `llvm-mca`
* Merging and inspecting datasets

> We recommend using Docker to quickly verify the environment. You can do so with the following commands:
>
> ```shell
> docker pull ghcr.io/yilingqinghan/llvm-alive2:fulllinux
> docker run -it ghcr.io/yilingqinghan/llvm-alive2:fulllinux
> ```
>
> This allows you to skip the complex LLVM and Alive2 setup and jump straight to the \[🔨 Dataset Generation Process]\(🔨 Dataset Generation Process).

---

### 🔧 Prerequisites

* **CMake**, **Ninja**, **Git**, **Python 3.8+**
* It is recommended to use **conda** for managing the Python environment
* Approximately **5 GB** of disk space is required for building the base environment

---

### 🚀 Installation Steps (Approx. 10–30 minutes)

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yilingqinghan/IR-OptSet.git
   cd IR-OptSet
   ```

2. **Build LLVM**

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

3. **Build Alive2**

   ```bash
   cd ../../alive2
   git checkout v19.0
   mkdir build && cd build
   cmake -DLLVM_DIR=../../llvm-project/build/ ..
   make
   ```

4. **Configure Python Environment**

   ```bash
   conda create -n ir-optset python=3.10 -y
   conda activate ir-optset
   pip install -r requirements.txt
   ```

5. **Set Tool Paths**
   Edit `IRDS/config/settings.yaml` and provide paths to LLVM/Alive2 executables:

   Example:

   ```yaml
   clang: /path/to/llvm-project/build/bin/clang
   clangpp: /path/to/llvm-project/build/bin/clang++
   opt: /path/to/llvm-project/build/bin/opt
   llc: /path/to/llvm-project/build/bin/llc
   alive2: /path/to/alive2/build/alive-tv
   ```

---

### 🔨 Dataset Generation Process

First, set the project directory: `export DIR=$(pwd)`

1. **Generate IR Data**
   Test files are provided in the `test` folder for quick evaluation:

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

   **Output Directory Descriptions**:

   * **UNOPT**: Unoptimized IR (.ll)
   * **EX**: Function-extracted IR
   * **OPT**: Optimized IR
   * **LOG**: Optimization logs
   * **PRE\_EX**: Preprocessed IR (before)
   * **PRE\_OPT**: Preprocessed IR (after)

2. **Build the Dataset**

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

   * **filters**: Preliminary filters (e.g., `func_body_changed`, `token_limit_v3`)
   * **vfilters**: Validation filters (e.g., `keep_core`, `dedupe_content`)
   * **prompt-template**: Defines the input format for models

---

### 🔍 Additional Toolchain Overview

| Script               | Description                                      |
| -------------------- | ------------------------------------------------ |
| `alive2.py`          | Automated equivalence checking using Alive2      |
| `analyze_changed.py` | Extract and count effective optimization passes  |
| `dataset_info.py`    | View dataset statistics and examples             |
| `mca_cycles.py`      | Static performance analysis (`llc` + `llvm-mca`) |
| `merge_dataset.py`   | Merge multiple dataset samples                   |
| `opt_verify.py`      | Batch syntax verification of IR                  |

---

#### Usage: `mca_cycles.py`

```bash
cd $DIR/IRDS/tools
python mca_cycles.py $DIR/test/tmp/PRE_OPT/ --suffix ".ll"
```

This will print an **OptVerifier Summary** table showing average cycle counts, success, and failure counts. Additional options include:

* `--csv 1.csv`: Output statistics to CSV
* `--dispatch-width`: Set CPU dispatch width (default: 6)
* `--metric`: Default is `cycle`; you can also use `rthroughput`

> Full example:
>
> ```shell
> python mca_cycles.py $DIR/test/tmp/PRE_OPT/ --suffix ".ll" --dispatch-width 1 --mcpu znver5 --metric rthroughput
> ```

#### Usage: `analyze_changed.py`

```shell
cd $DIR/IRDS/tools
python analyze_changed.py --input $DIR/test/tmp/LOG --csv tmp
```

This prints an analysis of optimization passes, including attempted and effective ones.

* Add `--sample <number>` and `--seed <number>` to randomly sample files; by default, all `.log` files are analyzed.

#### Usage: `opt_verify.py`

```shell
python opt_verify.py --folder $DIR/test/tmp/FINAL/ --log-errors --log-dir "./logs" --clean --suffix ".ll"
```

This prints a table showing how many files passed `opt` syntax checks. Expect a 100% pass rate here.

#### Usage: `alive2.py`

```shell
cd $DIR/IRDS/tools
python alive2.py --input-dir $DIR/test/alive --suffix ".model.predict.ll" --output-dir ./tmp
```

If Alive2 verification fails, it prints detailed errors. Final summary includes counts of passed and failed cases, saved in a CSV (SMT solving may take time).

#### Usage: `dataset_info.py`

```shell
cd $DIR/IRDS/tools
python dataset_info.py --root-path $DIR/test/tmp/dataset --preview --split test --num-samples 1 --full-preview --draw-hist
```

This command provides a clear, visual summary of a test dataset and statistics such as token count distributions (max, min, median, mean, etc.).

---

### 📄 License

Licensed under the MIT License. See the LICENSE file for details.