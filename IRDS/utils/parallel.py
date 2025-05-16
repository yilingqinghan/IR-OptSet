# utils/parallel.py

from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from typing import Callable, Iterable, List, Any, Optional

def parallel_map(
    func: Callable[[Any], Any],
    tasks: Iterable[Any],
    desc: Optional[str] = None,
    num_workers: Optional[int] = None,
) -> List[Any]:
    """
    Apply `func` to each item in `tasks`, in parallel.

    Args:
        func: Function to apply to each item.
        tasks: Iterable of tasks.
        desc: Optional description for progress bar.
        num_workers: Number of parallel workers (default: cpu_count()).

    Returns:
        List of results in order.
    """
    tasks = list(tasks)
    n = len(tasks)
    num_workers = num_workers or min(32, cpu_count())

    results = []
    with Pool(processes=num_workers) as pool:
        for result in tqdm(pool.imap(func, tasks), total=n, desc=desc, unit="task"):
            results.append(result)

    return results