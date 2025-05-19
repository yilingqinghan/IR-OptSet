"""
opt_verify.py: Verify LLVM .ll files by running `opt -passes=verify`.

Usage:
    python opt_verify.py --folder PATH [--opt-path PATH] [--log-errors] [--log-dir DIR]

Enhancements:
- Validates tool paths and permissions.
- Ensures input folder exists.
- Uses Rich console for structured output.
- Provides detailed error logging.
"""
import os
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from config.config import ToolchainConfig

import re

class OptVerifier:
    """Tool for batch verifying LLVM IR (.ll) files using opt's verify pass.

    Args:
        opt_path (Optional[str]): Path to the `opt` executable.
        log_errors (bool): Whether to save detailed error logs.
        log_dir (Optional[str]): Directory to write error logs.
        num_workers (int): Number of parallel threads.
        clean (bool): If True, remove 'Opt IR:' headers before verification.
        suffix (str): File extension filter for IR files.
    """
    def __init__(self, opt_path=None, log_errors=False, log_dir=None, num_workers=4, clean=False, suffix=".ll"):
        """
        Initialize the OptVerifier tool.
        """
        if opt_path:
            self.opt = opt_path
        else:
            config = ToolchainConfig()
            self.opt = config.opt

        self.console = Console()
        self.log_errors = log_errors
        self.log_dir = log_dir
        self.num_workers = num_workers
        self.clean = clean
        self.suffix = suffix

        # Validate opt executable
        opt_path_obj = Path(self.opt)
        if not opt_path_obj.is_file() or not os.access(str(opt_path_obj), os.X_OK):
            self.console.print(f"[red]Error: opt executable not found or not executable: {self.opt}[/red]")
            sys.exit(1)

        if self.log_errors:
            if self.log_dir:
                self.log_dir = Path(self.log_dir)
                try:
                    self.log_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self.console.print(f"[red]Error: Cannot create log directory {self.log_dir}: {e}[/red]")
                    sys.exit(1)
            else:
                self.console.print(f"[red]Error: log_dir must be specified if log_errors is True[/red]")
                sys.exit(1)

    def verify_folder(self, folder_path):
        """Verify all .ll files in the given folder using a thread pool."""
        path = Path(folder_path)
        if not path.is_dir():
            self.console.print(f"[red]Error: Folder not found: {folder_path}[/red]")
            return

        ll_files = list(path.glob(f"*{self.suffix}"))

        if not ll_files:
            self.console.print(f"[yellow]No .ll files found in {folder_path}[/yellow]")
            return

        self.console.print(f"[bold cyan]Verifying {len(ll_files)} .ll files with {self.num_workers} threads...[/bold cyan]\n")

        error_records = []

        try:
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                futures = {executor.submit(self.run_opt_verify, str(file)): file for file in ll_files}

                for future in tqdm(as_completed(futures), total=len(futures), desc="Processing .ll files", ncols=100):
                    result = future.result()
                    if not result["success"]:
                        error_records.append(result)
        except Exception as e:
            self.console.print(f"[red]Error during verification: {e}[/red]")
            return

        success_count = len(ll_files) - len(error_records)
        failure_count = len(error_records)

        self.display_result(success_count, failure_count, len(ll_files))

        if self.log_errors and error_records:
            self.save_error_logs(error_records)

    def run_opt_verify(self, filepath):
        """Run `opt -passes=verify` on a single .ll file.

        Args:
            filepath (str): Path to the .ll file.
        Returns:
            Dict[str, Any]: {'file': filepath, 'success': bool, 'error': str}
        """
        if self.clean:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                cleaned = re.sub(r"^Opt IR:", "", content, flags=re.MULTILINE)
                cleaned = cleaned.replace("\\n", "")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(cleaned)
            except Exception as e:
                return {"file": filepath, "success": False, "error": f"Cleaning error: {e}"}
        try:
            subprocess.run(
                [self.opt, "-passes=verify", filepath],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )
            return {"file": filepath, "success": True, "error": ""}
        except subprocess.CalledProcessError as e:
            return {"file": filepath, "success": False, "error": e.stderr}
        except Exception as e:
            return {"file": filepath, "success": False, "error": str(e)}

    def save_error_logs(self, error_records):
        """Save error records to a timestamped log file in the log directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"opt_verify_errors_{timestamp}.log"

        try:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"Total Failed Files: {len(error_records)}\n")
                f.write("=" * 60 + "\n\n")
                for record in error_records:
                    f.write(f"File: {record['file']}\n")
                    f.write(f"Error:\n{record['error']}\n")
                    f.write("=" * 60 + "\n\n")

            self.console.print(f"\n[bold yellow]Detailed error logs saved to: {log_file}[/bold yellow]")
        except Exception as e:
            self.console.print(f"[red]Failed to save error logs: {e}[/red]")

    def display_result(self, success_count, failure_count, total_files):
        """Display summary of verification results."""
        denom = total_files
        pass_rate = (success_count / denom) * 100 if denom > 0 else 0.0

        table = Table(title="LLVM opt Verify Summary", show_lines=True)

        table.add_column("Metric", style="cyan", justify="right")
        table.add_column("Count", style="magenta", justify="center")

        table.add_row("Total Files", str(total_files))
        table.add_row("Passed", str(success_count))
        table.add_row("Failed", str(failure_count))
        table.add_row("Pass Rate (%)", f"{pass_rate:.2f}")

        self.console.print(table)


def main():
    """Parse arguments and run the verification tool."""
    parser = argparse.ArgumentParser(description="Verify .ll files using opt -passes=verify")
    parser.add_argument("--folder", type=str, required=True, help="Folder containing .ll files to verify")
    parser.add_argument("--opt-path", type=str, default=None, help="Path to the opt binary (optional)")
    parser.add_argument("--log-errors", action="store_true", help="Whether to save error logs")
    parser.add_argument("--log-dir", type=str, default="./opt_error_logs", help="Directory to save error logs")
    parser.add_argument("--num-workers", type=int, default=4, help="Number of parallel workers (default: 4)")
    parser.add_argument("--clean", action="store_true", help="Clean files before verification by removing 'Opt IR:' headers")
    parser.add_argument("--suffix", type=str, default=".ll", help="File suffix to filter files in folder")
    args = parser.parse_args()

    verifier = OptVerifier(
        opt_path=args.opt_path,
        log_errors=args.log_errors,
        log_dir=args.log_dir,
        num_workers=args.num_workers,
        clean=args.clean,
        suffix=args.suffix,
    )
    verifier.verify_folder(args.folder)


if __name__ == "__main__":
    main()
