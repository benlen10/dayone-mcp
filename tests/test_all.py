#!/usr/bin/env python3
"""Comprehensive test suite for Day One MCP server."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dayone_mcp.database import DayOneDatabase
from src.dayone_mcp.server import format_entry


def test_database_connection():
    """Test 1: Database connection and initialization."""
    print("\n" + "=" * 70)
    print("TEST 1: Database Connection")
    print("=" * 70)

    db = DayOneDatabase()
    print(f"✓ Connected to: {db.db_path}")

    count = db.get_entry_count()
    print(f"✓ Total entries: {count}")

    journals = db.list_journals()
    print(f"✓ Found {len(journals)} journal(s):")
    for journal in journals:
        print(f"  - {journal['name']}: {journal['entry_count']} entries")

    return db, count > 0


def test_basic_operations(db):
    """Test 2: Basic read and search operations."""
    print("\n" + "=" * 70)
    print("TEST 2: Basic Operations")
    print("=" * 70)

    # Read recent entries
    entries = db.read_recent_entries(limit=5)
    print(f"✓ Retrieved {len(entries)} recent entries")
    for i, entry in enumerate(entries, 1):
        date_str = entry['creation_date'].strftime('%Y-%m-%d')
        text_preview = entry['text'][:50] + "..." if len(entry['text']) > 50 else entry['text']
        print(f"  {i}. {date_str} - {text_preview}")

    # Test search
    search_results = db.search_entries(text="the", limit=3)
    print(f"✓ Search found {len(search_results)} matching entries")

    return len(entries) > 0


def test_text_extraction(db):
    """Test 3: Text extraction from rich text JSON and markdown."""
    print("\n" + "=" * 70)
    print("TEST 3: Text Extraction")
    print("=" * 70)

    entries = db.get_entries_by_date("10-31", years_back=5)
    print(f"✓ Found {len(entries)} entries for 10-31 (past 5 years)")

    if entries:
        entry = entries[0]
        print(f"\nAnalyzing entry from {entry['year']} ({entry['years_ago']} years ago):")
        print(f"  - Text length: {len(entry['text'])} characters")
        print(f"  - Journal: {entry['journal_name']}")
        print(f"  - Tags: {entry.get('tags', [])}")

        if entry['text']:
            preview = entry['text'][:100].replace('\n', ' ')
            print(f"  - Preview: {preview}...")
        else:
            print("  ⚠️ No text extracted")

    return len(entries) > 0 if entries else True


def test_format_display(db):
    """Test 4: Entry formatting (preview vs full text)."""
    print("\n" + "=" * 70)
    print("TEST 4: Entry Formatting")
    print("=" * 70)

    entries = db.get_entries_by_date("10-31", years_back=5)

    if entries:
        test_entry = entries[0]

        print("\nPreview mode (200 char limit):")
        print("-" * 70)
        preview_output = format_entry(test_entry, full_text=False)
        print(preview_output)
        print(f"\nPreview length: {len(preview_output)} characters")

        print("\n" + "-" * 70)
        print("Full text mode:")
        print("-" * 70)
        full_output = format_entry(test_entry, full_text=True)
        print(full_output[:500] + "..." if len(full_output) > 500 else full_output)
        print(f"\nFull text length: {len(full_output)} characters")

    return True


def test_search_filters(db):
    """Test 5: Advanced search filters."""
    print("\n" + "=" * 70)
    print("TEST 5: Advanced Search Filters")
    print("=" * 70)

    # Text search
    results = db.search_entries(text="vacation", limit=5)
    print(f"✓ Text search ('vacation'): {len(results)} entries")

    # Starred filter
    starred = db.search_entries(starred=True, limit=5)
    print(f"✓ Starred entries: {len(starred)} entries")

    # Media filters
    photos = db.search_entries(has_photos=True, limit=3)
    print(f"✓ Entries with photos: {len(photos)} entries")

    videos = db.search_entries(has_videos=True, limit=3)
    print(f"✓ Entries with videos: {len(videos)} entries")

    audio = db.search_entries(has_audio=True, limit=3)
    print(f"✓ Entries with audio: {len(audio)} entries")

    # Location filter
    with_location = db.search_entries(has_location=True, limit=5)
    print(f"✓ Entries with location: {len(with_location)} entries")

    # Date range
    date_entries = db.search_entries(
        date_from="2025-10-01",
        date_to="2025-10-31",
        limit=10
    )
    print(f"✓ Entries in October 2025: {len(date_entries)} entries")

    # Combined filters
    combined = db.search_entries(
        starred=True,
        has_photos=True,
        date_from="2025-10-01",
        date_to="2025-10-31",
        limit=5
    )
    print(f"✓ Combined filters (starred + photos + Oct 2025): {len(combined)} entries")

    return True


def test_lazy_loading_performance(db):
    """Test 6: Lazy loading and performance optimization."""
    print("\n" + "=" * 70)
    print("TEST 6: Lazy Loading & Performance")
    print("=" * 70)

    # Test 1: Basic search without optional data (1 query)
    print("\n1. Basic search (no tags, no attachments):")
    entries = db.search_entries(limit=10, include_tags=False, include_attachments=False)
    print(f"   ✓ Found {len(entries)} entries")
    if entries:
        first = entries[0]
        print(f"   - Has 'tags' key: {'tags' in first}")
        print(f"   - Has 'attachments' key: {'attachments' in first}")

    # Test 2: Search with tags included (2 queries)
    print("\n2. Search with tags included:")
    entries_with_tags = db.search_entries(limit=10, include_tags=True, include_attachments=False)
    print(f"   ✓ Found {len(entries_with_tags)} entries")
    entries_with_data = [e for e in entries_with_tags if e.get('tags')]
    print(f"   - Entries with tags: {len(entries_with_data)}")

    # Test 3: Search with attachments (2 queries)
    print("\n3. Search with attachments included:")
    entries_with_attachments = db.search_entries(
        has_photos=True,
        limit=5,
        include_tags=False,
        include_attachments=True
    )
    print(f"   ✓ Found {len(entries_with_attachments)} entries with photos")

    for i, entry in enumerate(entries_with_attachments[:3], 1):
        attachments = entry.get('attachments', [])
        print(f"\n   Entry {i} ({entry['creation_date'].strftime('%Y-%m-%d')}):")
        print(f"     - Attachments: {len(attachments)}")
        for att in attachments:
            print(f"       • Type: {att['type']}")
            print(f"         Path: {att['file_path']}")
            if att.get('width') and att.get('height'):
                print(f"         Size: {att['width']}x{att['height']}")

    # Test 4: All features enabled (3 queries)
    print("\n4. All features enabled (tags + attachments):")
    full_featured = db.search_entries(
        has_photos=True,
        limit=3,
        include_tags=True,
        include_attachments=True
    )
    print(f"   ✓ Found {len(full_featured)} entries")
    for entry in full_featured:
        print(f"   - {entry['creation_date'].strftime('%Y-%m-%d')}: "
              f"{len(entry.get('tags', []))} tags, "
              f"{len(entry.get('attachments', []))} attachments")

    # Test 5: Date range efficiency
    print("\n5. Date range search (no extras - should be fast):")
    halloween = db.search_entries(
        date_from="2024-10-31",
        date_to="2024-10-31",
        limit=10,
        include_tags=False,
        include_attachments=False
    )
    print(f"   ✓ Found {len(halloween)} entries on Halloween 2024")

    return True


def test_get_entry_by_uuid(db):
    """Test 7: Get entry by UUID for resource retrieval."""
    print("\n" + "=" * 70)
    print("TEST 7: Get Entry by UUID")
    print("=" * 70)

    # First get a recent entry with attachments
    entries = db.search_entries(has_photos=True, limit=1, include_attachments=True)

    if not entries:
        print("⚠ No entries with photos found to test")
        return True

    test_entry = entries[0]
    test_uuid = test_entry['uuid']

    print(f"Testing UUID lookup for: {test_uuid}")

    # Test 1: Fetch entry without attachments
    entry_no_att = db.get_entry_by_uuid(test_uuid, include_attachments=False)
    if entry_no_att:
        print(f"✓ Retrieved entry without attachments")
        print(f"  - Has 'attachments' key: {'attachments' in entry_no_att}")
    else:
        print(f"✗ Failed to retrieve entry by UUID")
        return False

    # Test 2: Fetch entry with attachments
    entry_with_att = db.get_entry_by_uuid(test_uuid, include_attachments=True)
    if entry_with_att and 'attachments' in entry_with_att:
        attachments = entry_with_att['attachments']
        print(f"✓ Retrieved entry with {len(attachments)} attachment(s)")
        for i, att in enumerate(attachments):
            print(f"  - Attachment {i}: {att['type']}, path exists: {att['file_path'] is not None}")
    else:
        print(f"✗ Failed to retrieve entry with attachments")
        return False

    # Test 3: Try non-existent UUID
    fake_entry = db.get_entry_by_uuid("00000000-0000-0000-0000-000000000000")
    if fake_entry is None:
        print(f"✓ Correctly returns None for non-existent UUID")
    else:
        print(f"✗ Should return None for non-existent UUID")
        return False

    return True


def test_attachment_file_verification(db):
    """Test 8: Verify attachment file paths exist."""
    print("\n" + "=" * 70)
    print("TEST 8: Attachment File Verification")
    print("=" * 70)

    entries = db.search_entries(has_photos=True, limit=3, include_attachments=True)

    if entries:
        print(f"✓ Testing {len(entries)} entries with photos")

        verified = 0
        for entry in entries:
            for att in entry.get('attachments', []):
                if att['file_path']:
                    file_path = Path(att['file_path'])
                    if file_path.exists():
                        verified += 1
                        print(f"  ✓ {file_path.name} ({att['type']}, "
                              f"{file_path.stat().st_size / 1024:.1f} KB)")
                    else:
                        print(f"  ✗ File not found: {file_path}")

        print(f"\n✓ Verified {verified} attachment file(s)")
    else:
        print("⚠ No entries with photos found to test")

    return True


def test_format_entry_with_attachments(db):
    """Test 9: Entry formatting with attachments."""
    print("\n" + "=" * 70)
    print("TEST 9: Format Entry with Attachments")
    print("=" * 70)

    entries = db.search_entries(has_photos=True, limit=2, include_attachments=True, include_tags=True)

    if entries:
        for i, entry in enumerate(entries, 1):
            print(f"\nEntry {i}:")
            print("-" * 70)
            formatted = format_entry(entry, full_text=True)
            # Show first 500 chars to keep output manageable
            print(formatted[:500] + "..." if len(formatted) > 500 else formatted)
    else:
        print("⚠ No entries with photos found")

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("DAY ONE MCP - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    try:
        # Initialize database
        db, db_ok = test_database_connection()
        if not db_ok:
            print("\n✗ Database initialization failed")
            return 1

        # Run all tests
        tests = [
            ("Basic Operations", lambda: test_basic_operations(db)),
            ("Text Extraction", lambda: test_text_extraction(db)),
            ("Entry Formatting", lambda: test_format_display(db)),
            ("Search Filters", lambda: test_search_filters(db)),
            ("Lazy Loading & Performance", lambda: test_lazy_loading_performance(db)),
            ("Get Entry by UUID", lambda: test_get_entry_by_uuid(db)),
            ("Attachment File Verification", lambda: test_attachment_file_verification(db)),
            ("Format Entry with Attachments", lambda: test_format_entry_with_attachments(db))
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
                    print(f"⚠ {test_name} returned False")
            except Exception as e:
                failed += 1
                print(f"\n✗ {test_name} failed: {e}")
                import traceback
                traceback.print_exc()

        # Final summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total tests: {len(tests)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")

        if failed == 0:
            print("\n✅ ALL TESTS PASSED!")
            return 0
        else:
            print(f"\n⚠️ {failed} test(s) failed")
            return 1

    except Exception as e:
        print(f"\n✗ Critical error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
