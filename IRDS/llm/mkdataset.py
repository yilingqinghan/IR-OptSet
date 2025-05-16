# File: llm/mkdataset.py

import os
from typing import List, Tuple, Dict
from utils.random import RandomGenerator

def normalize_stem(path: str) -> str:
    base = os.path.basename(path)
    for suf in ('.opt.ll', '.opt.log', '.ll'):
        if base.endswith(suf):
            return base[:-len(suf)]
    return os.path.splitext(base)[0]

def collect_triples(final_dir: str) -> List[Tuple[str, str, str]]:
    """Collect (pre, post, log) triples from a directory."""
    files = os.listdir(final_dir)
    pre_map: Dict[str, str] = {}
    post_map: Dict[str, str] = {}
    log_map: Dict[str, str] = {}
    for f in files:
        p = os.path.join(final_dir, f)
        if f.endswith('.ll') and not f.endswith('.opt.ll'):
            pre_map[normalize_stem(f)] = p
        elif f.endswith('.opt.ll'):
            post_map[normalize_stem(f)] = p
        elif f.endswith('.opt.log'):
            log_map[normalize_stem(f)] = p
    stems = set(pre_map) & set(post_map) & set(log_map)
    return [(pre_map[s], post_map[s], log_map[s]) for s in sorted(stems)]

def split_triples(
    triples: List[Tuple[str, str, str]],
    train_size: int,
    test_size: int,
    valid_size: int,
    seed: int
) -> Tuple[List, List, List]:
    """Split into train/test/valid sets."""
    total = len(triples)
    if train_size + test_size + valid_size > total:
        raise ValueError(f"Requested {train_size+test_size+valid_size} > available {total}")
    rng = RandomGenerator(seed)
    order = list(range(total))
    rng._random.shuffle(order)
    train_idx = order[:train_size]
    test_idx = order[train_size:train_size+test_size]
    valid_idx = order[train_size+test_size:train_size+test_size+valid_size]
    return (
        [triples[i] for i in train_idx],
        [triples[i] for i in test_idx],
        [triples[i] for i in valid_idx],
    )

def load_file(path: str) -> str:
    """Load a text file."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def make_prompt(pre_ir: str, opt_ir: str, log: str, template: str) -> str:
    """Fill in prompt template."""
    return template.format(pre_ir=pre_ir, opt_ir=opt_ir, log=log)