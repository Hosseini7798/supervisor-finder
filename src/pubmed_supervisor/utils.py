"""
Utility functions for supervisor-finder.
"""

import pandas as pd


def first_valid(series):
    """
    Get the first non-null value from a pandas Series.

    Args:
        series: pandas Series to search.

    Returns:
        The first non-null, non-empty value, or None if all values are null/empty.

    Examples:
        >>> import pandas as pd
        >>> s = pd.Series([None, "", "value", "other"])
        >>> first_valid(s)
        'value'
    """
    for val in series:
        if pd.notna(val) and val:
            return val
    return None
