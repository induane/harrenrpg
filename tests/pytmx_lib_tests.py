# Test Module
from unittest import TestCase

# Project
from pytmx import lib


class TestLib(TestCase):
    def test_convert_to_bool(self):
        """Check casting property values to booleans."""
        data = (
            ("0", False),
            ("1", True),
            ("True", True),
            ("false", False),
            (0, False),
            (1, True),
            ("99", True),
            (2, True),
            (-1, True),
            ("no", False),
        )
        for value, expected in data:
            result = lib.convert_to_bool(value)
            self.assertEqual(result, expected, msg=f"Expected '{value}' to be '{expected}'")
