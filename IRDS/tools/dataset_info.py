from typing import Any, List, Optional
import sys
import os
import argparse
from datasets import load_from_disk
from datasets import Dataset, DatasetDict
import numpy as np
from transformers import AutoTokenizer
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich import box
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
import matplotlib.pyplot as plt

class DatasetStats:
    """Compute and display token statistics for text datasets.

    Args:
        root_path (str): Path containing train/valid/test folders.
        model_path (Optional[str]): Path or name of the pretrained tokenizer.
        max_length (int): Maximum number of tokens per sample.
    """
    def __init__(self, root_path: str, model_path: Optional[str], max_length: int = 4096) -> None:
        self.root_path = root_path
        # Validate dataset root path
        if not os.path.isdir(self.root_path):
            self.console = Console()
            self.console.print(f"[red]Dataset root not found: {self.root_path}[/red]")
            sys.exit(1)
        self.model_path = model_path
        self.max_length = max_length
        self.console = Console()
        if model_path is None:
            # Define dummy tokenizer
            class DummyTokenizer:
                def __call__(self, text, truncation=True, max_length=None, padding=False):
                    length = len(text) // 2
                    if max_length is not None:
                        length = min(length, max_length)
                    return {"input_ids": [0] * length}
            self.tokenizer = DummyTokenizer()
        else:
            # Load tokenizer and handle errors
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            except Exception as e:
                self.console.print(f"[red]Failed to load tokenizer from {model_path}: {e}[/red]")
                sys.exit(1)
        self.datasets = {}  # Mapping from split name -> dataset

    def _extract_text(self, data_point: Any) -> str:
        """Extract text from a data point.

        Supports raw strings or dicts with keys 'prompt', 'text', or 'content'.

        Args:
            data_point (Any): A dataset entry.

        Returns:
            str: Extracted text.
        """
        if isinstance(data_point, str):
            return data_point
        for key in ("prompt", "text", "content"):
            if key in data_point:
                return data_point[key]
        # Fallback: string‑ify whole dict
        return str(data_point)

    def load_all_datasets(self) -> None:
        """Load a dataset from the root path. Handles DatasetDict and Dataset."""
        with self.console.status("Loading dataset...", spinner="dots"):
            try:
                ds = load_from_disk(self.root_path)
            except Exception as e:
                self.console.print(f"[red]Failed to load dataset: {e}[/red]")
                return
        # Determine type and register splits
        if isinstance(ds, DatasetDict):
            for split_name, subset in ds.items():
                self.datasets[split_name] = subset
                self.console.print(f"[green]Loaded split '{split_name}' with {len(subset)} samples.[/green]")
        elif isinstance(ds, Dataset):
            self.datasets["default"] = ds
            self.console.print(f"[green]Loaded dataset with {len(ds)} samples.[/green]")
        else:
            self.console.print("[red]Unsupported dataset type.[/red]")

    def calculate_token_lengths(self, dataset: Dataset) -> List[int]:
        """Tokenize samples and compute their token lengths.

        Args:
            dataset (Dataset): A Hugging Face Dataset split.

        Returns:
            List[int]: Token lengths for each sample.
        """
        token_lengths: List[int] = []
        for i, data_point in enumerate(track(dataset, description="Tokenizing samples..."), start=1):
            try:
                text = self._extract_text(data_point)
                tokens = self.tokenizer(text, truncation=True, max_length=self.max_length, padding=False)
                token_lengths.append(len(tokens["input_ids"]))
            except Exception as e:
                self.console.print(f"[red]Tokenization error at sample {i}: {e}, skipping[/red]")
                continue
        return token_lengths

    def show_statistics(self, draw_histogram: bool = False) -> None:
        """Display token statistics and optionally plot histograms.

        Args:
            draw_histogram (bool): Whether to display token length histograms.
        """
        self.console.rule("Displaying token statistics")
        for split, dataset in self.datasets.items():
            token_lengths = self.calculate_token_lengths(dataset)

            if not token_lengths:
                self.console.print(f"[red]No tokens found for {split} dataset.[/red]")
                continue

            total_tokens = np.sum(token_lengths)
            avg_tokens = np.mean(token_lengths)
            max_tokens = np.max(token_lengths)
            min_tokens = np.min(token_lengths)
            median_tokens = np.median(token_lengths)

            table = Table(title=f"Token Statistics for {split}", box=box.SIMPLE_HEAVY)
            table.add_column("Metric", justify="right")
            table.add_column("Value", justify="left")

            table.add_row("Total Tokens", str(total_tokens))
            table.add_row("Average Tokens", f"{avg_tokens:.2f}")
            table.add_row("Max Tokens", str(max_tokens))
            table.add_row("Min Tokens", str(min_tokens))
            table.add_row("Median Tokens", f"{median_tokens}")

            self.console.print(table)

            if draw_histogram:
                self.draw_histogram(token_lengths, split)

    def draw_histogram(self, token_lengths: List[int], split: str) -> None:
        """Draw a histogram of token lengths.

        Args:
            token_lengths (List[int]): List of token counts.
            split (str): Dataset split name.
        """
        plt.figure(figsize=(8, 4))
        plt.hist(token_lengths, bins=20)
        plt.title(f"Token Length Distribution - {split}")
        plt.xlabel("Token Length")
        plt.ylabel("Frequency")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def preview_samples(self, split: str, num_samples: int = 5, full_preview: bool = False) -> None:
        """Preview a few samples from the specified dataset split.

        Args:
            split (str): Dataset split name ('train', 'valid', 'test').
            num_samples (int): Number of samples to preview.
            full_preview (bool): Whether to show full sample text without truncation.
        """
        dataset = self.datasets.get(split)
        if not dataset:
            self.console.print(f"[red]No dataset found for split: {split}[/red]")
            return

        self.console.rule(f"Previewing samples from {split}")

        for i in range(min(num_samples, len(dataset))):
            sample = dataset[i]
            text = self._extract_text(sample)
            if not full_preview:
                text = text[:300] + ("..." if len(text) > 300 else "")
            panel = Panel.fit(Text(text, style="none"), title=f"Sample {i+1}", border_style="green")
            self.console.print(panel)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dataset Information and Token Statistics Tool")
    parser.add_argument("--root-path", type=str, required=True, help="Path to dataset directory or dataset split folder.")
    parser.add_argument("--model", type=str, required=False, help="Path or name of the pre-trained model.")
    parser.add_argument("--preview", action="store_true", help="Preview a few samples from the dataset.")
    parser.add_argument("--split", type=str, help="Which split to preview (if not set, auto-detect from available).")
    parser.add_argument("--num-samples", type=int, default=5, help="Number of samples to preview (default: 5).")
    parser.add_argument("--full-preview", action="store_true", help="Show full prompt text when previewing.")
    parser.add_argument("--max-length", type=int, default=4096, help="Max token length when tokenizing text (default: 4096).")
    parser.add_argument("--draw-hist", action="store_true", help="Draw token length histogram after statistics.")
    args = parser.parse_args()

    with Console().status("Initializing DatasetStats...", spinner="dots"):
        stats_tool = DatasetStats(args.root_path, args.model, max_length=args.max_length)
    stats_tool.load_all_datasets()

    # Auto-select split if not provided
    if args.split is None:
        available_splits = list(stats_tool.datasets.keys())
        if not available_splits:
            stats_tool.console.print("[red]No datasets found in the specified root path.[/red]")
            return
        args.split = available_splits[0]
        stats_tool.console.print(f"[yellow]No split specified. Using available dataset: {args.split}[/yellow]")

    if args.preview:
        stats_tool.preview_samples(args.split, num_samples=args.num_samples, full_preview=args.full_preview)

    stats_tool.show_statistics(draw_histogram=args.draw_hist)


if __name__ == "__main__":
    main()