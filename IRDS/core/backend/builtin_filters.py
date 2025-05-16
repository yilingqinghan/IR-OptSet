"""
Built-in filters for backend IR processing.
"""
from typing import List
from .plugin import register_hfilter, register_vfilter
from config.config import ToolchainConfig
import os
from utils import logger
import hashlib
import re
from collections import Counter

log = logger.logger()
os.environ["TOKENIZERS_PARALLELISM"] = "false"

config = ToolchainConfig()

try:
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(config.tokenizer) if config.tokenizer else None
except ImportError:
    tokenizer = None

def clean_lines(section: str) -> str:
    return "\n".join(
        [line.strip() for line in section.splitlines() if line.strip()]  # 忽略空行和多余空格
    )

@register_hfilter('complex_bb')
def complex_bb(pre: str, post: str, log: str) -> bool:
    """
    Match lines in `post` that start with basic block labels like B0:, B1:, etc.
    Return True if there are 3 or more such labels, otherwise False.
    """
    # Use regex to find lines that start with B<number>:
    basic_blocks = re.findall(r'^B\d+:', post, re.MULTILINE)
    return len(basic_blocks) >= 3

@register_hfilter('memssa')
def memssa(pre: str, post: str, log: str) -> bool:
    return len(log.strip().splitlines()) >= 10

@register_hfilter('loops')
def loops(pre: str, post: str, log: str) -> bool:
    return len(log.strip().splitlines()) >= 3

from collections import Counter

@register_hfilter('familiar_pass')
def familiar_pass(pre: str, post: str, log: str) -> bool:
    """
    Return True to keep the (pre, post, log) triplet if:
      - The log content contains no '*** IR Dump Before {pass} on ...' ⇒ keep (not a log).
      - Otherwise, at least one '*** IR Dump After {pass} on ...' occurs ≥9 times ⇒ keep.
      - If any pass in the special_passes list appears in 'After' entries, keep regardless of the count.
      - Else ⇒ filter out (return False).
    """
    AFTER_RE  = re.compile(r"\*\*\* IR Dump After (\w+) on .+ \*\*\*")
    BEFORE_RE = re.compile(r"\*\*\* IR Dump Before (\w+) on .+ \*\*\*")

    # List of passes that we want to keep regardless of count
    special_passes = [
        'ADCEPass', 
        'AggressiveInstCombinePass',
        'BDCEPass',
        'ConstraintEliminationPass',
        'CorrelatedValuePropagationPass',
        'DSEPass',
        'DivRemPairsPass',
        'GVNPass',
        'GlobalDCEPass',
        'InferAlignmentPass',
        'LoopFullUnrollPass',
        'LoopLoadEliminationPass',
        'LoopVectorizePass',
        'MemCpyOptPass',
        'MergedLoadStoreMotionPass',
        'SCCPPass',
        'SLPVectorizerPass',
        'SimpleLoopUnswitchPass',
        'VectorCombinePass'
    ]
    
    # log is already the full content as a string
    content = log

    # If no 'Before' entries, assume it's not really a dump log ⇒ keep
    if not AFTER_RE.search(content):
        return True

    # Count all 'After' passes
    before_passes = BEFORE_RE.findall(content)
    counts = Counter(before_passes)

    # Check if any special pass appears in the 'After' entries
    if any(pass_name in counts for pass_name in special_passes):
        return True

    if sum(counts.values()) >= 9:
        return True
    
    return False
    
@register_hfilter('token_limit_v1')
def token_limit_v1(pre: str, post: str, log: str, limit: int) -> bool:
    """
    Filter out if token count of pre or post exceeds the given limit,
    and also ensure that the combined token count of pre + log is <= limit.
    Additionally, skip files that exceed 1000 lines.
    """
    def count_tokens(text: str) -> int:
        if tokenizer:
            return len(tokenizer.tokenize(text))
        else:
            return len(text.split())

    # Pre-check for line count > 1000 and return False immediately if exceeded
    if len(pre.splitlines()) > 1000:
        return False

    return (
        (count_tokens(pre) + count_tokens(log)) <= limit
    )

