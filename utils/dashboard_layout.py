"""Pure layout helpers for the dashboard grid (test-friendly)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def normalize_width(width: int, max_columns: int) -> int:
    """Clamp widget width between 1 and max_columns."""
    return max(1, min(int(width or 1), max_columns))


def pack_rows(layout: List[Dict[str, Any]], columns: int) -> List[List[Tuple[int, Dict[str, Any]]]]:
    """
    Pack widgets into rows based on widths, returning indices to preserve removal targets.

    Each row is a list of (index, entry_with_width) tuples.
    """
    rows: List[List[Tuple[int, Dict[str, Any]]]] = []
    current_row: List[Tuple[int, Dict[str, Any]]] = []
    used = 0

    for idx, entry in enumerate(layout):
        width = normalize_width(entry.get("width", 1), columns)
        if used + width > columns and current_row:
            rows.append(current_row)
            current_row = []
            used = 0
        current_row.append((idx, {**entry, "width": width}))
        used += width

    if current_row:
        rows.append(current_row)
    return rows
