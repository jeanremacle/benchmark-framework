"""Baseline iteration: simple sorting with bubble sort."""

import random


def bubble_sort(data: list[int]) -> list[int]:
    """Sort a list using bubble sort (intentionally slow)."""
    arr = data.copy()
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def main() -> None:
    random.seed(42)
    data = [random.randint(0, 10000) for _ in range(2000)]
    result = bubble_sort(data)
    print(f"Sorted {len(data)} elements")
    print(f"First 5: {result[:5]}")
    print(f"Last 5: {result[-5:]}")


if __name__ == "__main__":
    main()
