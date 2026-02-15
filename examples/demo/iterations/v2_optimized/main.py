"""Optimized iteration: sorting with Python's built-in Timsort."""

import random


def optimized_sort(data: list[int]) -> list[int]:
    """Sort a list using Python's built-in sorted (Timsort)."""
    return sorted(data)


def main() -> None:
    random.seed(42)
    data = [random.randint(0, 10000) for _ in range(2000)]
    result = optimized_sort(data)
    print(f"Sorted {len(data)} elements")
    print(f"First 5: {result[:5]}")
    print(f"Last 5: {result[-5:]}")


if __name__ == "__main__":
    main()
