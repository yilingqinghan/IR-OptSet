# core/llvm/clang.py

from typing import List
from core.llvm.base import ToolRunner

class ClangCompiler(ToolRunner):
    """
    Compiler wrapper for clang, supports parallel compilation and suffix inference based on flags.
    """
    def __init__(self):
        super().__init__("clang", "clang")

    def _infer_suffix(self, flags: List[str]) -> str:
        if "-E" in flags:
            return ".i"
        if "-S" in flags and "-emit-llvm" in flags:
            return ".ll"
        if "-S" in flags:
            return ".s"
        if "-c" in flags:
            return ".o"
        return ".o"

    def compile(self, source_files: List[str], output_dir: str, flags: List[str]) -> List[str]:
        """
        Compile source files into objects/assembly/IR based on flags.
        """
        return self.run(source_files, output_dir, flags)