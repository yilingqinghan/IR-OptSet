# --- Worker for copying triples (must be module-level for multiprocessing) ---
def copy_one_worker(args):
    """
    Worker for copying triples in parallel.
    Args:
        args: (triple, out_dir)
    """
    import shutil
    triple, out_dir = args
    pre, post, logf = triple
    shutil.copy(pre, out_dir)
    shutil.copy(post, out_dir)
    shutil.copy(logf, out_dir)
   
# File: cli-backend.py
import argparse
import os
import shutil
from typing import List
from utils import logger
from utils.parallel import parallel_map
from core.backend.plugin import get_hfilter, get_vfilter, list_hfilters, list_vfilters
from llm.mkdataset import collect_triples, split_triples, load_file, make_prompt
from datasets import Dataset, DatasetDict
import functools

def apply_hfilter_worker(args):
    """Worker for horizontal filters usable with multiprocessing."""
    triple, filter_name, token_limit = args
    hfilter = get_hfilter(filter_name)
    if filter_name == "token_limit_v1" or filter_name == "token_limit_v2" or filter_name == "token_limit_v3" or filter_name == "token_limit_v4":
        hfilter = functools.partial(hfilter, limit=token_limit)
    return hfilter(*[open(x, 'r').read() for x in triple])

# --- Worker for vertical filters usable with multiprocessing ---
def apply_vfilter_worker(args):
    """
    Worker for vertical filters usable with multiprocessing.
    Args:
        args: (file_path, filter_name, token_limit)
    Returns:
        bool indicating whether to keep this file.
    """
    path, filter_name, token_limit = args
    vfilter = get_vfilter(filter_name)
    # Call vfilter on singleton list, passing limit when needed
    if filter_name == 'token_limit_vfilter':
        kept = vfilter([path], limit=token_limit)
    else:
        kept = vfilter([path])
    return path in kept

log = logger.logger()

def find_files(root_dir: str, suffixes: List[str]) -> List[str]:
    """
    Recursively find files ending with any of the given suffixes in root_dir.
    """
    matches = []
    for dirpath, _, files in os.walk(root_dir):
        for f in files:
            if any(f.endswith(suf) for suf in suffixes):
                matches.append(os.path.join(dirpath, f))
    return matches

# Normalize file stems for pairing
def normalize_stem(filename: str) -> str:
    base = os.path.basename(filename)
    for suf in ('.opt.ll', '.opt.log', '.ll'):
        if base.endswith(suf):
            return base[:-len(suf)]
    return os.path.splitext(base)[0]



