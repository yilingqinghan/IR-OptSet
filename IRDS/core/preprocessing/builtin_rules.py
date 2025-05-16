from .plugin import register_rule
import re

@register_rule('strip_all')
def strip_all(text: str) -> str:
    """Strip whitespace at ends of every line."""
    if "define " not in text:
        return text
    lines = text.splitlines()
    stripped_lines = [line.strip() for line in lines]
    return "\n".join(stripped_lines)

@register_rule('filter_header')
def filter_header(text: str) -> str:
    """Remove source_filename, datalayout and triple lines."""
    if "define " not in text:
        return text
    lines = text.splitlines()
    filtered = [
        line for line in lines
        if not (
            line.lstrip().startswith("source_filename") or
            line.lstrip().startswith("target datalayout") or
            line.lstrip().startswith("target triple")
        )
    ]
    return "\n".join(filtered)

@register_rule('clean_metadata')
def clean_metadata(text: str) -> str:
    """Remove metadata entries like !123 and lines starting with !."""
    if "define " not in text:
        return text
    lines = text.splitlines()
    cleaned = []
    pattern = re.compile(r'\s*![\w.]*\s*!?\d+')
    for line in lines:
        if line.lstrip().startswith('!'):
            continue
        ln = pattern.sub('', line)
        cleaned.append(ln.rstrip())
    return "\n".join(cleaned)

@register_rule('filter_globals')
def filter_globals(text: str) -> str:
    """Remove lines starting with '@' (global definitions)."""
    if "define " not in text:
        return text
    lines = text.splitlines()
    filtered = [line for line in lines if not line.lstrip().startswith("@")]
    return "\n".join(filtered)

@register_rule('remove_blank')
def remove_blank(text: str) -> str:
    """Remove blank lines."""
    if "define " not in text:
        return text
    lines = text.splitlines()
    non_blank = [line for line in lines if line.strip()]
    return "\n".join(non_blank)

@register_rule('filter_declare')
def filter_declare(text: str) -> str:
    """Remove lines beginning with 'declare'."""
    if "define " not in text:
        return text
    lines = text.splitlines()
    filtered = [line for line in lines if not line.lstrip().startswith("declare")]
    return "\n".join(filtered)

@register_rule('complex_clean')
def complex_clean(text: str) -> str:
    """Remove dbg/meta keywords, debug intrinsics and comments."""
    if "define " not in text:
        return text
    lines = text.splitlines()
    out = []
    for line in lines:
        if line.lstrip().startswith(';') or re.match(r'^\s*#dbg_', line):
            continue
        if ';' in line:
            line = line.split(';', 1)[0]
        if any(k in line for k in ['dbg', 'prev', 'succ']):
            continue
        out.append(line.rstrip())
    return "\n".join(out)

# Some IRs have hidden blocks' defs
@register_rule('ensure_entry_block')
def ensure_entry_block(text: str) -> str:
    """
    Ensure that the first block after a function definition has a label.
    If the line immediately following 'define ...' is not a basic block label (e.g., 'label:'),
    insert a block label '<N>:' where N = max(param_indices)+1 or 0 if no numeric params.
    """
    if "define " not in text:
        return text

    import re
    lines = text.splitlines()
    output = []
    for idx, line in enumerate(lines):
        output.append(line)
        if line.strip().startswith("define"):
            params_part = ""
            m = re.search(r"\((.*)\)", line)
            if m:
                params_part = m.group(1)
            nums = [int(n) for n in re.findall(r"%(\d+)", params_part)]
            label_index = max(nums) + 1 if nums else 0

            j = idx + 1
            while j < len(lines) and not lines[j].strip():
                output.append(lines[j])
                j += 1

            if j < len(lines):
                nxt = lines[j]
                if not re.match(r'^\s*[\w\.\$\-]+:\s*$', nxt):
                    output.append(f"{label_index}:")
    return "\n".join(output)

# FIXME: only allow removal in function body, otherwise it will remove metadata, .etc
@register_rule('remove_comments')
def remove_comments(text: str) -> str:
    """Strip inline comments and comment lines *only inside function bodies*."""
    if "define " not in text:
        return text

    lines = text.splitlines()
    out = []

    in_func = False

    for line in lines:
        stripped = line.strip()
        # detect function start
        if stripped.startswith("define"):
            in_func = True
            out.append(line)
            continue

        # detect function end
        if stripped == "}":
            in_func = False
            out.append(line)
            continue

        if in_func:
            # inside function, strip comments
            if stripped.startswith(";"):
                continue
            if ";" in line:
                line = line.split(';', 1)[0]
            out.append(line.rstrip())
        else:
            # outside function, keep intact
            out.append(line)

    return "\n".join(out)

