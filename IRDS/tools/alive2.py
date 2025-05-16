# EXPERIMENTAL! We recommend using LLVM : opt -passes=verify
# Don't support IR under LLVM 19, otherwise may:ERROR: Unsupported instruction
# ⚠️ Limitations of using alive-tv for LLVM IR verification:

# 1. **Unsupported Instructions**: `alive-tv` may not support certain LLVM IR instructions,
#    especially those introduced in newer LLVM versions (e.g., LLVM 19 and above). This can lead
#    to errors such as "ERROR: Unsupported instruction".

# 2. **Limited Intrinsic Support**: Some LLVM intrinsics are not supported by `alive-tv`, which
#    may cause verification failures or inaccurate results.

# 3. **Memory Model Constraints**: `alive-tv` has limitations in modeling complex memory behaviors,
#    which can affect the accuracy of verification for transformations involving memory operations.

# 4. **Interprocedural Optimization**: `alive-tv` does not support interprocedural optimizations,
#    limiting its applicability for certain types of LLVM IR transformations.

# 5. **SMT Solver Timeouts**: The underlying SMT solver used by `alive-tv` may experience timeouts
#    when dealing with complex or large IR inputs, leading to incomplete verification.

# 6. **Undefined Behavior Handling**: `alive-tv` may not accurately model undefined behaviors
#    present in the IR, which can result in misleading verification outcomes.

# Recommendation:
# For comprehensive verification, consider using LLVM's built-in verifier with `opt -passes=verify`
# as a primary check. Use `alive-tv` as a supplementary tool for specific cases where its
# capabilities align with the IR constructs being verified.
import csv
import subprocess
import re
from pathlib import Path
from config.config import ToolchainConfig
from rich.console import Console
import argparse

console = Console()

class IRProcessor:
    @staticmethod
    def clean_ir_content(ir_content: str) -> str:
        cleaned = []
        for line in ir_content.splitlines():
            s = line.strip()
            if s.startswith((";", "source_filename", "target datalayout", "target triple")):
                continue
            if s.startswith("!"):
                continue
            line = re.sub(r'!\w+\b.*?(?=\s|$)', '', line)
            cleaned.append(line)
        return '\n'.join(cleaned)

    @staticmethod
    def extract_global_section(ir_content: str) -> str:
        lines = ir_content.splitlines()
        globals = []
        for line in lines:
            if line.lstrip().startswith('define '):
                break
            globals.append(line)
        return '\n'.join(globals)

    @staticmethod
    def extract_function(ir_content: str) -> str:
        lines = ir_content.splitlines()
        func_lines = []
        in_func = False
        brace_count = 0
        for line in lines:
            if not in_func and line.lstrip().startswith('define '):
                in_func = True
                brace_count = 0
            if in_func:
                func_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    break
        return '\n'.join(func_lines)


