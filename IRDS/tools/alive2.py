import csv
import subprocess
import re
from pathlib import Path
from config.config import ToolchainConfig
from rich.console import Console
import argparse

console = Console()

class IRProcessor:
    """
    A utility class for processing LLVM IR content.
    Provides static methods to clean IR text, extract global sections,
    and extract function definitions from IR files.
    """

    @staticmethod
    def clean_ir_content(ir_content: str) -> str:
        """
        Cleans the given LLVM IR content by removing comments, metadata,
        and irrelevant lines such as source filename and target info.

        Args:
            ir_content (str): The raw LLVM IR content as a string.

        Returns:
            str: The cleaned LLVM IR content.
        """
        cleaned = []
        for line in ir_content.splitlines():
            s = line.strip()
            # Skip comments and metadata lines
            if s.startswith((";", "source_filename", "target datalayout", "target triple")):
                continue
            if s.startswith("!"):
                continue
            # Remove metadata annotations like !dbg or !tbaa
            line = re.sub(r'!\w+\b.*?(?=\s|$)', '', line)
            cleaned.append(line)
        return '\n'.join(cleaned)

    @staticmethod
    def extract_global_section(ir_content: str) -> str:
        """
        Extracts the global declarations section from the LLVM IR content,
        i.e., all lines before the first function definition.

        Args:
            ir_content (str): The cleaned LLVM IR content.

        Returns:
            str: The global declarations section of the IR.
        """
        lines = ir_content.splitlines()
        globals = []
        for line in lines:
            if line.lstrip().startswith('define '):
                break
            globals.append(line)
        return '\n'.join(globals)

    @staticmethod
    def extract_function(ir_content: str) -> str:
        """
        Extracts the first function definition from the LLVM IR content,
        including the function body enclosed in braces.

        Args:
            ir_content (str): The cleaned LLVM IR content.

        Returns:
            str: The extracted function definition including its body.
        """
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
    """
    Runs the Alive2 equivalence checker on a pair of LLVM IR files
    representing pre- and post-optimization code.

    This function:
    - Reads and cleans the IR files.
    - Extracts global declarations and function definitions.
    - Renames the post function if it has the same name as the pre function.
    - Combines the IR parts into a single file.
    - Executes Alive2 with appropriate arguments.
    - Returns any error output from Alive2.

    Args:
        pre_file (Path): Path to the pre-optimization IR file.
        post_file (Path): Path to the post-optimization IR file.
        work_dir (Path): Working directory to save intermediate files.

    Returns:
        str: The stderr output from Alive2, typically empty if successful.
    """
    config = ToolchainConfig()
    alive2 = config.alive2
    # Verify Alive2 executable exists
    if not alive2 or not Path(alive2).exists():
        raise EnvironmentError(f"Alive2 executable not found at {alive2}")
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
    """
    Extracts pairs of pre- and post-optimization LLVM IR code blocks from a file.

    The function removes extraneous tokens and markers, then splits the content
    into pre and post IR sections based on the marker "[/INST]".

    Args:
        path (Path): Path to the file containing IR pairs.

    Returns:
        list of tuples or None: Returns a list with one tuple (pre, post) if successful,
                                or None if the marker is not found or no valid pairs.
    """
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

def process_folder(input_dir: Path, output_dir: Path, suffix: str = '.model.predict.ll', pure: bool=False):
    """
    Processes a folder of predicted LLVM IR files, runs equivalence checking on each,
    and summarizes the results.

    For each file matching the suffix in the input directory:
    - Extracts IR pairs.
    - Saves pre and post IR to separate files.
    - Runs Alive2 equivalence checker.
    - Records success or failure.
    - Writes a CSV summary of all results.

    Args:
        input_dir (Path): Directory containing prediction output files.
        output_dir (Path): Directory to save processed IR and results.
        suffix (str): File suffix to filter prediction files.
        pad (int): Optional denominator for pass rate calculation.
        pure (bool): If True, suppresses detailed logging output.

    Returns:
        tuple: (total processed, number passed, number failed)
    """
    files = sorted(input_dir.glob(f"*{suffix}"))
    if not files:
        console.print(f"[yellow]No files found with suffix '{suffix}' in {input_dir}[/yellow]")
        return 0, 0, 0
    results = []
    total_files = len(files)
    failed = 0

    for file in files:
        pairs = extract_ir_pairs(file)
        if pairs is None:
            failed += 1
            results.append((file.name, 0))
            if not pure:
                console.print(f"[red]{file.name} parsing failed: no code block pair[/red]")
            continue
        pair_success = True
        for idx, (pre, post) in enumerate(pairs, start=1):
            work = output_dir / file.stem / f"pair_{idx}"
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
            results.append((file.name, 1))
        else:
            failed += 1
            results.append((file.name, 0))

    csv_path = output_dir / 'result_summary.csv'
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['filename', 'passed'])
        for fname, res in results:
            writer.writerow([fname, res])

    passed = sum(res for _, res in results)
    failed = total_files - passed

    if not pure:
        console.print(f"\n[bold]Summary:[/] Total files: {total_files}, Passed: {passed}, Failed: {failed}")
        console.print(f"[green]CSV saved to: {csv_path}[/green]")

    return total_files, passed, failed

def main():
    """
    Main entry point for command-line execution.
    Parses arguments, sets up directories, and initiates processing.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', required=True, help='Directory of .model.predict.ll files')
    parser.add_argument('--output-dir', required=True, help='Directory to save IR and combined files')
    parser.add_argument('--pure', action='store_true', help='Suppress logs, output only accuracy and counts')
    parser.add_argument('--suffix', type=str, default='.model.predict.ll', help='Only process files with this suffix')
    # --pad argument removed
    args = parser.parse_args()

    inp = Path(args.input_dir)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    total_files, passed, failed = process_folder(inp, out, suffix=args.suffix, pure=args.pure)
    if args.pure:
        rate_percent = (passed / total_files * 100) if total_files > 0 else 0.0
        print(f"{rate_percent:.3f} {passed} {failed}")

if __name__ == '__main__':
    main()

"""
Example usage:

Assume you have a directory of prediction outputs named `outputs/` where each file is named like `1.model.predict.ll`, `2.model.predict.ll`, ..., and you want to check correctness using Alive2 and save results in `results/`.

You can run:
    python alive2.py --input-dir outputs --output-dir results

To suppress logs and just get a pass rate:
    python alive2.py --input-dir outputs --output-dir results --pure

This tool will:
- Parse each .ll file and extract the pre- and post-optimization IR.
- Clean and prepare the IR for Alive2.
- Run Alive2 equivalence checking.
- Save each IR pair and combined file in results/.
- Output a CSV summarizing which examples passed.
"""