@register_hfilter('token_limit_v2')
def token_limit_v2(pre: str, post: str, log: str, limit: int) -> bool:
    """
    Filter out triples if:
    1. Token count of function body in pre or post exceeds `limit`.
    2. Sum of token counts of function bodies in pre + post exceeds 3800.
    
    Only function body (from `define` to matching `}`) is considered.
    """
    def extract_func_body(ir: str) -> str:
        """Extract content between 'define' and matching '}'"""
        func_start = ir.find('define')
        if func_start == -1:
            return ""
        brace_count = 0
        started = False
        body_lines = []

        for line in ir[func_start:].splitlines():
            if '{' in line and not started:
                started = True
                brace_count += line.count('{') - line.count('}')
                body_lines.append(line)
                continue
            if started:
                brace_count += line.count('{') - line.count('}')
                body_lines.append(line)
                if brace_count == 0:
                    break
        return '\n'.join(body_lines)

    def count_tokens(text: str) -> int:
        if tokenizer:
            return len(tokenizer.tokenize(text))
        else:
            return len(text.split())

    pre_func = extract_func_body(pre)
    post_func = extract_func_body(post)

    pre_tokens = count_tokens(pre_func)
    post_tokens = count_tokens(post_func)

    return (
        (pre_tokens + post_tokens) <= 3800
    )
    
@register_hfilter('token_limit_v3')
def token_limit_v3(pre: str, post: str, log: str, limit: int) -> bool:
    """
    Keep only if the token count of pre and post function bodies,
    plus non-function-body sections (e.g., lines starting with % or ! or @),
    excluding the lines starting with '; ModuleID', 'source_filename', 'target datalayout',
    'target triple', and all comments (lines starting with ';'), is <= limit.
    """
    def extract_func_body(ir: str) -> str:
        """Extract content between 'define' and matching '}'"""
        func_start = ir.find('define')
        if func_start == -1:
            return ""
        brace_count = 0
        started = False
        body_lines = []

        for line in ir[func_start:].splitlines():
            if '{' in line and not started:
                started = True
                brace_count += line.count('{') - line.count('}')
                body_lines.append(line)
                continue
            if started:
                brace_count += line.count('{') - line.count('}')
                body_lines.append(line)
                if brace_count == 0:
                    break
        return '\n'.join(body_lines)

    def extract_non_func_body(ir: str) -> str:
        """Extract all lines outside function bodies that are relevant to token count"""
        lines = ir.splitlines()
        non_func_lines = []
        for line in lines:
            stripped = line.strip()
            # Exclude the following:
            # 1. Lines starting with '; ModuleID', 'source_filename', 'target datalayout', 'target triple'
            # 2. Lines starting with ';' (comments)
            if stripped and not (stripped.startswith((
                '; ModuleID', 'source_filename', 'target datalayout', 'target triple')) or
                stripped.startswith(';')):
                # Keep lines that start with % (structs, global variables), ! (metadata), @ (external declarations), and others
                non_func_lines.append(line)
        return '\n'.join(non_func_lines)

    def count_tokens(text: str) -> int:
        """Count tokens in the provided text"""
        if tokenizer:
            return len(tokenizer.tokenize(text))
        else:
            return len(text.split())

    pre_func = extract_func_body(pre)
    post_func = extract_func_body(post)
    pre_non_func = extract_non_func_body(pre)
    post_non_func = extract_non_func_body(post)

    # Calculate the token count for the function bodies and non-function bodies
    pre_tokens = count_tokens(pre_func) + count_tokens(pre_non_func)
    post_tokens = count_tokens(post_func) + count_tokens(post_non_func)

    return (pre_tokens + post_tokens) <= limit

@register_hfilter('token_limit_v4')
def token_limit_v4(pre: str, post: str, log: str, limit: int) -> bool:
    """
    Keep only if the token count of pre and post function bodies,
    plus non-function-body sections (e.g., lines starting with % or ! or @),
    excluding the lines starting with '; ModuleID', 'source_filename', 'target datalayout',
    'target triple', and all comments (lines starting with ';'), is <= limit.
    """
    def extract_func_body(ir: str) -> str:
        """Extract content between 'define' and matching '}'"""
        func_start = ir.find('define')
        if func_start == -1:
            return ""
        brace_count = 0
        started = False
        body_lines = []

        for line in ir[func_start:].splitlines():
            if '{' in line and not started:
                started = True
                brace_count += line.count('{') - line.count('}')
                body_lines.append(line)
                continue
            if started:
                brace_count += line.count('{') - line.count('}')
                body_lines.append(line)
                if brace_count == 0:
                    break
        return '\n'.join(body_lines)

    def extract_non_func_body(ir: str) -> str:
        """Extract all lines outside function bodies that are relevant to token count"""
        lines = ir.splitlines()
        non_func_lines = []
        for line in lines:
            stripped = line.strip()
            # Exclude the following:
            # 1. Lines starting with '; ModuleID', 'source_filename', 'target datalayout', 'target triple'
            # 2. Lines starting with ';' (comments)
            if stripped and not (stripped.startswith((
                '; ModuleID', 'source_filename', 'target datalayout', 'target triple')) or
                stripped.startswith(';')):
                # Keep lines that start with % (structs, global variables), ! (metadata), @ (external declarations), and others
                non_func_lines.append(line)
        return '\n'.join(non_func_lines)

    def count_tokens(text: str) -> int:
        """Count tokens in the provided text"""
        if tokenizer:
            return len(tokenizer.tokenize(text))
        else:
            return len(text.split())

    pre_func = extract_func_body(pre)
    post_func = extract_func_body(post)
    pre_non_func = extract_non_func_body(pre)
    post_non_func = extract_non_func_body(post)

    # Calculate the token count for the function bodies and non-function bodies
    pre_tokens = count_tokens(pre_func) + count_tokens(pre_non_func)
    post_tokens = count_tokens(post_func) + count_tokens(post_non_func)

    return (pre_tokens + post_tokens) >= 1200


