import argparse
import re
import csv
import random
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm
from rich.console import Console

class PassLogAnalyzer:
    def __init__(self, input_dir: Path, output_csv: Path, sample_size: int = None, seed: int = 42):
        self.input_dir = input_dir
        self.output_csv = output_csv
        self.sample_size = sample_size
        self.seed = seed
        self.console = Console()
        self.before_re = re.compile(r"\*\*\* IR Dump Before (\w+) on .+ \*\*\*")

    def extract_effective_passes(self, log_path: Path):
        effective = set()
        try:
            with log_path.open('r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    match = self.before_re.match(line.strip())
                    if match:
                        effective.add(match.group(1))
        except Exception as e:
            self.console.print(f"[red]Failed to read {log_path}: {e}[/red]")
        return effective

    def write_effective_pass_csv(self, log_files):
        with self.output_csv.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['log_file', 'active_passes'])  # Header
            for log_path in tqdm(log_files, desc="Writing effective pass CSV"):
                effective_passes = self.extract_effective_passes(log_path)
                writer.writerow([log_path.name, ",".join(sorted(effective_passes))])

    def analyze(self):
        log_files = sorted(self.input_dir.glob('*.log'))
        if self.sample_size:
            random.seed(self.seed)
            log_files = random.sample(log_files, min(self.sample_size, len(log_files)))
            self.console.print(f"[bold blue]Sampled {len(log_files)} logs from {self.input_dir} with seed {self.seed}[/bold blue]")
        if not log_files:
            self.console.print(f"[bold red]No .log files found in {self.input_dir}[/bold red]")
            return
        self.write_effective_pass_csv(log_files)
        self.console.print(f"[green]Done: output saved to {self.output_csv}[/green]")

def parse_args():
    parser = argparse.ArgumentParser(description="Extract unique active LLVM passes from logs.")
    parser.add_argument('-i', '--input', required=True, help='Directory with .log files')
    parser.add_argument('--csv', required=True, help='Output CSV file path')
    parser.add_argument('--sample-size', type=int, default=None, help='Random sample count')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for sampling')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    input_dir = Path(args.input).expanduser()
    output_csv = Path(args.csv).expanduser()
    analyzer = PassLogAnalyzer(input_dir, output_csv, sample_size=args.sample_size, seed=args.seed)
    analyzer.analyze()