# cli.py

import argparse
import os
import shlex
import shutil
from core.llvm.clang import ClangCompiler
from core.llvm.opt import OptOptimizer
from core.preprocessing.ir_preprocessor import IRPreprocessor
from core.llvm.llvm_extract import LLVMExtractFunctions
from utils import logger
from utils.random import RandomGenerator

log = logger.logger()


# Make extractor and extract_one pickleable for multiprocessing
extractor = LLVMExtractFunctions()
def extract_one(args):
    llpath, extract_dir = args
    extractor.extract_functions(llpath, extract_dir)

def main():
    parser = argparse.ArgumentParser(description="LLVM Toolchain CLI: clang & opt")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # clang subcommand
    clang_p = subparsers.add_parser("clang", help="Compile source files with clang")
    clang_p.add_argument("--source-dir", required=True, help="Directory containing source files")
    clang_p.add_argument("--output-dir", required=True, help="Directory for compiled objects/IR")
    clang_p.add_argument("--ext", required=True, help="Source file extension (e.g. .c, .cpp)")
    clang_p.add_argument("--flags", type=str, required=True,
                         help="Flags passed to clang (e.g. -S -emit-llvm -O3)")

    # opt subcommand
    opt_p = subparsers.add_parser("opt", help="Optimize LLVM IR files with opt")
    opt_p.add_argument("--input-dir", required=True, help="Directory containing IR files (.ll/.bc)")
    opt_p.add_argument("--output-dir", required=True, help="Directory for optimized IR")
    opt_p.add_argument("--flags", type=str, required=True,
                       help="Flags passed to opt (e.g. -O3 -mem2reg)")

    # pipeline subcommand
    pipeline_p = subparsers.add_parser("pipeline", help="Run clang and opt in sequence")
    pipeline_p.add_argument("--source-dir", required=False, help="Directory containing source files")
    pipeline_p.add_argument("--ir-dir", required=False, help="Directory containing IR files (.ll)")

    # Conditional required arguments
    # If --ir-dir is provided, then --ext and --clang-flags are not required
    # Otherwise, they are required

    # First add all arguments without required flag
    pipeline_p.add_argument("--compile-out", required=False, help="Directory for clang outputs")
    pipeline_p.add_argument("--opt-out", required=True, help="Directory for opt outputs")
    pipeline_p.add_argument("--ext", required=False, help="Source file extension (e.g. .c, .cpp)")
    pipeline_p.add_argument("--clang-flags", type=str, required=False,
                            help="Flags passed to clang (e.g. -S -emit-llvm -O3)")
    pipeline_p.add_argument("--opt-flags", type=str, required=True,
                            help="Flags passed to opt (e.g. -O3 -mem2reg)")
    pipeline_p.add_argument("--rules", nargs='+', default=None,
                            help="Preprocess rules to apply to IR files")
    pipeline_p.add_argument("--where", choices=['pre', 'post', 'both', 'log', 'all'], default='both',
                            help="Where to apply preprocessing: 'pre' (compile-out), 'post' (opt-out), or 'both'")
    pipeline_p.add_argument("--pre-out", required=False, help="Directory for preprocessed IR before optimization")
    pipeline_p.add_argument("--post-out", required=False, help="Directory for preprocessed IR after optimization")
    pipeline_p.add_argument("--log-out", required=False, help="Directory for preprocessed Logs after optimization")
    pipeline_p.add_argument("--extract-dir", required=False,
                            help="Directory for per-function extraction IR files")
    pipeline_p.add_argument('--sample-size', type=int, default=None,
                            help='Optionally randomly sample this many source files before processing')
    pipeline_p.add_argument('--seed', type=int, default=None,
                            help='Random seed for sampling source files')

    args = parser.parse_args()

    # After parsing, enforce required arguments conditionally
    if args.command == "pipeline":
        if args.ir_dir:
            # when --ir-dir is provided, --ext and --clang-flags should not be required
            pass
        else:
            # when --ir-dir is not provided, --ext and --clang-flags are required
            if not args.ext:
                log.error("--ext is required when --ir-dir is not provided")
                return
            if not args.clang_flags:
                log.error("--clang-flags is required when --ir-dir is not provided")
                return

    if args.command == "clang":
        # Collect source files by extension
        sources = []
        for root, _, files in os.walk(args.source_dir):
            for f in files:
                if f.endswith(args.ext):
                    sources.append(os.path.join(root, f))
        if not sources:
            log.error("No source files found matching extension %s", args.ext)
            return
        compiler = ClangCompiler()
        clang_flags = shlex.split(args.flags)
        compiler.compile(sources, args.output_dir, flags=clang_flags)

    elif args.command == "opt":
        # Collect IR files
        inputs = []
        for root, _, files in os.walk(args.input_dir):
            for f in files:
                if f.endswith('.ll') or f.endswith('.bc'):
                    inputs.append(os.path.join(root, f))
        if not inputs:
            log.error("No IR files found in %s", args.input_dir)
            return
        optimizer = OptOptimizer()
        opt_flags = shlex.split(args.flags)
        optimizer.optimize(inputs, args.output_dir, flags=opt_flags)

    if args.command == "pipeline":
    # Clean output directories before running pipeline
        if args.compile_out:
            for d in [args.compile_out, args.extract_dir, args.opt_out]:
                if os.path.isdir(d):
                    shutil.rmtree(d)
                os.makedirs(d, exist_ok=True)
        else:
            for d in [args.compile_out, args.extract_dir, args.opt_out]:
                if os.path.isdir(d):
                    shutil.rmtree(d)
                os.makedirs(d, exist_ok=True)         

    # Also clean pre-out and post-out if provided
    if args.pre_out:
        if os.path.isdir(args.pre_out): shutil.rmtree(args.pre_out)
        os.makedirs(args.pre_out, exist_ok=True)
    if args.post_out:
        if os.path.isdir(args.post_out): shutil.rmtree(args.post_out)
        os.makedirs(args.post_out, exist_ok=True)

    # Check if we are processing source files or IR files
    if args.ir_dir:
        # Collect IR files directly from the provided IR directory
        ir_files = []
        for root, _, files in os.walk(args.ir_dir):
            for f in files:
                if f.endswith('.ll'):
                    ir_files.append(os.path.join(root, f))
        if not ir_files:
            log.error("No IR files found in %s", args.ir_dir)
            return

        # Optionally sample a subset of IR files
        if args.sample_size is not None:
            rng = RandomGenerator(args.seed)
            if args.sample_size > len(ir_files):
                log.error(f"Requested sample-size {args.sample_size} > available IR files {len(ir_files)}")
                return
            # sample without replacement
            ir_files = rng._random.sample(ir_files, args.sample_size)
            log.info(f"Randomly sampled {len(ir_files)} IR files from {args.ir_dir}")

        log.info(f"Processing IR files directly from {args.ir_dir}")

        # Skip the clang steps as we're working with IR files directly
        compiler = None
        clang_flags = []

        # Copy sampled IR files to compile-out directory before extracting functions
        if args.compile_out:
            os.makedirs(args.compile_out, exist_ok=True)
            for ir_file in ir_files:
                dest_path = os.path.join(args.compile_out, os.path.basename(ir_file))
                shutil.copy2(ir_file, dest_path)

    else:
        # Collect source files by extension
        sources = []
        for root, _, files in os.walk(args.source_dir):
            for f in files:
                if f.endswith(args.ext):
                    sources.append(os.path.join(root, f))
        if not sources:
            log.error(f"No source files found matching extension {args.ext}")
            return

        # Optionally sample a subset of source files
        if args.sample_size is not None:
            rng = RandomGenerator(args.seed)
            if args.sample_size > len(sources):
                log.error(f"Requested sample-size {args.sample_size} > available sources {len(sources)}")
                return
            # sample without replacement
            sources = rng._random.sample(sources, args.sample_size)
            log.info(f"Randomly sampled {len(sources)} source files for pipeline")

        compiler = ClangCompiler()
        clang_flags = shlex.split(args.clang_flags) if args.clang_flags else []

    if compiler:
        compiler.compile(sources, args.compile_out, flags=clang_flags)

    from utils.parallel import parallel_map

    # Determine source directory for optimization IR files
    if args.extract_dir:
        # Perform per-function extraction
        os.makedirs(args.extract_dir, exist_ok=True)
        ll_files = []
        for root, _, files in os.walk(args.compile_out):
            for fname in files:
                if fname.endswith('.ll'):
                    llpath = os.path.join(root, fname)
                    ll_files.append((llpath, args.extract_dir))
        parallel_map(extract_one, ll_files, desc="Extracting functions")
        ir_source_dir = args.extract_dir
    else:
        # Skip extraction, use compile output directly
        ir_source_dir = args.compile_out

    # Collect IR files for optimization
    ir_files = []
    for root, _, files in os.walk(ir_source_dir):
        for f in files:
            if f.endswith('.ll'):
                ir_files.append(os.path.join(root, f))
    if not ir_files:
        log.error(f"No IR files found in {ir_source_dir}")
        return

    # Apply preprocessing if requested
    ir_pre = IRPreprocessor(rules=args.rules) if args.rules else None
    ir_files_for_opt = ir_files
    if ir_pre and args.where in ('pre', 'both', 'all'):
        pre_out_dir = args.pre_out or args.compile_out or ir_source_dir
        os.makedirs(pre_out_dir, exist_ok=True)
        ir_pre.process(ir_files, pre_out_dir)
        ir_files_for_opt = [
            os.path.join(pre_out_dir, os.path.basename(path))
            for path in ir_files
        ]

    # Optimization
    optimizer = OptOptimizer()
    opt_flags = shlex.split(args.opt_flags)
    opt_outputs = optimizer.optimize(ir_files_for_opt, args.opt_out, flags=opt_flags)

    # Conditional preprocessing after full pipeline
    if args.rules:
        ir_pre = IRPreprocessor(rules=args.rules)
        if args.where in ('pre', 'both', 'all'):
            pass 
        if args.where in ('post', 'both', 'all'):
            # process opt-out files
            post_out_dir = args.post_out if args.post_out else args.opt_out
            os.makedirs(post_out_dir, exist_ok=True)
            post_files = []
            for root, _, files in os.walk(args.opt_out):
                for f in files:
                    if f.endswith('.ll') or f.endswith('.bc'):
                        post_files.append(os.path.join(root, f))
            ir_pre.process(post_files, post_out_dir)
        if args.where in ('log', 'all'):
            # process opt-out logs
            log_out_dir = args.log_out
            os.makedirs(log_out_dir, exist_ok=True)
            log_files = []
            for root, _, files in os.walk(args.opt_out):
                for f in files:
                    if f.endswith('.log'):
                        log_files.append(os.path.join(root, f))
            ir_pre.process(log_files, log_out_dir)

if __name__ == "__main__":
    main()