from typing import Iterable, Optional
import tqdm

def progress_bar(iterable: Iterable, desc: Optional[str] = None, unit: str = "", leave: bool = True):
    return tqdm.tqdm(iterable, desc=desc, unit=unit, leave=leave)
