IR-OptSet Toolchain
===================

This project provides a complete toolchain for constructing, processing, and evaluating datasets 
for LLVM IR optimization using large language models (LLMs). It includes data preprocessing, 
transformation analysis, verification, and model training utilities.

⚠️ Note: This toolchain is under active development and requires further testing for full stability. 
Please be patient as we work to improve coverage and robustness.

Directory Overview
------------------


```
  IRDS/
  ├── cli-frontend.py      # Apply Clang and opt with preprocessing rules to generate optimized IR and logs
  ├── cli-backend.py       # Assemble the final dataset from generated IR/logs and apply filtering
  ├── config/              # Global config files (YAML and Python)
  ├── core/                # Core compiler logic:
  │   ├── llvm/            # Wrappers for Clang/opt IR manipulation
  │   ├── backend/         # Data filtering logic
  │   ├── preprocessing/   # IR preprocessing rules and plugin architecture
  │   └── metrics/         # (Reserved for evaluation metrics)
  ├── dataset/             # Dataset downloading utilities
  ├── llm/                 # Tools for training and analyzing LLMs on the IR data
  ├── tools/               # Analysis and verification scripts:
  │   ├── alive2.py            # Alive2-based semantic checking
  │   ├── mca_cycles.py        # LLVM-MCA performance simulation
  │   ├── opt_verify.py        # Batch IR syntax verification
  │   └── others...
  └── utils/              # Logging, concurrency, token statistics, etc.
```

```
  test/
  ├── cfiles/             # Test C programs for generating IR
  └── clean.sh            # Script to clean temporary files
```

- Docs → Documentation, appendices, and figures

Getting Started
---------------

1. Setup:
   Install dependencies:
     pip install -r requirements.txt

2. Compile LLVM & Alive2 (see Appendix G of paper or `Docs/` for details)

3. Dataset construction:
   Run `cli-frontend.py` to preprocess and optimize IR
   Run `cli-backend.py` to build datasets from logs and filtered IR pairs

4. Verification:
   Use `tools/alive2.py` to validate semantic equivalence
   Use `tools/opt_verify.py` for syntax checks

5. Performance analysis:
   Use `tools/mca_cycles.py` to estimate cycle counts via llvm-mca

6. Model training:
   Use `llm/train.py` and `llm/mkdataset.py` to prepare and fine-tune models


📦 The associated dataset is publicly available at:
https://huggingface.co/datasets/YangziResearch/IR-OptSet