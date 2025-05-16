# core/llvm/opt.py

from typing import List
from core.llvm.base import ToolRunner

class OptOptimizer(ToolRunner):
    """
    Optimizer wrapper for `opt`, supports parallel IR optimization.
    """
    def __init__(self):
        super().__init__("opt", "opt")

    def _infer_suffix(self, flags: List[str]) -> str:
        # Always produce LLVM IR text
        return ".opt.ll"

    def optimize(self, input_files: List[str], output_dir: str, flags: List[str]) -> List[str]:
        """
        Optimize IR files according to given flags.
        """
        return self.run(input_files, output_dir, flags)