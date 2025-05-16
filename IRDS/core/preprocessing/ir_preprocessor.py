# File: core/preprocessing/ir_preprocessor.py
"""IRPreprocessor: applies registered transforms to IR files in parallel."""
import os
from typing import List
from utils.parallel import parallel_map
from utils import logger
from .plugin import get_rule
from .builtin_rules import *   # ensure built-in rules are registered

class IRPreprocessor:
    def __init__(self, rules: List[str]):
        self.log = logger.logger()
        self.transforms = [get_rule(name) for name in rules]

    def _process_one(self, args):
        src, dst = args
        try:
            content = open(src).read()
            for tf in self.transforms:
                content = tf(content)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, 'w').write(content)
            return dst
        except Exception as e:
            self.log.debug(f"Failed to preprocess {src}: {e}")
            return None

    def process(self, input_files: List[str], output_dir: str) -> List[str]:
        jobs = []
        for src in input_files:
            name, ext = os.path.splitext(os.path.basename(src))
            dst = os.path.join(output_dir, name + ext)
            jobs.append((src, dst))
        results = parallel_map(self._process_one, jobs, desc="Preprocessing")
        return [r for r in results if r]