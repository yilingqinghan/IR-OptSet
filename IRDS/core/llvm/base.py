# core/llvm/base.py

import os
import subprocess
from typing import List, Tuple, Optional, Any
from utils import logger
from config.config import ToolchainConfig
from utils.parallel import parallel_map

class ToolRunner:
    """
    Base class for running LLVM tools (clang, opt) in parallel with progress and logging.
    """
    def __init__(self, tool_name: str, config_attr: str):
        self.config = ToolchainConfig()
        self.tool_path = getattr(self.config, config_attr)
        self.log = logger.logger()
        if not self.tool_path or not os.path.isfile(self.tool_path):
            self.log.error(f"Invalid {tool_name} path: {self.tool_path}")
            raise ValueError(f"Invalid {tool_name} path: {self.tool_path}")

    def _infer_suffix(self, flags: List[str]) -> str:
        """
        Infer output file suffix based on flags. Subclasses must override.
        """
        raise NotImplementedError

    def _run_one(self, args: Tuple[str, str, List[str]]) -> Optional[str]:
        """
        Run the tool on a single file, capturing both stdout and stderr to a log file.
        The log file path is derived from the output file by replacing its suffix with '.log'.
        """
        src, output_file, flags = args
        log_file = None
        try:
            cmd = [self.tool_path, src, "-o", output_file] + flags
            self.log.debug(f"Running command: {' '.join(cmd)}")
            log_path = os.path.splitext(output_file)[0] + ".log"
            log_file = open(log_path, "w")
            subprocess.run(cmd, check=True, stdout=log_file, stderr=log_file)
            return output_file
        except subprocess.CalledProcessError as e:
            self.log.debug(f"Failed processing {src}: {e}")
            return None
        finally:
            if log_file is not None:
                log_file.close()

    def run(
        self,
        input_files: List[str],
        output_dir: str,
        flags: List[str],
        suffix: Optional[str] = None
    ) -> List[str]:
        """
        Run the tool on input_files in parallel, writing outputs to output_dir.

        Args:
            input_files: List of source/IR file paths.
            output_dir: Directory for outputs.
            flags: Flags to pass to the tool.
            suffix: Optional override of output file suffix.

        Returns:
            List of successfully generated output file paths.
        """
        os.makedirs(output_dir, exist_ok=True)
        if suffix is None:
            suffix = self._infer_suffix(flags)
        self.log.info(f"Output suffix set to: {suffix}")

        jobs: List[Tuple[str, str, List[str]]] = []
        for src in input_files:
            base = os.path.basename(src)
            name = os.path.splitext(base)[0]
            out = os.path.join(output_dir, name + suffix)
            jobs.append((src, out, flags))

        results = parallel_map(self._run_one, jobs, desc=f"Running {os.path.basename(self.tool_path)}")
        return [r for r in results if r]