@register_hfilter('func_body_changed')
def func_body_changed(pre: str, post: str, log: str) -> bool:
    """
    Keep only if the function body (excluding the 'define' line) has changed between pre- and post-IRs.
    """
    def extract_function_body(ir: str) -> str:
        lines = ir.splitlines()
        body_lines = []
        in_function = False
        brace_depth = 0
        for line in lines:
            stripped = line.strip()
            if not in_function and stripped.startswith('define'):
                in_function = True
                brace_depth += line.count('{') - line.count('}')
                continue  # Skip the define line itself
            if in_function:
                body_lines.append(line)
                brace_depth += line.count('{') - line.count('}')
                if brace_depth == 0:
                    in_function = False
        return "\n".join(body_lines).strip()

    pre_body = extract_function_body(pre)
    post_body = extract_function_body(post)
    return pre_body != post_body

@register_vfilter('keep_core')
def keep_core(paths: List[str]) -> List[str]:
    """
    Removes lines starting with ';', 'source_filename', 'target datalayout', or 'target triple'
    from .ll files. Keeps all other content unchanged.

    Returns the list of processed file paths (overwriting original files).
    """
    HEADER_PREFIXES = (
        ';',
        'source_filename',
        'target datalayout',
        'target triple',
    )

    def clean_lines(content: str) -> str:
        return "\n".join(
            line for line in content.splitlines()
            if not any(line.strip().startswith(prefix) for prefix in HEADER_PREFIXES)
        )

    result = []
    for p in paths:
        if not p.endswith('.ll'):
            result.append(p)
            continue
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read()
        cleaned = clean_lines(content)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        result.append(p)

    return result

@register_vfilter('structural_hash')
def structural_hash(paths: List[str]) -> List[str]:
    """
    Deduplicates files based on the extracted structural hash (e.g., 'Module Hash').
    This filter ensures that only one file with a unique structural hash is kept.
    Files with identical structural hashes are considered duplicates and will be removed.

    Args:
        paths (List[str]): A list of file paths to be processed.

    Returns:
        List[str]: A list of file paths that are kept after deduplication based on structural hash.
    """
    # Regular expression to match the 'Module Hash' line and capture the hash value
    MODULE_HASH_RE = re.compile(r"Module Hash:\s*([0-9a-fA-F]+)")
    
    seen_hashes = set()  # Set to track structural hashes that have been encountered
    result = []  # List to store the paths of files to be kept

    for path in paths:
        # Process only '.log' files, skip others
        if not path.endswith('.log'):
            return paths

        try:
            # Read the content of the file
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Search for the 'Module Hash' in the file content
            match = re.search(MODULE_HASH_RE, content)
            if match:
                module_hash = match.group(1)  # Extract the structural hash value
                if module_hash not in seen_hashes:
                    # If the hash is not seen before, add the file path to the result
                    seen_hashes.add(module_hash)
                    result.append(path)
        except Exception as e:
            # Log error if there is an issue processing the file
            log.error(f"[structural_hash] Failed processing {path}: {e}")

    # Return the list of files that have unique structural hashes
    return result
    

