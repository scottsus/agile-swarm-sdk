from calculator import add, subtract


def test_add():
    """Test addition."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_subtract():
    """Test subtraction."""
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5