@register_rule('filter_attributes')
def filter_attributes(text: str) -> str:
    """Remove lines beginning with 'attributes #'."""
    if "define " not in text:
        return text
    lines = text.splitlines()
    filtered = [line for line in lines if not line.lstrip().startswith("attributes #")]
    return "\n".join(filtered)

@register_rule('clean_align')
def clean_align(text: str) -> str:
    """Remove 'align N' specifications."""
    if "define " not in text:
        return text
    lines = text.splitlines()
    out = []
    pattern = re.compile(r'\s*align\s+\d+\s*,?')
    for line in lines:
        ln = pattern.sub('', line).rstrip().rstrip(',')
        out.append(ln)
    return "\n".join(out)

# FIXME: Failed when meeting complex IR
@register_rule('sort_phi')
def sort_phi(text: str) -> str:
    """Sort phi instruction incoming blocks by constant and variable order."""
    if "define " not in text:
        return text
    # Helper functions
    def is_constant(value):
        return (value.isdigit() or
                (value.startswith("-") and value[1:].isdigit()) or
                value.startswith("@") or
                value.lower() in {"true", "false", "null", "undef"})
    def constant_sort_key(value):
        if value.lower() in {"undef", "null"}:
            return float('-inf')
        if value.startswith("-") and value[1:].isdigit():
            return int(value)
        if value.isdigit():
            return int(value)
        return float('inf')
    def extract_variable_value(val):
        if val.startswith("%") and val[1:].isdigit():
            return int(val[1:])
        return float('inf')
    def sort_phi_blocks(match):
        var, typ, blocks = match.group(1), match.group(2), match.group(3)
        items = re.findall(r"\[\s*([^,]+)\s*,\s*([^\]]+)\s*\]", blocks)
        sorted_items = sorted(
            items,
            key=lambda x: (
                not is_constant(x[0]),
                constant_sort_key(x[0]) if is_constant(x[0]) else float('inf'),
                extract_variable_value(x[0]) if not is_constant(x[0]) else 0
            )
        )
        s = ", ".join(f"[ {v}, {b}]" for v,b in sorted_items)
        return f"{var} = phi {typ} {s}\n"
    phi_pat = re.compile(r"(\%\w+)\s*=\s*phi\s+(\w+)\s+((?:\[.*?\],?\s*)+)")
    return phi_pat.sub(sort_phi_blocks, text)

@register_rule('process_functions')
def process_functions(text: str) -> str:
    """Identify and process each function block as a unit."""
    if "define " not in text:
        return text
    lines = text.splitlines()
    output = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip().startswith('define'):
            output.append(line)
            i += 1
            continue
        block = []
        while i < len(lines):
            block.append(lines[i])
            if lines[i].strip() == '}':
                break
            i += 1
        # Placeholder: could call another transform on block
        output.extend(block)
        i += 1
    return "\n".join(output)

@register_rule('rename_functions')
def rename_functions(text: str) -> str:
    """Rename function definitions to @FUNC0, @FUNC1, ..."""
    if "define " not in text:
        return text
    lines = text.splitlines()
    count = 0
    out = []
    for line in lines:
        s = line.strip()
        if s.startswith('define'):
            at = s.find('@')
            lp = s.find('(', at)
            if at != -1 and lp != -1:
                new = f"define @FUNC{count}" + s[lp:]
                out.append(new)
                count += 1
                continue
        out.append(line)
    return "\n".join(out)

