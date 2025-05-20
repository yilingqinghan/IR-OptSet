import os
import random
from typing import List, Union


class RandomGenerator:
    """
    A utility class for generating random data types, including integers,
    floats, and file selections from a specified directory.
    """

    def __init__(self, seed: Union[int, None] = None):
        """
        Initialize the RandomGenerator with an optional seed for reproducibility.

        :param seed: Optional seed value for random generator.
        """
        self._random = random.Random(seed)

    def random_int(self, min_value: int, max_value: int) -> int:
        """
        Generate a random integer between min_value and max_value (inclusive).

        :param min_value: The minimum integer value.
        :param max_value: The maximum integer value.
        :return: A randomly selected integer.
        """
        return self._random.randint(min_value, max_value)

    def random_float(self, min_value: float, max_value: float) -> float:
        """
        Generate a random float between min_value and max_value.

        :param min_value: The minimum float value.
        :param max_value: The maximum float value.
        :return: A randomly selected float.
        """
        return self._random.uniform(min_value, max_value)

    def random_files(self, directory: str, count: int) -> List[str]:
        """
        Randomly select a specified number of files from a directory.

        :param directory: The path to the directory containing files.
        :param count: The number of files to randomly select.
        :return: A list of selected file paths.
        :raises ValueError: If the directory doesn't contain enough files.
        :raises FileNotFoundError: If the directory does not exist.
        """
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory '{directory}' does not exist.")

        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

        if len(files) < count:
            raise ValueError(f"Requested {count} files, but only {len(files)} available.")

        return self._random.sample([os.path.join(directory, f) for f in files], count)

# Example usage (to be placed in test script or main section, not in module directly)
# rg = RandomGenerator(seed=42)
# print(rg.random_int(1, 10))
# print(rg.random_float(1.5, 5.5))
# print(rg.random_files("/path/to/folder", 3))
