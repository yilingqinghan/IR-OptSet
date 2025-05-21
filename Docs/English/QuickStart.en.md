## IR-OptSet Quick Start Guide

### Project Overview

**IR-OptSet** is a toolchain for automatically constructing, filtering, analyzing, and generating LLVM IR datasets. Its key features include:

* Setting up and configuring LLVM & Alive2 environments
* Extracting and preprocessing pre-/post-optimization LLVM IR
* Generating datasets in the Hugging Face format
* Validating IR correctness and analyzing optimization passes
* Performing static performance analysis via `llvm-mca`
* Merging and inspecting datasets

> 🚀 **Recommended**: Use Docker to quickly try out our environment with the following commands:
>
> ```shell
> docker pull ghcr.io/yilingqinghan/llvm-alive2:fulllinux
> docker run -it ghcr.io/yilingqinghan/llvm-alive2:fulllinux
> ```
>
> This will place you in the `/workspace` directory. From there, clone the repository:
>
> ```shell
> git clone https://github.com/yilingqinghan/IR-OptSet.git
> cd IR-OptSet
> ```
>
> With this setup, you can skip the manual LLVM and Alive2 build process and jump directly to the [🔨 Dataset Generation Workflow](#-dataset-generation-workflow).

### 🔧 Prerequisites

* **CMake**, **Ninja**, **Git**, **Python 3.8+**
* Using **conda** to manage Python environments is recommended
* Approximately **10GB** of disk space is needed for environment setup

---

### 🚀 Installation Steps (10–30 minutes)

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

4. **Set Up Python Environment**

   ```bash
   conda create -n ir-optset python=3.10 -y
   conda activate ir-optset
   pip install -r requirements.txt
   ```

5. **Configure Tool Paths**

   Edit `IRDS/config/settings.yaml` and set the paths to LLVM/Alive2 executables. For example:

   ```yaml
   clang: /path/to/llvm-project/build/bin/clang
   clangpp: /path/to/llvm-project/build/bin/clang++
   opt: /path/to/llvm-project/build/bin/opt
   llc: /path/to/llvm-project/build/bin/llc
   alive2: /path/to/alive2/build/alive-tv
   ```

---

### 🔨 Dataset Generation Workflow

The dataset generation process follows a front-end → back-end pipeline.

First, set the project root directory:

```shell
export DIR=$(pwd)
```

1. **Generate IR Data**

   The `test` folder contains example `.c` files for immediate testing:

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

   **Output Directories:**

   * **UNOPT**: Unoptimized IR (.ll)
   * **EX**: Function-level extracted IR
   * **OPT**: Optimized IR
   * **LOG**: Optimization logs
   * **PRE\_EX**: Preprocessed (before optimization)
   * **PRE\_OPT**: Preprocessed (after optimization)

2. **Build Dataset**

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

   * **filters**: Primary filters, e.g., `func_body_changed`, `token_limit_v3`
   * **vfilters**: Secondary filters, e.g., `keep_core`, `dedupe_content`
   * **prompt-template**: Defines input prompt format for models

   The final dataset will be available under `$DIR/test/tmp/dataset`.

---

### 🔍 Additional Tools

We provide a variety of auxiliary tools for validation and automated analysis:

| Script               | Description                                      |
| -------------------- | ------------------------------------------------ |
| `alive2.py`          | Automatic equivalence checking (Alive2)          |
| `analyze_changed.py` | Extract & count effective optimization passes    |
| `dataset_info.py`    | View dataset statistics and samples              |
| `mca_cycles.py`      | Static performance analysis (`llc` + `llvm-mca`) |
| `merge_dataset.py`   | Merge multiple dataset samples                   |
| `opt_verify.py`      | Batch verify IR syntactic correctness            |

---

#### Usage: `mca_cycles.py`

```bash
cd $DIR/IRDS/tools
python mca_cycles.py $DIR/test/tmp/PRE_OPT/ --suffix ".ll"
```

This prints an **OptVerifier Summary** table showing average cycles and pass/fail counts. Other optional flags:

* `--csv 1.csv`: Export results to CSV
* `--dispatch-width`: Set processor dispatch width (default 6)
* `--metric`: Default is `cycle`, optional: `rthroughput`

> Example:
>
> ```bash
> python mca_cycles.py $DIR/test/tmp/PRE_OPT/ --suffix ".ll" --dispatch-width 1 --mcpu znver5 --metric rthroughput
> ```

#### Usage: `analyze_changed.py`

```shell
cd $DIR/IRDS/tools
python analyze_changed.py --input $DIR/test/tmp/LOG --csv tmp
```

This outputs an analysis of attempted vs. effective optimization passes.

* Use `--sample <number>` and `--seed <number>` to randomly sample log files (default: all logs)

#### Usage: `opt_verify.py`

```shell
python opt_verify.py --folder $DIR/test/tmp/FINAL/ --log-errors --log-dir "./logs" --clean --suffix ".ll"
```

This checks syntax correctness of `.ll` files and summarizes results (should be 100% valid).

#### Usage: `alive2.py`

```shell
cd $DIR/IRDS/tools
python alive2.py --input-dir $DIR/test/alive --suffix ".model.predict.ll" --output-dir ./tmp
```

Failed Alive2 equivalence checks will be logged. Final results include pass/fail counts and CSV export (SMT solving may take time).

#### Usage: `dataset_info.py`

```shell
cd $DIR/IRDS/tools
python dataset_info.py --root-path $DIR/test/tmp/dataset --preview --split test --num-samples 1 --full-preview --draw-hist
```

This gives a visual and statistical summary of the dataset, including token count distributions (min/median/max/average, etc.).

---

### 📄 License

MIT License. See the `LICENSE` file for details.