def main():
    parser = argparse.ArgumentParser(description="CLI Backend for filtering and dataset creation")
    parser.add_argument('--pre-dir', required=True, help='Directory of pre-IR files')
    parser.add_argument('--post-dir', required=True, help='Directory of post-IR files')
    parser.add_argument('--log-dir', required=True, help='Directory of log files')
    parser.add_argument('--filters', nargs='+', required=False, default=[],
                        help='Horizontal filters to apply')
    parser.add_argument('--vfilters', nargs='+', required=False, default=[],
                        help='Vertical filters to apply')
    parser.add_argument('--out-dir', required=True, help='Output directory for filtered triples')
    parser.add_argument('--make-dataset', action='store_true',
                        help='Generate HuggingFace .arrow dataset from final triples')
    parser.add_argument('--train-size', type=int, default=100,
                        help='Number of training samples')
    parser.add_argument('--test-size', type=int, default=20,
                        help='Number of test samples')
    parser.add_argument('--valid-size', type=int, default=30,
                        help='Number of validation samples')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for splitting')
    parser.add_argument('--prompt-template', type=str,
                        default="Given original IR:\n{pre_ir}\nOptimized IR:\n{opt_ir}\nLog:\n{log}\n",
                        help='Prompt template: use {pre_ir}, {opt_ir}, {log}')
    parser.add_argument('--dataset-output', type=str,
                        help='Output path for .arrow dataset')
    parser.add_argument('--token-limit', type=int, default=2048,
                        help='token limitation for a file')

    args = parser.parse_args()


        
    # Collect files
    pre_files = find_files(args.pre_dir, ['.ll'])
    post_files = find_files(args.post_dir, ['.opt.ll'])
    log_files = find_files(args.log_dir, ['.opt.log'])

    # Build maps
    pre_map = {normalize_stem(p): p for p in pre_files}
    post_map = {normalize_stem(p): p for p in post_files}
    log_map = {normalize_stem(p): p for p in log_files}

    log.debug(f"Pre stems: {list(pre_map.keys())}")
    log.debug(f"Post stems: {list(post_map.keys())}")
    log.debug(f"Log stems: {list(log_map.keys())}")

    # Warn on missing triples
    all_stems = set(pre_map) | set(post_map) | set(log_map)
    for s in sorted(all_stems):
        ok_pre = s in pre_map
        ok_post = s in post_map
        ok_log = s in log_map
        if not (ok_pre and ok_post and ok_log):
            log.debug(f"Missing triple for stem {s}: pre={ok_pre}, post={ok_post}, log={ok_log}")

    # Filter to complete triples
    stems = set(pre_map) & set(post_map) & set(log_map)
    triples = [(pre_map[s], post_map[s], log_map[s]) for s in sorted(stems)]

    log.info(f"Found {len(triples)} complete triples.")

    # Apply horizontal filters
    for fname in args.filters:
        before = len(triples)
        triples = [
            t for t, keep in zip(
                triples,
                parallel_map(
                    apply_hfilter_worker,
                    [(t, fname, args.token_limit) for t in triples],
                    desc=f"Filtering {fname}"
                )
            ) if keep
        ]
        log.info(f"After horizontal filter '{fname}': {len(triples)}/{before}")

    # Apply vertical filters
    for vname in args.vfilters:
        before = len(triples)
        # Special handling for dedupe_content: apply on all files at once, not in parallel
        if vname == "dedupe_content" or vname == "dedupe_triple" or vname == "structural_hash":
            vfilter = get_vfilter(vname)
            # dedupe_content expects a list of files and returns a list of kept files
            pre_paths = [t[0] for t in triples]  # pre files
            post_paths = [t[1] for t in triples]  # post files
            log_paths = [t[2] for t in triples]  # post files
            log.info(f"[dedupe_content] Starting deduplication with {len(pre_paths)} pre-files and {len(post_paths)} post-files.")

            # Perform deduplication by passing pre files and post files separately
            kept_pre_files = set(vfilter(pre_paths))  # deduplicate based on pre files
            kept_post_files = set(vfilter(post_paths))  # deduplicate based on post files
            kept_log_files = set(vfilter(log_paths))  # deduplicate based on post files
            log.info(f"[dedupe_content] Kept {len(kept_pre_files)} pre-files and {len(kept_post_files)} post-files after deduplication.")

            # Keep triples where both pre-file and post-file are in kept_pre_files and kept_post_files
            filtered_triples = [t for t in triples if t[0] in kept_pre_files and t[1] in kept_post_files and t[2] in kept_log_files]
            log.info(f"[dedupe_content] After filtering: {len(filtered_triples)} triples remain.")

            triples = filtered_triples
            log.info(f"[dedupe_content] Final kept {len(triples)} files after deduplication")
        else:
            # Filter pre-files in parallel
            pre_paths = [t[0] for t in triples]
            pre_keeps = parallel_map(
                apply_vfilter_worker,
                [(p, vname, args.token_limit) for p in pre_paths],
                desc=f"Vertical filtering pre {vname}"
            )
            # Filter post-files in parallel
            post_paths = [t[1] for t in triples]
            post_keeps = parallel_map(
                apply_vfilter_worker,
                [(p, vname, args.token_limit) for p in post_paths],
                desc=f"Vertical filtering post {vname}"
            )
            # Keep triples where both pre and post passed
            triples = [
                t for t, keep_pre, keep_post in zip(triples, pre_keeps, post_keeps)
                if keep_pre and keep_post
            ]
            log.info(f"After vertical filter '{vname}': {len(triples)}/{before}")

    log.info("Moving to Final dir")
    # Copy filtered triples
    os.makedirs(args.out_dir, exist_ok=True)
    parallel_map(
        copy_one_worker,
        [(triple, args.out_dir) for triple in triples],
        desc="Copying filtered triples"
    )
    log.info(f"Filtered triples copied to {args.out_dir}")

    # Dataset creation
    if args.make_dataset:
        if not args.dataset_output:
            log.error("--dataset-output is required when using --make-dataset")
            return
        log.info("Building dataset from final triples...")

        rec_triples = collect_triples(args.out_dir)
        train, test, valid = split_triples(rec_triples,
                                           args.train_size,
                                           args.test_size,
                                           args.valid_size,
                                           args.seed)

        # Build Dataset objects per split
        ds_dict = DatasetDict({
            'train': Dataset.from_list([
                {
                    'pre_ir': load_file(pre_path),
                    'opt_ir': load_file(post_path),
                    'log': load_file(log_path),
                    'prompt': make_prompt(
                        load_file(pre_path),
                        load_file(post_path),
                        load_file(log_path),
                        args.prompt_template
                    )
                }
                for pre_path, post_path, log_path in train
            ]),
            'test': Dataset.from_list([
                {
                    'pre_ir': load_file(pre_path),
                    'opt_ir': load_file(post_path),
                    'log': load_file(log_path),
                    'prompt': make_prompt(
                        load_file(pre_path),
                        load_file(post_path),
                        load_file(log_path),
                        args.prompt_template
                    )
                }
                for pre_path, post_path, log_path in test
            ]),
            'valid': Dataset.from_list([
                {
                    'pre_ir': load_file(pre_path),
                    'opt_ir': load_file(post_path),
                    'log': load_file(log_path),
                    'prompt': make_prompt(
                        load_file(pre_path),
                        load_file(post_path),
                        load_file(log_path),
                        args.prompt_template
                    )
                }
                for pre_path, post_path, log_path in valid
            ]),
        })
        # Save all splits to disk
        ds_dict.save_to_disk(args.dataset_output)
        log.info(f"DatasetDict saved to {args.dataset_output}")

if __name__ == '__main__':
    main()