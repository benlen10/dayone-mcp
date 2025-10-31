#!/usr/bin/env python3
"""Simple test script to verify database access."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dayone_mcp.database import DayOneDatabase


def main():
    print("Testing Day One MCP Database Access\n" + "=" * 50)

    try:
        # Initialize database
        print("\n1. Initializing database connection...")
        db = DayOneDatabase()
        print(f"   ✓ Connected to: {db.db_path}")

        # Test entry count
        print("\n2. Getting entry count...")
        count = db.get_entry_count()
        print(f"   ✓ Total entries: {count}")

        # Test list journals
        print("\n3. Listing journals...")
        journals = db.list_journals()
        for journal in journals:
            print(f"   ✓ {journal['name']}: {journal['entry_count']} entries")

        # Test read recent entries
        print("\n4. Reading recent entries (5)...")
        entries = db.read_recent_entries(limit=5)
        print(f"   ✓ Retrieved {len(entries)} entries")
        for i, entry in enumerate(entries, 1):
            date_str = entry['creation_date'].strftime('%Y-%m-%d')
            text_preview = entry['text'][:50] + "..." if len(entry['text']) > 50 else entry['text']
            print(f"   {i}. {date_str} - {text_preview}")

        # Test search
        print("\n5. Testing search (searching for 'the')...")
        search_results = db.search_entries("the", limit=3)
        print(f"   ✓ Found {len(search_results)} matching entries")

        print("\n" + "=" * 50)
        print("✓ All tests passed successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
