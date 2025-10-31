#!/usr/bin/env python3
"""Test script to diagnose get_entries_by_date text extraction."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dayone_mcp.database import DayOneDatabase


def main():
    print("Testing get_entries_by_date Text Extraction\n" + "=" * 70)

    try:
        db = DayOneDatabase()

        # Test with 10-31
        print("\n1. Fetching entries for 10-31 (past 5 years)...")
        entries = db.get_entries_by_date("10-31", years_back=5)
        print(f"   ✓ Found {len(entries)} entries")

        if not entries:
            print("   No entries found for 10-31")
            return 0

        # Analyze each entry
        print("\n2. Analyzing each entry:\n")
        for i, entry in enumerate(entries, 1):
            print(f"   Entry {i}:")
            print(f"   - UUID: {entry['uuid']}")
            print(f"   - Date: {entry['creation_date']}")
            print(f"   - Year: {entry['year']} ({entry['years_ago']} years ago)")
            print(f"   - Journal: {entry['journal_name']}")
            print(f"   - Text Length: {len(entry['text'])} characters")

            if entry['text']:
                preview = entry['text'][:200].replace('\n', ' ')
                print(f"   - Preview: {preview}...")
            else:
                print(f"   - ⚠️ NO TEXT EXTRACTED!")

            print()

        # Now let's check the raw database for one of these entries
        if entries:
            print("\n3. Checking raw database for first entry...\n")
            test_uuid = entries[0]['uuid']

            conn = db._connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    ZUUID,
                    ZRICHTEXTJSON,
                    ZMARKDOWNTEXT,
                    LENGTH(ZRICHTEXTJSON) as json_length,
                    LENGTH(ZMARKDOWNTEXT) as markdown_length
                FROM ZENTRY
                WHERE ZUUID = ?
            """, (test_uuid,))

            row = cursor.fetchone()
            if row:
                print(f"   UUID: {row['ZUUID']}")
                print(f"   Rich Text JSON Length: {row['json_length']} bytes")
                print(f"   Markdown Text Length: {row['markdown_length']} bytes")
                print()

                if row['ZRICHTEXTJSON']:
                    print(f"   Rich Text JSON (first 500 chars):")
                    print(f"   {row['ZRICHTEXTJSON'][:500]}")
                    print()

                if row['ZMARKDOWNTEXT']:
                    print(f"   Markdown Text (first 500 chars):")
                    print(f"   {row['ZMARKDOWNTEXT'][:500]}")
                    print()

                # Test extraction directly
                extracted = db._extract_text(row['ZRICHTEXTJSON'], row['ZMARKDOWNTEXT'])
                print(f"   Direct Extraction Result: {len(extracted)} characters")
                if extracted:
                    print(f"   Extracted Preview: {extracted[:200]}")
                else:
                    print(f"   ⚠️ EXTRACTION FAILED!")

            conn.close()

        print("\n" + "=" * 70)
        print("✓ Analysis complete")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
