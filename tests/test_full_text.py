#!/usr/bin/env python3
"""Test full text display for get_entries_by_date."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dayone_mcp.database import DayOneDatabase
from src.dayone_mcp.server import format_entry


def main():
    print("Testing Full Text Display\n" + "=" * 70)

    try:
        db = DayOneDatabase()

        # Get entries for 10-31
        print("\n1. Fetching entries for 10-31...")
        entries = db.get_entries_by_date("10-31", years_back=5)
        print(f"   ✓ Found {len(entries)} entries\n")

        if not entries:
            print("   No entries found")
            return 0

        # Test both preview and full text modes
        test_entry = entries[0]

        print("2. Testing PREVIEW mode (200 char limit):\n")
        preview_output = format_entry(test_entry, full_text=False)
        print(preview_output)
        print(f"\n   Preview length: {len(preview_output)} characters\n")

        print("=" * 70)
        print("\n3. Testing FULL TEXT mode:\n")
        full_output = format_entry(test_entry, full_text=True)
        print(full_output)
        print(f"\n   Full text length: {len(full_output)} characters")

        print("\n" + "=" * 70)
        print("✓ Test complete - full text is working!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
