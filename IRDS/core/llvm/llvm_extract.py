# File: core/llvm/llvm_extract.py

import subprocess
import os
from typing import List
from core.llvm.base import ToolRunner
class LLVMExtractFunctions:
    def __init__(self):
        # Initialize runners for llvm-as, llvm-nm, llvm-extract, and llvm-dis
        self.as_runner = ToolRunner("llvm-as", "llvm_as")
        self.nm_runner = ToolRunner("llvm-nm", "llvm_nm")
        self.extract_runner = ToolRunner("llvm-extract", "llvm_extract")
        self.dis_runner = ToolRunner("llvm-dis", "llvm_dis")
        # Use extract_runner's logger for consistency
        self.log = self.extract_runner.log

    def _infer_suffix(self, flags: List[str]) -> str:
        return ".ll"  # Using .ll directly

    def extract_functions(self, llfile: str, output_dir: str):
        """
        Extract functions from the given .ll file and save them as separate .ll files.

        Args:
            llfile (str): The input LLVM IR file (.ll).
            output_dir (str): The directory to save extracted functions.
        """
        base = os.path.basename(llfile)

        # Limit the length of the base file name if needed (e.g., 100 characters)
        if len(base) > 100:
            import hashlib
            hash_suffix = hashlib.md5(base.encode()).hexdigest()[:8]
            base = base[:90] + f"_{hash_suffix}"

        # Step 1: Convert .ll to .bc using llvm-as
        bcfile = self._convert_ll_to_bc(llfile)

        if not bcfile or not os.path.exists(bcfile):
            self.log.debug(f"Failed to convert {llfile} to .bc")
            return

        # Step 2: Get function names using llvm-nm
        func_names = self._get_function_names(bcfile)

        if not func_names:
            self.log.debug(f"No functions found in {bcfile}, skipping extraction.")
            return

        for func in func_names:
            safe_func = self._sanitize_function_name(func)

            # Limit the length of the function name part to avoid long filenames
            if len(safe_func) > 100:
                import hashlib
                hash_suffix = hashlib.md5(safe_func.encode()).hexdigest()[:8]
                safe_func = safe_func[:90] + f"_{hash_suffix}"

            outbc = os.path.join(output_dir, f"{base}_{safe_func}.bc")
            outll = os.path.join(output_dir, f"{base}_{safe_func}.ll")

            # extract to bitcode per function
            if not self.extract_runner._run_one((bcfile, outbc, [f"-func={func}"])):
                continue

            # disassemble extracted bitcode to text IR
            if os.path.exists(outbc):
                self.dis_runner._run_one((outbc, outll, []))
                try:
                    os.remove(outbc)
                except FileNotFoundError:
                    self.log.warning(f"Expected .bc file not found: {outbc}")
            else:
                self.log.warning(f"opt failed to generate: {outbc}")

    def _convert_ll_to_bc(self, llfile: str) -> str:
        """
        Use llvm-as to convert .ll file to .bc (bitcode).
        """
        bcfile = llfile.replace(".ll", ".bc")
        cmd = [self.as_runner.tool_path, llfile, "-o", bcfile]
        
        result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            self.log.debug(f"llvm-as failed for {llfile}: {result.stderr}")
            return None
        return bcfile

    def _get_function_names(self, bcfile: str) -> List[str]:
        """
        Use llvm-nm to get the list of function names from a .bc file.
        """
        cmd = [self.nm_runner.tool_path, "--defined-only", bcfile]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            self.log.debug(f"llvm-nm failed for {bcfile}: {result.stderr}")
            return []

        # Filter for functions marked as 'T' (text section, i.e., functions)
        func_names = [
            line.split()[2] for line in result.stdout.splitlines() if ' T ' in line
        ]
        return func_names

    def _sanitize_function_name(self, func: str) -> str:
        """
        Sanitize the function name to make it filesystem-safe (replace non-alphanumeric characters).
        """
        return func.replace(" ", "_").replace("-", "_").replace(",", "_")