@register_rule('rename_locals')
def rename_locals(text: str) -> str:
    """
    Uniformly rename local variables to %0, %1, ... within each function,
    but skip any names starting with %STRUCT.
    """
    import re
    from typing import Dict

    if "define " not in text:
        return text

    lines = text.splitlines()
    out = []
    i = 0
    n = len(lines)
    while i < n:
        if not lines[i].lstrip().startswith('define'):
            out.append(lines[i])
            i += 1
            continue
        func = []
        depth = lines[i].count('{') - lines[i].count('}')
        func.append(lines[i])
        i += 1
        while i < n and depth > 0:
            func.append(lines[i])
            depth += lines[i].count('{') - lines[i].count('}')
            i += 1
        varmap: Dict[str, str] = {}
        nxt = 0
        for m in re.findall(r'(%[\w.\-]+)', func[0]):
            if m.startswith('%STRUCT'):
                continue
            if m not in varmap:
                varmap[m] = f"%{nxt}"
                nxt += 1
        lhs = re.compile(r'^\s*(%[\w.\-]+)\s*=')
        for line in func[1:]:
            mo = lhs.match(line)
            if not mo:
                continue
            v = mo.group(1)
            if v.startswith('%STRUCT'):
                continue
            if v not in varmap:
                varmap[v] = f"%{nxt}"
                nxt += 1
        if varmap:
            old_names = sorted(varmap.keys(), key=len, reverse=True)
            pattern = re.compile(r'(?<![\w@%])(' + '|'.join(map(re.escape, old_names)) + r')\b')
            func = [pattern.sub(lambda m: varmap[m.group(1)], ln) for ln in func]
        out.extend(func)
    return "\n".join(out)

@register_rule('normalize_structs')
def normalize_structs(text: str) -> str:
    """
    Normalize top-level struct-like type definitions.
    Renames them to %STRUCT0, %STRUCT1, etc., and updates references.
    Only processes global scope, skips inside function bodies.
    """
    import re
    lines = text.splitlines()
    struct_defs = []  # (old_name, new_name)
    struct_idx = 0
    in_func = False
    brace_balance = 0
    def_line_re = re.compile(r'^(%[\w.\-]+)\s*=\s*.+')
    for line in lines:
        stripped = line.strip()
        brace_balance += line.count('{')
        brace_balance -= line.count('}')
        in_func = brace_balance > 0

        if not in_func:
            m = def_line_re.match(line)
            if m:
                old_name = m.group(1)
                new_name = f'%STRUCT{struct_idx}'
                struct_defs.append((old_name, new_name))
                struct_idx += 1
    if not struct_defs:
        return text
    name_mapping = dict(struct_defs)
    pattern = re.compile(r'(?<![\w%.])(' + '|'.join(re.escape(k) for k in name_mapping.keys()) + r')\b')
    def replacer(m):
        old = m.group(1)
        return name_mapping.get(old, old)
    new_text = pattern.sub(replacer, text)

    return new_text

@register_rule('domtree_analysis')
def domtree_analysis(text: str) -> str:
    """Simplify DominatorTree logs by removing extra metadata and indentation, keep [n] %x."""
    lines = text.splitlines()
    output = []
    if "DominatorTree for function:" not in text:
        return text
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("DominatorTree for function:"):
            output.append(stripped)
        elif set(stripped) <= {"=", "-"}:
            continue
        elif "DFSNumbers invalid" in stripped:
            continue
        elif stripped.startswith("Roots:"):
            output.append(stripped)
        else:
            # Correctly keep "[n] %x"
            m = re.match(r"(\[\d+\])\s*(%[^\s{]+)", stripped)
            if m:
                output.append(f"{m.group(1)} {m.group(2)}")
    return "\n".join(output)

@register_rule('loops_analysis')
def loops_analysis(text: str) -> str:
    return text

