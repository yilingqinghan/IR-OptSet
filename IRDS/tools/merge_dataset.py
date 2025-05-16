import argparse
import random
import os
from typing import List
from datasets import load_from_disk, concatenate_datasets, Dataset


class DatasetMerger:
    def __init__(self, input_dirs: List[str], output_dir: str, samples_per_dataset: int):
        self.input_dirs = input_dirs
        self.output_dir = output_dir
        self.samples_per_dataset = samples_per_dataset
        os.makedirs(self.output_dir, exist_ok=True)

    def _load_dataset(self, dataset_dir: str) -> Dataset:
        dataset = load_from_disk(dataset_dir)
        if "test" in dataset:
            dataset = dataset["test"]
        print(f"Loaded {len(dataset)} rows from {dataset_dir}")
        return dataset

    def _sample_dataset(self, dataset: Dataset, num_samples: int) -> Dataset:
        if len(dataset) <= num_samples:
            print(f"Dataset has only {len(dataset)} rows, using all.")
            return dataset
        sampled = dataset.shuffle(seed=42).select(range(num_samples))
        print(f"Sampled {len(sampled)} rows.")
        return sampled

    def merge_datasets(self):
        all_samples = []
        for dir_path in self.input_dirs:
            dataset = self._load_dataset(dir_path)
            sample = self._sample_dataset(dataset, self.samples_per_dataset)
            all_samples.append(sample)

        merged_dataset = concatenate_datasets(all_samples)
        merged_dataset.save_to_disk(self.output_dir)
        print(f"✅ Merged dataset saved to: {self.output_dir} ({len(merged_dataset)} rows)")


def parse_args():
    parser = argparse.ArgumentParser(description="Merge multiple HuggingFace datasets by sampling from each.")
    parser.add_argument("--input-dirs", nargs="+", required=True, help="List of input directories with datasets.")
    parser.add_argument("--out-dir", required=True, help="Directory to save the merged dataset.")
    parser.add_argument("--samples-per-dataset", type=int, required=True, help="Number of samples to take from each dataset.")
    return parser.parse_args()


def main():
    args = parse_args()
    merger = DatasetMerger(args.input_dirs, args.out_dir, args.samples_per_dataset)
    merger.merge_datasets()


if __name__ == "__main__":
    main()