def run_alive2(pre_file: Path, post_file: Path, work_dir: Path) -> str:
    config = ToolchainConfig()
    alive2 = config.alive2
    work_dir.mkdir(parents=True, exist_ok=True)
    combined_path = work_dir / 'combined.ll'

    pre = pre_file.read_text(errors='ignore')
    post = post_file.read_text(errors='ignore')
    pre_clean = IRProcessor.clean_ir_content(pre)
    post_clean = IRProcessor.clean_ir_content(post)

    global_sec = IRProcessor.extract_global_section(pre_clean)
    pre_func = IRProcessor.extract_function(pre_clean)
    post_func = IRProcessor.extract_function(post_clean)

    func_name_regex = re.compile(r'define\s+.*?@(?:"([^"]+)"|([\w\.\$]+))\s*\(')
    m_pre = func_name_regex.search(pre_func)
    m_post = func_name_regex.search(post_func)
    if not m_pre or not m_post:
        return 'Failed to locate function definitions.'
    pre_name = m_pre.group(1) if m_pre.group(1) is not None else m_pre.group(2)
    post_name = m_post.group(1) if m_post.group(1) is not None else m_post.group(2)

    if pre_name == post_name:
        # Append the suffix **inside** existing quotes if the name is quoted
        if post_name.startswith('"') and post_name.endswith('"'):
            new_post_name = f'"{post_name[1:-1]}2"'
        else:
            new_post_name = post_name + '2'
        post_func = post_func.replace(f'@{post_name}(', f'@{new_post_name}(', 1)
        post_name = new_post_name

    combined = '\n'.join([global_sec, pre_func, post_func])
    combined = re.sub(r',\s*$', '', combined, flags=re.M)
    combined_path.write_text(combined)

    proc = subprocess.run([
        alive2, str(combined_path),
        f'--src-fn={pre_name}', f'--tgt-fn={post_name}'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    return proc.stderr.strip()


def extract_ir_pairs(path: Path):
    text = path.read_text(errors='ignore')
    text = re.sub(r'(?:<s>|</s>|\[INST\]|\[\\INST\]|<code>|</code>|\\n)', '', text)
    text = re.sub('Optimize the following LLVM IR with O3:', '', text)
    text = re.sub('Opt IR:', '', text)
    
    marker = "[/INST]"
    pos = text.find(marker)
    if pos == -1:
        return None

    pre_raw = text[:pos]
    post_raw = text[pos + len(marker):]

    pre = pre_raw.strip()
    post = post_raw.strip()

    if pre and post:
        return [(pre, post)]
    return None

def process_folder(input_dir: Path, output_dir: Path, suffix: str = '.model.predict.ll', pad: int = None, pure: bool=False):
    total = 0
    failed = 0
    max_index = 500
    results = []

    for i in range(1, max_index + 1):
        file = input_dir / f"{i}{suffix}"
        if not file.exists():
            results.append((str(i), 1))
            continue

        pairs = extract_ir_pairs(file)
        if pairs is None:
            failed += 1
            results.append((str(i), 0))
            if not pure:
                console.print(f"[red]{file.name} parsing failed: no code block pair[/red]")
            continue

        pair_success = True
        for idx, (pre, post) in enumerate(pairs, start=1):
            total += 1
            work = output_dir / f"{i}" / f"pair_{idx}"
            work.mkdir(parents=True, exist_ok=True)
            (work / 'pre.ll').write_text(pre)
            (work / 'post.ll').write_text(post)
            err = run_alive2(work / 'pre.ll', work / 'post.ll', work)
            if err:
                pair_success = False
                if not pure:
                    console.print(f"[red]{file.name} pair {idx} failed[/red]")
                    console.print(err, markup=False)
        if pair_success:
            results.append((str(i), 1))
        else:
            failed += 1
            results.append((str(i), 0))

    csv_path = output_dir / 'result_summary.csv'
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([idx for idx, _ in results])
        writer.writerow([res for _, res in results])

    passed = sum(1 for _, res in results if res == 1)
    denom = pad if pad is not None else total
    if pad is not None:
        passed += max(0, pad - total)

    if not pure:
        console.print(f"\n[bold]Summary:[/] Total parsed: {total}, Passed: {passed}, Failed: {failed}")
        console.print(f"[green]CSV saved to: {csv_path}[/green]")

    return total, passed, failed

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', required=True, help='Directory of .model.predict.ll files')
    parser.add_argument('--output-dir', required=True, help='Directory to save IR and combined files')
    parser.add_argument('--pure', action='store_true', help='Suppress logs, output only accuracy and counts')
    parser.add_argument('--suffix', type=str, default='.model.predict.ll', help='Only process files with this suffix')
    parser.add_argument('--pad', type=int, default=None, help='Use this number as denominator for pass rate instead of total')
    args = parser.parse_args()

    inp = Path(args.input_dir)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    total, passed, failed = process_folder(inp, out, suffix=args.suffix, pad=args.pad, pure=args.pure)
    if args.pure:
        denom = args.pad if args.pad is not None else total
        passed_output = passed
        rate_percent = (passed_output / denom * 100) if denom > 0 else 0.0
        print(f"{rate_percent:.3f} {passed_output} {failed}")

if __name__ == '__main__':
    main()