def calculate_average(numbers: list[int]) -> float:
    """Calculate average of numbers.

    Bug: Doesn't handle empty list.
    """
    return sum(numbers) / len(numbers)


def find_max(numbers: list[int]) -> int:
    """Find maximum number.

    Bug: Returns None for empty list instead of raising error.
    """
    if not numbers:
        return None
    return max(numbers)
