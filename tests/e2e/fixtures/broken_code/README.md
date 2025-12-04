# Broken Code

Code with known bugs for testing bug-fix scenarios.

## Known Bugs

1. `calculate_average()` - Crashes on empty list (should raise ValueError)
2. `find_max()` - Returns None on empty list (should raise ValueError)

## Run Tests

```bash
pytest -v  # Will show 2 failures
```

## Common Test Scenarios

1. Fix the empty list bugs
2. Add input validation
3. Improve error messages
