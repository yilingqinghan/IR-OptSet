## IR-OptSet Quick Start Guide

### Project Overview

**IR-OptSet** is an automated toolchain for building, filtering, analyzing, and creating LLVM IR datasets. Key features:

* Build and configure LLVM & Alive2 environments
* Extract and preprocess LLVM IR before and after optimizations
* Generate Hugging Face–compatible datasets
* Verify IR correctness and analyze optimization passes
* Perform static performance analysis using `llvm-mca`
* Merge and inspect datasets

---

### 🔧 Prerequisites

* **CMake**, **Ninja**, **Git**, **Python 3.8+**
* **conda** recommended for Python environment management
* \~**5 GB** of disk space for base environment builds

---

### 🚀 Installation Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/yilingqinghan/IR-OptSet.git
   cd IR-OptSet
   ```

2. **Build LLVM (>=19.1.0)**

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

4. **Set up Python environment**

   ```bash
   conda create -n ir-optset python=3.10 -y
   conda activate ir-optset
   pip install -r requirements.txt
   ```

5. **Configure tool paths**

   Edit `IRDS/config/settings.yaml` and specify absolute paths to each executable:

   ```yaml
   clang: /path/to/llvm-project/build/bin/clang
   clangpp: /path/to/llvm-project/build/bin/clang++
   opt: /path/to/llvm-project/build/bin/opt
   llc: /path/to/llvm-project/build/bin/llc
   alive2: /path/to/alive2/build/alive-tv
   ```

---

### 🔨 Data Workflow

1. **Generate IR data**

   Use sample files in `test/cfiles` to test the pipeline:

   ```bash
   python cli-frontend.py pipeline \
     --source-dir test/cfiles \
     --ext .c \
     --clang-flags "-S -emit-llvm -O3 -Xclang -disable-llvm-passes" \
     --compile-out test/tmp/UNOPT \
     --extract-dir test/tmp/EX \
     --opt-out test/tmp/OPT \
     --opt-flags "-passes='default<O3>' -S -print-changed -print-before-changed" \
     --sample-size 10 --seed 1 \
     --rules normalize_structs ensure_entry_block remove_blank remove_comments rename_blocks rename_locals \
     --where all \
     --log-out test/tmp/LOG \
     --pre-out test/tmp/PRE_EX \
     --post-out test/tmp/PRE_OPT
   ```

   **Output directories**:

   * `UNOPT`: Unoptimized IR (.ll files)
   * `EX`: Function-level IR extraction
   * `OPT`: Optimized IR
   * `LOG`: Optimization logs
   * `PRE_EX`: Preprocessed IR before optimization
   * `PRE_OPT`: Preprocessed IR after optimization

2. **Build the dataset**

   ```bash
   python cli-backend.py \
     --pre-dir test/tmp/PRE_EX \
     --post-dir test/tmp/PRE_OPT \
     --log-dir test/tmp/LOG \
     --filters func_body_changed token_limit_v3 \
     --vfilters keep_core dedupe_content \
     --out-dir test/tmp/FINAL \
     --make-dataset \
     --train-size 5 --test-size 1 --valid-size 1 --seed 1 \
     --prompt-template "[INST]Analyze IR:\n<code>{pre_ir}</code>[/INST]..." \
     --dataset-output test/tmp/dataset --token-limit 4096
   ```

   * `--filters`: initial filtering rules (e.g., `func_body_changed`, `token_limit_v3`)
   * `--vfilters`: post-filtering rules (e.g., `keep_core`, `dedupe_content`)
   * `--prompt-template`: prompt template for model input

---

### 🔍 Tool Overview

| Script               | Description                                         |
| -------------------- | --------------------------------------------------- |
| `alive2.py`          | Equivalence checking with Alive2                    |
| `analyze_changed.py` | Extract and count effective optimization passes     |
| `dataset_info.py`    | Inspect dataset statistics and sample entries       |
| `mca_cycles.py`      | Static performance analysis with `llc` + `llvm-mca` |
| `merge_dataset.py`   | Merge multiple datasets by sampling                 |
| `opt_verify.py`      | Batch verify IR syntax using `opt -passes=verify`   |

---

### 📄 License

MIT License. See [LICENSE](LICENSE) for details.