# IR-OptSet Toolchain

**IR-OptSet** is a comprehensive toolchain for constructing, transforming, and analyzing LLVM IR datasets tailored for large language models (LLMs). It is designed to facilitate research on code optimization, transformation understanding, and compiler behavior modeling.

> > For a quick reproduction setup, please refer to [Reproduction Guide](Docs/English/Reproduce.md).

---

### 🚀 Key Use Cases

- Generate pre- and post-optimization LLVM IR from C code
- Build clean, structured datasets for LLM training and evaluation
- Analyze and verify compiler transformations (semantic & syntactic)
- Perform static performance estimation with `llvm-mca`
- Support LLM-based IR optimization or reasoning research

> 📦 Associated dataset: [IR-OptSet on Hugging Face](https://huggingface.co/datasets/YangziResearch/IR-OptSet)

------

## Project Structure

```
IRDS/
├── cli-frontend.py      # Extract, preprocess, and optimize IR from source code
├── cli-backend.py       # Assemble final dataset with filtering and formatting
├── config/              # Configuration files (YAML & Python)
├── core/                # Internal logic
│   ├── llvm/            # Clang/opt wrappers
│   ├── backend/         # Dataset filtering & validation
│   ├── preprocessing/   # IR transformation rules
│   └── metrics/         # (Reserved for evaluation metrics)
├── dataset/             # Data downloading helpers
├── llm/                 # Model training and prompt construction tools
├── tools/               # Analysis scripts
│   ├── alive2.py        # Semantic equivalence checking
│   ├── mca_cycles.py    # Static performance profiling
│   ├── opt_verify.py    # IR syntax verification
│   └── ...
└── utils/               # Logging, parallelism, token stats
test/
├── cfiles/              # Example C files for testing
└── clean.sh             # Cleanup script
```

------

## Quick Start

[English](Docs/English/QuickStart.en.md)|[简体中文](Docs/简体中文/QuickStart.zh.md)

## License

MIT License — see `LICENSE` for details.