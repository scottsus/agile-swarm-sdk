import pytest
from buggy import calculate_average, find_max


def test_calculate_average():
    """Test average calculation."""
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0


def test_calculate_average_empty():
    """Test average with empty list (currently fails)."""
    with pytest.raises(ValueError):
        calculate_average([])


def test_find_max():
    """Test finding maximum."""
    assert find_max([1, 5, 3, 2]) == 5


def test_find_max_empty():
    """Test finding max in empty list (currently fails)."""
    with pytest.raises(ValueError):
        find_max([])