@register_vfilter('dedupe_content')
def dedupe_content(paths: List[str]) -> List[str]:
    """
    Keep first file for each unique *set of function bodies* (ignores define/} lines
    and whitespace).
    """
    seen = set()
    result = []

    def all_function_bodies(ir: str) -> str:
        bodies, cur, depth = [], [], 0
        for line in ir.splitlines():
            if line.strip().startswith('define'):
                depth = line.count('{') - line.count('}')
                cur = []
                continue
            elif depth > 0:
                depth += line.count('{') - line.count('}')
                if depth == 0:
                    bodies.append('\n'.join(cur).strip())
                else:
                    cur.append(line.strip())
        return '\n'.join(bodies)

    for p in paths:
        if not p.endswith('.ll'):
            result.append(p)
            continue
        with open(p, 'r', encoding='utf-8') as f:
            func_text = all_function_bodies(f.read())
        if not func_text:
            result.append(p)
            continue
        digest = hashlib.md5(func_text.encode()).hexdigest()
        if digest not in seen:
            seen.add(digest)
            result.append(p)

    log.info(f"[dedupe_content] kept {len(result)} / {len(paths)} files after dedup")
    return result

@register_vfilter('func_only')
def func_only(paths: List[str]) -> List[str]:
    """
    For each .ll file, keep only the function bodies (from 'define' to the matching '}').
    Non-.ll files are kept unchanged.

    Returns the list of processed file paths (overwriting original files).
    """
    def extract_functions(content: str) -> str:
        lines = content.splitlines()
        in_function = False
        result = []
        brace_depth = 0

        for line in lines:
            stripped = line.strip()
            if not in_function and stripped.startswith('define'):
                in_function = True
                brace_depth = line.count('{') - line.count('}')
                result.append(line)
            elif in_function:
                result.append(line)
                brace_depth += line.count('{') - line.count('}')
                if brace_depth == 0:
                    in_function = False

        return "\n".join(result)

    result = []
    for p in paths:
        if not p.endswith('.ll'):
            result.append(p)
            continue
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read()
        processed = extract_functions(content)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(processed)
        result.append(p)

    return result

@register_vfilter('strip_header_comments')
def strip_header_comments(paths: List[str]) -> List[str]:
    """
    Remove LLVM header lines and full‑line comments from every `.ll` file, in place.

    * Lines dropped completely if they start with one of:
        - '; ModuleID'
        - 'source_filename'
        - 'target datalayout'
        - 'target triple'
        - ';'   (any full‑line comment)

    The function rewrites the files on disk and returns the list of paths.
    Non‑`.ll` files are passed through unchanged.
    """
    HEADER_PREFIXES = (
        '; ModuleID',
        'source_filename',
        'target datalayout',
        'target triple',
    )

    kept: List[str] = []
    for path in paths:
        if not path.endswith('.ll'):
            kept.append(path)
            continue

        try:
            with open(path, 'r', encoding='utf-8') as f:
                new_lines = []
                for ln in f:
                    stripped = ln.lstrip()
                    # Skip full‑line comment or unwanted header
                    if stripped.startswith(';'):
                        continue
                    if any(stripped.startswith(pref) for pref in HEADER_PREFIXES):
                        continue
                    new_lines.append(ln.rstrip('\n'))
            with open(path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            kept.append(path)
        except Exception as e:
            log.error(f"[strip_header_comments] Failed processing {path}: {e}")

    log.info(f"[strip_header_comments] processed {len(kept)} files")
    return kept

@register_vfilter('token_limit_vfilter')
def token_limit_vfilter(paths: List[str], limit: int = 1800) -> List[str]:
    def count_tokens(text: str) -> int:
        if tokenizer:
            return len(tokenizer.tokenize(text))
        else:
            return len(text.split())

    pre_files = [p for p in paths if p.endswith('.ll') and not p.endswith('.opt.ll')]
    post_files = [p for p in paths if p.endswith('.opt.ll')]
    log_files = [p for p in paths if p.endswith('.log')]

    def get_base(p):
        return os.path.basename(p).split('.')[0]

    kept = set()
    for pre in pre_files:
        base = get_base(pre)
        post = next((p for p in post_files if get_base(p) == base), None)
        logf = next((l for l in log_files if get_base(l) == base), None)
        if not post or not logf:
            log.warning(f"[token_limit_vfilter] Missing post or log for {pre}")
            continue

        with open(pre, 'r', encoding='utf-8') as f:
            pre_text = f.read()
        with open(post, 'r', encoding='utf-8') as f:
            post_text = f.read()

        pre_tokens = count_tokens(pre_text)
        post_tokens = count_tokens(post_text)

        if pre_tokens > limit:
            log.warning(f"[token_limit_vfilter] Pre too long: {pre_tokens} tokens in {pre}")
            continue
        if post_tokens > limit:
            log.warning(f"[token_limit_vfilter] Post too long: {post_tokens} tokens in {post}")
            continue

        kept.add(pre)
        kept.add(post)
        kept.add(logf)
        log.warning(f"[token_limit_vfilter] Kept {pre}")

    return [p for p in paths if p in kept]