@register_rule('memoryssa_walker_analysis')
def memoryssa_walker_analysis(text: str) -> str:
    """
    Simplify and analyze MemorySSA instructions in LLVM IR logs.
    """
    if "MemorySSA (walker) for function" not in text:
        return text
    lines = text.splitlines()
    result = []
    current_func = None
    # Regular expressions for identifying specific patterns
    re_func = re.compile(r"^define.*@(\w+)\(")
    re_def = re.compile(r"^;\s*(\d+)\s*=\s*MemoryDef\([^\)]*\)->[^\s]+")
    re_use = re.compile(r"^;\s*MemoryUse\((\d+)\).*- clobbered by\s*(\d+)\s*=\s*MemoryDef")
    re_phi = re.compile(r"^;\s*(\d+)\s*=\s*MemoryPhi\([^\)]*\)")
    # Temporary storage for lines to be combined
    pending = None  # (kind, id, text)
    for raw in lines:
        line = raw.strip()
        # 1) Function header
        m = re_func.match(line)
        if m:
            current_func = m.group(1)
            result.append(f"MemorySSA for function {current_func}:")
            pending = None
            continue
        # 2) Def instruction
        m = re_def.match(line)
        if m:
            if pending:
                result.append(pending[2])
            def_id = m.group(1)
            pending = ("Def", def_id, f"[Def {def_id}]")
            continue
        # 3) Use instruction
        m = re_use.match(line)
        if m:
            if pending:
                result.append(pending[2])
            use_id, clobber = m.group(1), m.group(2)
            pending = ("Use", use_id, f"[Use {use_id}] (clobbered by Def {clobber})")
            continue
        # 4) Phi instruction (optional)
        m = re_phi.match(line)
        if m:
            if pending:
                result.append(pending[2])
            phi_id = m.group(1)
            pending = ("Phi", phi_id, f"[Phi {phi_id}]")
            continue
        # 5) If it's a store/load/call instruction, merge it with the pending one
        if pending and (line.startswith("store") or line.startswith("load") or
                        line.startswith("call") or line.startswith("%")):
            pending = (pending[0], pending[1], pending[2] + "  " + line)
            result.append(pending[2])
            pending = None
            continue

    # If there is any pending content, add it
    if pending:
        result.append(pending[2])

    return "\n".join(result) + "\n"

@register_rule('bfi_analysis')
def bfi_analysis(text: str) -> str:
    """
    Process log file content to simplify BFI analysis results.
    """
    lines = text.splitlines()
    result = []
    if "Printing analysis results of BFI for function" not in text:
        return text
    for line in lines:
        # Replace header line
        if "Printing analysis results of BFI for function" in line:
            line = re.sub(
                r"Printing analysis results of BFI for function '([^']+)'",
                r"Analysis results of BlockFrequency for function '\1'",
                line
            )
            result.append(line)
            continue
        # Extract label and float values, discard int values
        match = re.search(r"^\s*-\s*(.*?):\s*float\s*=\s*([\d.eE+-]+)", line)
        if match:
            label, value = match.groups()
            result.append(f" - {label}: float = {value}")
    return "\n".join(result) + "\n"

@register_rule('func_only')
def func_only(text: str) -> str:
    
    """Keep only function definitions, removing all non-function content."""
    lines = text.splitlines()
    output = []
    if "define " not in text:
        return text
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.strip().startswith('define'):
            func_block = []
            func_block.append(line)
            i += 1
            while i < n:
                func_block.append(lines[i])
                if lines[i].strip() == '}':
                    break
                i += 1
            output.extend(func_block)
        i += 1
    return "\n".join(output)

@register_rule('rename_blocks')
def rename_blocks(text: str) -> str:
    """Rename basic blocks inside functions to B0, B1, ... and update all references."""
    if "define " not in text:
        return text
    lines = text.splitlines()
    new_lines = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped.startswith('define'):
            new_lines.append(line)
            i += 1
            continue

        func_block = []
        depth = 0
        while i < n:
            func_block.append(lines[i])
            depth += lines[i].count('{') - lines[i].count('}')
            if depth <= 0 and lines[i].strip() == '}':
                break
            i += 1

        block_map = {}
        block_counter = 0
        for l in func_block:
            ls = l.strip()
            if ls.endswith(':') and not ls.startswith(';'):
                label = ls[:-1]
                block_map[label] = f'B{block_counter}'
                block_counter += 1
        processed_func = []
        token_re = re.compile(r'[%@][\w\.\-]+')
        for l in func_block:
            if l.strip().endswith(':') and not l.strip().startswith(';'):
                label = l.strip()[:-1]
                new_label = block_map.get(label, label)
                processed_func.append(f'{new_label}:')
            else:
                def repl(m):
                    token = m.group()
                    if token.startswith('%'):
                        token_body = token[1:]
                        if token_body in block_map:
                            return f'%{block_map[token_body]}'
                    return token
                processed_func.append(token_re.sub(repl, l))
        new_lines.extend(processed_func)
        i += 1
    return '\n'.join(new_lines)

@register_rule('extract_modulehash')
def extract_modulehash(text: str) -> str:
    """
    Extracts the Module Hash from LLVM opt output (log)
    """
    match = re.search(r"Module Hash:\s*([0-9a-fA-F]+)", text)
    if match:
        return match.group(1)
    return ""