## ⚡ Quick Reproduce (Zero Setup)

Want to try **IR-OptSet** instantly? Use our Docker image and run a series of one-click tests.

### 🐳 1. Pull & Run Docker Image

```bash
docker pull ghcr.io/yilingqinghan/llvm-alive2:fulllinux
docker run -it ghcr.io/yilingqinghan/llvm-alive2:fulllinux
```

### 📂 2. Clone the Repository

Once inside the container:

```bash
cd /workspace
git clone https://github.com/yilingqinghan/IR-OptSet.git
cd IR-OptSet
export DIR=$(pwd)
```

------

## ✅ Functional Test Checklist

Now that everything is set up, try the tools step by step to verify they work.

### 🔧 IR Extraction Pipeline

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
  --sample-size 3 --seed 1 \
  --rules normalize_structs ensure_entry_block remove_blank remove_comments rename_blocks rename_locals \
  --where all \
  --log-out ../test/tmp/LOG \
  --pre-out ../test/tmp/PRE_EX \
  --post-out ../test/tmp/PRE_OPT
```

### 📦 Dataset Construction

```bash
python cli-backend.py \
  --pre-dir ../test/tmp/PRE_EX \
  --post-dir ../test/tmp/PRE_OPT \
  --log-dir ../test/tmp/LOG \
  --filters func_body_changed token_limit_v3 \
  --vfilters keep_core dedupe_content \
  --out-dir ../test/tmp/FINAL \
  --make-dataset \
  --train-size 2 --test-size 1 --valid-size 1 --seed 1 \
  --prompt-template "[INST]Analyze IR:\n<code>{pre_ir}</code>[/INST]..." \
  --dataset-output ../test/tmp/dataset --token-limit 4096
```

### 🔍 Tool 1: Performance Analysis (`mca_cycles.py`)

```bash
cd $DIR/IRDS/tools
python mca_cycles.py $DIR/test/tmp/PRE_OPT --suffix ".ll"
```

### 🔍 Tool 2: Optimization Pass Analysis (`analyze_changed.py`)

```bash
python analyze_changed.py --input $DIR/test/tmp/LOG --csv tmp
```

### 🔍 Tool 3: IR Syntax Check (`opt_verify.py`)

```bash
python opt_verify.py --folder $DIR/test/tmp/FINAL --log-errors --log-dir "./logs" --clean --suffix ".ll"
```

### 🔍 Tool 4: Alive2 Equivalence Check (`alive2.py`)

```bash
python alive2.py --input-dir $DIR/test/alive --suffix ".model.predict.ll" --output-dir ./tmp
```

### 🔍 Tool 5: Dataset Statistics Viewer (`dataset_info.py`)

```bash
python dataset_info.py --root-path $DIR/test/tmp/dataset --preview --split test --num-samples 1 --full-preview --draw-hist
```

------

### 🏁 Done!

By following the above steps, you will:

- Reproduce the IR optimization pipeline
- Validate the correctness and quality of data
- Run static analysis & optimization audits

No manual build steps. No environment headaches. Just results.

> For full details and advanced usage, see the [QuickStart Guide](./QuickStart.en.md).