import unittest

from utils.dashboard_layout import normalize_width, pack_rows


class DashboardLayoutTests(unittest.TestCase):
    def test_normalize_width_bounds(self):
        self.assertEqual(normalize_width(0, 3), 1)
        self.assertEqual(normalize_width(5, 2), 2)
        self.assertEqual(normalize_width(2, 3), 2)

    def test_pack_rows_respects_columns_and_order(self):
        layout = [
            {"name": "A", "width": 2},
            {"name": "B", "width": 1},
            {"name": "C", "width": 2},
            {"name": "D", "width": 1},
        ]
        rows = pack_rows(layout, columns=3)

        # Extract widths row by row
        row_widths = [[entry["width"] for _, entry in row] for row in rows]
        self.assertEqual(row_widths, [[2, 1], [2, 1]])

        # Ensure order is preserved
        flattened_order = [layout[idx]["name"] for row in rows for idx, _ in row]
        self.assertEqual(flattened_order, ["A", "B", "C", "D"])

    def test_pack_rows_clamps_widths(self):
        layout = [
            {"name": "Wide", "width": 10},
            {"name": "Narrow", "width": 1},
        ]
        rows = pack_rows(layout, columns=2)
        row_widths = [[entry["width"] for _, entry in row] for row in rows]
        self.assertEqual(row_widths, [[2], [1]])


if __name__ == "__main__":
    unittest.main()
