"""
DatasetMerger: Merge multiple HuggingFace datasets by sampling from each and concatenating.

Usage:
    python merge_dataset.py --input-dirs DIR1 DIR2 ... --out-dir OUTPUT_DIR --samples-per-dataset N

Enhancements:
- Validates input paths and parameters.
- Handles load/save errors with clear messages.
- Logs progress using Rich console.
"""
import argparse
import sys
from pathlib import Path
from typing import List
from datasets import load_from_disk, concatenate_datasets, Dataset
from rich.console import Console

console = Console()


class DatasetMerger:
    """Orchestrates merging of multiple HuggingFace datasets by sampling.

    Args:
        input_dirs (List[str]): Paths to input dataset directories.
        output_dir (str): Path to save the merged dataset.
        samples_per_dataset (int): Number of samples to draw from each dataset.
    """

    def __init__(self, input_dirs: List[str], output_dir: str, samples_per_dataset: int) -> None:
        # Convert to Path objects and validate
        self.input_dirs: List[Path] = [Path(d) for d in input_dirs]
        if not self.input_dirs:
            console.print("[red]Error: No input directories provided.[/red]")
            sys.exit(1)
        for d in self.input_dirs:
            if not d.is_dir():
                console.print(f"[red]Input directory not found or not a directory: {d}[/red]")
                sys.exit(1)

        # Prepare output directory
        self.output_dir = Path(output_dir)
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            console.print(f"[red]Failed to create output directory {self.output_dir}: {e}[/red]")
            sys.exit(1)

        self.samples_per_dataset = samples_per_dataset
        if samples_per_dataset <= 0:
            console.print(f"[red]samples_per_dataset must be positive, got {samples_per_dataset}[/red]")
            sys.exit(1)

    def _load_dataset(self, dataset_dir: Path) -> Dataset:
        """Load a HuggingFace dataset from disk, returning the 'test' split or full dataset."""
        if not dataset_dir.exists() or not dataset_dir.is_dir():
            console.print(f"[red]Dataset directory does not exist or is not a directory: {dataset_dir}[/red]")
            sys.exit(1)
        try:
            dataset = load_from_disk(str(dataset_dir))
        except Exception as e:
            console.print(f"[red]Failed to load dataset from {dataset_dir}: {e}[/red]")
            sys.exit(1)
        if "test" in dataset:
            dataset = dataset["test"]
        console.print(f"Loaded {len(dataset)} rows from {dataset_dir}")
        return dataset

    def _sample_dataset(self, dataset: Dataset, num_samples: int) -> Dataset:
        """Randomly sample up to num_samples from the dataset."""
        if len(dataset) <= num_samples:
            console.print(f"Dataset has only {len(dataset)} rows, using all.")
            return dataset
        try:
            sampled = dataset.shuffle(seed=42).select(range(num_samples))
        except Exception as e:
            console.print(f"[red]Failed to sample dataset: {e}[/red]")
            sys.exit(1)
        console.print(f"Sampled {len(sampled)} rows.")
        return sampled

    def merge_datasets(self) -> None:
        """Merge samples from each dataset and save merged dataset to output_dir."""
        console.rule("Merging datasets")
        all_samples: List[Dataset] = []
        for dir_path in self.input_dirs:
            try:
                dataset = self._load_dataset(dir_path)
            except SystemExit:
                console.print(f"[yellow]Skipping dataset at {dir_path} due to load error.[/yellow]")
                continue
            try:
                sample = self._sample_dataset(dataset, self.samples_per_dataset)
            except SystemExit:
                console.print(f"[yellow]Skipping sampling for dataset at {dir_path} due to error.[/yellow]")
                continue
            all_samples.append(sample)

        if not all_samples:
            console.print("[red]No datasets were successfully loaded and sampled. Exiting.[/red]")
            sys.exit(1)

        try:
            merged_dataset = concatenate_datasets(all_samples)
        except Exception as e:
            console.print(f"[red]Failed to concatenate datasets: {e}[/red]")
            sys.exit(1)

        try:
            merged_dataset.save_to_disk(str(self.output_dir))
        except Exception as e:
            console.print(f"[red]Failed to save merged dataset to {self.output_dir}: {e}[/red]")
            sys.exit(1)

        console.print(f"✅ Merged dataset saved to: {self.output_dir} ({len(merged_dataset)} rows)")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Merge multiple HuggingFace datasets by sampling from each.")
    parser.add_argument("--input-dirs", nargs="+", required=True, help="List of input directories with datasets.")
    parser.add_argument("--out-dir", required=True, help="Directory to save the merged dataset.")
    parser.add_argument("--samples-per-dataset", type=int, required=True, help="Number of samples to take from each dataset.")
    return parser.parse_args()


def main() -> None:
    """Entry point for merging datasets."""
    args = parse_args()
    try:
        with console.status("[bold green]Merging datasets..."):
            merger = DatasetMerger(args.input_dirs, args.out_dir, args.samples_per_dataset)
            merger.merge_datasets()
    except Exception as e:
        console.print(f"[red]An unexpected error occurred: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()