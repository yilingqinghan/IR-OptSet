import argparse
import re
import csv
import random
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm
from rich.console import Console
from rich.table import Table

class PassLogAnalyzer:
    def __init__(self, input_dir: Path, output_base: Path, sample_size: int = None, seed: int = 42):
        self.input_dir = input_dir
        self.output_base = output_base
        self.sample_size = sample_size
        self.seed = seed
        self.console = Console()
        # Regex for Before and After entries
        self.before_re = re.compile(r"\*\*\* IR Dump Before (\w+) on .+ \*\*\*")
        self.after_re = re.compile(r"\*\*\* IR Dump After ([\w]+)<?.*>? on .+ \*\*\*")
        self.unique_effective_sequence = []

    def count_passes_in_log(self, log_path: Path):
        attempted = defaultdict(int)
        effective = defaultdict(int)
        try:
            with log_path.open('r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            self.console.print(f"[red]Failed to read {log_path}: {e}[/red]")
            return attempted, effective

        # Count attempted from After entries
        # Count effective from Before entries
        for line in lines:
            text = line.strip()
            m_after = self.after_re.match(text)
            if m_after:
                pass_name = m_after.group(1)
                attempted[pass_name] += 1
            m_before = self.before_re.match(text)
            if m_before:
                pass_name = m_before.group(1)
                effective[pass_name] += 1
        return attempted, effective

    def collect_all_pass_names(self, log_files):
        all_passes = set()
        for log_path in tqdm(log_files, desc="Collecting pass names"):
            attempted, effective = self.count_passes_in_log(log_path)
            all_passes.update(attempted.keys())
            all_passes.update(effective.keys())
        return sorted(all_passes)

    def write_csv(self, csv_path: Path, log_files, all_passes, mode='attempted'):
        totals = defaultdict(int)
        with csv_path.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['log_file'] + all_passes)
            for log_path in tqdm(log_files, desc=f"Writing {mode} CSV"):
                attempted, effective = self.count_passes_in_log(log_path)
                counts = attempted if mode == 'attempted' else effective
                for p in all_passes:
                    totals[p] += counts.get(p, 0)
                row = [log_path.name] + [counts.get(p, 0) for p in all_passes]
                writer.writerow(row)
            # CSV summary rows
            writer.writerow(["=SUM"] + [totals[p] for p in all_passes])
            total_sum = sum(totals.values())
            writer.writerow(["=TOTAL_SUM"] + ["" for _ in all_passes[:-1]] + [total_sum])
        return total_sum

    def display_summary(self, attempted_sum: int, effective_sum: int):
        table = Table(title="Pass Count Summary (TOTAL_SUM)")
        table.add_column("Type", style="cyan")
        table.add_column("TOTAL_SUM", justify="right", style="bold red")
        table.add_row("Attempted Passes", str(attempted_sum))
        table.add_row("Effective Passes", str(effective_sum))
        self.console.print(table)

    def analyze(self):
        log_files = sorted(self.input_dir.glob('*.log'))
        if self.sample_size:
            random.seed(self.seed)
            log_files = random.sample(log_files, min(self.sample_size, len(log_files)))
            self.console.print(f"[bold blue]Sampled {len(log_files)} logs from {self.input_dir} with seed {self.seed}[/bold blue]")
        if not log_files:
            self.console.print(f"[bold red]No .log files found in {self.input_dir}[/bold red]")
            return
        for log_path in log_files:
            try:
                with log_path.open('r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        text = line.strip()
                        m_before = self.before_re.match(text)
                        if m_before:
                            name = m_before.group(1)
                            if name not in self.unique_effective_sequence:
                                self.unique_effective_sequence.append(name)
            except Exception:
                pass
        unique_count = len(self.unique_effective_sequence)
        all_passes = self.collect_all_pass_names(log_files)
        attempted_csv = self.output_base.with_name(self.output_base.stem + "_attempted.csv")
        effective_csv = self.output_base.with_name(self.output_base.stem + "_effective.csv")
        attempted_sum = self.write_csv(attempted_csv, log_files, all_passes, mode='attempted')
        effective_sum = self.write_csv(effective_csv, log_files, all_passes, mode='effective')
        self.display_summary(attempted_sum, effective_sum)
        self.console.print(f"[bold green]Unique effective passes count:[/] {unique_count}")


def parse_args():
    parser = argparse.ArgumentParser(description="Parse LLVM print-changed logs to generate pass CSVs.")
    parser.add_argument('-i','--input', required=True, help='Directory with .log files')
    parser.add_argument('--csv', required=True, help='CSV base path (no suffix)')
    parser.add_argument('--sample-size', type=int, default=None, help='Random sample count')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for sampling')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    input_dir = Path(args.input).expanduser()
    output_base = Path(args.csv).expanduser()
    analyzer = PassLogAnalyzer(input_dir, output_base, sample_size=args.sample_size, seed=args.seed)
    analyzer.analyze()

# python3 analyze_changed.py \
#   --input /path/to/logs \
#   --csv /path/to/output/prefix \
#   --sample-size 50 \
#   --seed 123