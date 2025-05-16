#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Tuple

from rich.console import Console
from rich.table import Table
from tqdm import tqdm

# Optional centralized config.
try:
    from config.config import ToolchainConfig  # type: ignore
except ModuleNotFoundError:
    ToolchainConfig = None

_RE_TOTAL_CYCLES = re.compile(r"Total\s+Cycles:\s+(\d+)")
_RE_RTHROUGHPUT = re.compile(r"Block\s+RThroughput:\s+([0-9.]+)")


class MCAError(RuntimeError):
    """Raised when llvm-mca output lacks requested metric."""


class OptVerifier:
    def __init__(
        self,
        *,
        llc_path: str | None,
        llvm_mca_path: str | None,
        workers: int,
        mca_cpu: str,
        suffix: str,
        from_predict: bool,
        extract_before: bool,
        dispatch_width: int,
        pad: int | None,
        metric: str,
        console: Console | None = None,
    ) -> None:
        # Resolve tool paths
        if not llc_path or not llvm_mca_path:
            if ToolchainConfig is None:
                raise ValueError("Must supply --llc/--llvm-mca or have ToolchainConfig")
            cfg = ToolchainConfig()
            llc_path = llc_path or cfg.llc
            llvm_mca_path = llvm_mca_path or cfg.llvm_mca
        for t in (llc_path, llvm_mca_path):
            if not Path(t).is_file():
                raise FileNotFoundError(t)

        self.llc = llc_path
        self.llvm_mca = llvm_mca_path
        self.workers = max(1, workers)
        self.mca_cpu = mca_cpu
        self.suffix = suffix
        self.from_predict = from_predict
        self.extract_before = extract_before
        self.dispatch_width = dispatch_width
        self.pad = pad
        self.metric = metric  # "cycles" or "rthroughput"
        self.console = console or Console()
        self.error_log: Path  # runtime set

    # ------------------------------------------------------------------
    def run(self, root: Path, csv_path: Path) -> None:
        files = sorted(p for p in root.rglob(f"*{self.suffix}") if p.is_file())
        if not files:
            self.console.print(f"[bold red]No '{self.suffix}' files in {root}")
            sys.exit(1)

        self.error_log = root / "llc_errors.log"
        self.error_log.write_text("", encoding="utf-8")

        metric_by_num: Dict[int, float] = {}
        errors: List[Tuple[str, str]] = []

        self.console.print(f"[bold]Processing {len(files)} files ({self.metric})…")
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = {ex.submit(self._process_file, f): f for f in files}
            for fut in tqdm(as_completed(futs), total=len(futs)):
                src = futs[fut]
                num = self._numeric_prefix(src.name)
                try:
                    val = fut.result()  # float or int
                    metric_by_num[num] = val
                except Exception as exc:  # pylint: disable=broad-except
                    metric_by_num[num] = 99999.0     # failure
                    errors.append((src.name, str(exc)))
                    self.console.log(f"[yellow]⚠️  {src.name}: {exc}")

        # fill missing with 0
        if self.pad is not None:
            for i in range(1, self.pad + 1):
                metric_by_num.setdefault(i, 0.0)

        self._write_csv(csv_path, metric_by_num)
        self._print_summary(metric_by_num, errors)

    # ------------------------------------------------------------------
    def _process_file(self, ll_file: Path) -> float:
        # optional extraction
        if self.from_predict:
            txt = ll_file.read_text(encoding="utf-8", errors="ignore")
            parts = txt.split("[/INST]", 1)
            if len(parts) < 2:
                raise RuntimeError("[/INST] marker not found")
            ir = parts[0] if self.extract_before else parts[1]
            # clean junk
            ir = re.sub(r'\\n', "", ir)
            ir = re.sub(r"</?code>|</?s>", "", ir)
            ir = ir.replace("Opt IR:", "").replace("[INST]Optimize the following LLVM IR with O3:", "")
            num = self._numeric_prefix(ll_file.name)
            ext_file = ll_file.parent / f"{num}.extract.ll"
            ext_file.write_text(ir, encoding="utf-8")
            llc_input = str(ext_file)
        else:
            llc_input = str(ll_file)

        # llc
        llc_cmd = [self.llc, "-march=x86-64", "-o", "-", llc_input]
        llc_proc = subprocess.run(llc_cmd, text=True, capture_output=True)

        llc_failed = (
            llc_proc.returncode != 0
            or re.search(r"(?i)\berror:", llc_proc.stderr)  # 不区分大小写匹配 “error:”
        )
        if llc_failed:
            with self.error_log.open("a", encoding="utf-8") as log:
                log.write(f"{ll_file.name} llc failed:\n{llc_proc.stderr}\n")
            raise RuntimeError("llc failed; see llc_errors.log")

        # llvm-mca
        mca_cmd = [
            self.llvm_mca,
            f"-mcpu={self.mca_cpu}",
            f"--dispatch={self.dispatch_width}",
        ]
        mca_proc = subprocess.run(mca_cmd, text=True, input=llc_proc.stdout, capture_output=True, check=True)

        if self.metric == "cycles":
            mat = _RE_TOTAL_CYCLES.search(mca_proc.stdout)
            if not mat:
                raise MCAError("Total Cycles not found")
            return float(mat.group(1))
        else:  # rthroughput
            mat = _RE_RTHROUGHPUT.search(mca_proc.stdout)
            if not mat:
                raise MCAError("Block RThroughput not found")
            return float(mat.group(1))

    # ------------------------------------------------------------------
    def _write_csv(self, path: Path, data: Dict[int, float]) -> None:
        order = list(range(1, self.pad + 1)) if self.pad else sorted(data)
        headers = [f"{i}{self.suffix}" for i in order]
        values = [str(data.get(i, 0)) for i in order]

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["file", *headers])
            w.writerow([self.metric, *values])

    # ------------------------------------------------------------------
    def _print_summary(self, data: Dict[int, float], errors: List[Tuple[str, str]]) -> None:
        ok_vals = [v for v in data.values() if v not in (0, 99999)]
        processed = len(ok_vals)
        avg = mean(ok_vals) if ok_vals else 0.0

        tbl = Table(title="OptVerifier Summary", header_style="bold magenta")
        tbl.add_column("Files OK", justify="right")
        tbl.add_column(f"Average {self.metric}", justify="right")
        tbl.add_column("Errors", justify="right")
        tbl.add_row(str(processed), f"{avg:,.3f}", str(len(errors)))
        self.console.print(tbl)

        if errors:
            et = Table(title="Failures", header_style="bold red")
            et.add_column("File")
            et.add_column("Reason")
            for f, msg in errors:
                et.add_row(f, msg)
            self.console.print(et)

    # ------------------------------------------------------------------
    @staticmethod
    def _numeric_prefix(name: str) -> int:
        try:
            return int(name.split(".", 1)[0])
        except ValueError:
            return -1


