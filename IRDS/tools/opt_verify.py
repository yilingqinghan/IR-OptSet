import os
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm

from rich.console import Console
from rich.table import Table
from config.config import ToolchainConfig

import re

class OptVerifier:
    def __init__(self, opt_path=None, log_errors=False, log_dir=None, num_workers=4, clean=False, suffix=".ll", pad=None):
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
        self.pad = pad

        if self.log_errors:
            os.makedirs(self.log_dir, exist_ok=True)

    def verify_folder(self, folder_path):
        """
        Verify all .ll files in the folder using thread pool.
        """
        if not os.path.isdir(folder_path):
            self.console.print(f"[red]Error: Folder {folder_path} does not exist.[/red]")
            return

        ll_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(self.suffix)]

        if not ll_files:
            self.console.print(f"[yellow]No .ll files found in {folder_path}[/yellow]")
            return

        self.console.print(f"[bold cyan]Verifying {len(ll_files)} .ll files with {self.num_workers} threads...[/bold cyan]\n")

        error_records = []

        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {executor.submit(self.run_opt_verify, file): file for file in ll_files}

            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing .ll files", ncols=100):
                result = future.result()
                if not result["success"]:
                    error_records.append(result)

        success_count = len(ll_files) - len(error_records)
        failure_count = len(error_records)

        self.display_result(success_count, failure_count, len(ll_files))

        if self.log_errors and error_records:
            self.save_error_logs(error_records)

    def run_opt_verify(self, filepath):
        """
        Run opt -passes=verify on a given file.
        :param filepath: Path to .ll file
        :return: Dict { 'file': filepath, 'success': bool, 'error': error message }
        """
        if self.clean:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            cleaned = re.sub(r"^Opt IR:", "", content, flags=re.MULTILINE)
            cleaned = cleaned.replace("\\n", "")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(cleaned)
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

    def save_error_logs(self, error_records):
        """
        Save detailed error messages from failed files to a log file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"opt_verify_errors_{timestamp}.log")

        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Total Failed Files: {len(error_records)}\n")
            f.write("=" * 60 + "\n\n")
            for record in error_records:
                f.write(f"File: {record['file']}\n")
                f.write(f"Error:\n{record['error']}\n")
                f.write("=" * 60 + "\n\n")

        self.console.print(f"\n[bold yellow]Detailed error logs saved to: {log_file}[/bold yellow]")

    def display_result(self, success_count, failure_count, total_files):
        """
        Display the verification results in a rich Table.
        """
        denom = self.pad if self.pad is not None else total_files
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
    parser = argparse.ArgumentParser(description="Verify .ll files using opt -passes=verify")
    parser.add_argument("--folder", type=str, required=True, help="Folder containing .ll files to verify")
    parser.add_argument("--opt-path", type=str, default=None, help="Path to the opt binary (optional)")
    parser.add_argument("--log-errors", action="store_true", help="Whether to save error logs")
    parser.add_argument("--log-dir", type=str, default="./opt_error_logs", help="Directory to save error logs")
    parser.add_argument("--num-workers", type=int, default=4, help="Number of parallel workers (default: 4)")
    parser.add_argument("--clean", action="store_true", help="Clean files before verification by removing 'Opt IR:' headers")
    parser.add_argument("--suffix", type=str, default=".ll", help="File suffix to filter files in folder")
    parser.add_argument("--pad", type=int, default=None, help="Use this number as denominator for pass rate instead of total files")
    args = parser.parse_args()

    verifier = OptVerifier(
        opt_path=args.opt_path,
        log_errors=args.log_errors,
        log_dir=args.log_dir,
        num_workers=args.num_workers,
        clean=args.clean,
        suffix=args.suffix,
        pad=args.pad,
    )
    verifier.verify_folder(args.folder)


if __name__ == "__main__":
    main()