# ----------------------------------------------------------------------
def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch llc → llvm-mca → transposed CSV")
    p.add_argument("root", type=Path, help="Directory to scan")
    p.add_argument("--csv", type=Path, default=Path("results.csv"))
    p.add_argument("--suffix", default=".ll")
    p.add_argument("--from-predict", action="store_true")
    p.add_argument("--extract-before", action="store_true",
                   help="With --from-predict: extract text before [/INST]")
    p.add_argument("--pad", type=int, help="Pad to N columns; missing→0, fail→99999")
    p.add_argument("--metric", choices=["cycles", "rthroughput"], default="cycles",
                   help="cycles=Total Cycles (int) | rthroughput=Block RThroughput (float)")
    p.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    p.add_argument("--llc", dest="llc_path")
    p.add_argument("--llvm-mca", dest="llvm_mca_path")
    p.add_argument("--mcpu", default="znver3")
    p.add_argument("--dispatch-width", type=int, default=6)
    return p.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    a = _parse_args(argv)
    verifier = OptVerifier(
        llc_path=a.llc_path,
        llvm_mca_path=a.llvm_mca_path,
        workers=a.workers,
        mca_cpu=a.mcpu,
        suffix=a.suffix,
        from_predict=a.from_predict,
        extract_before=a.extract_before,
        dispatch_width=a.dispatch_width,
        pad=a.pad,
        metric=a.metric,
    )
    verifier.run(a.root, a.csv)


if __name__ == "__main__":
    main()
