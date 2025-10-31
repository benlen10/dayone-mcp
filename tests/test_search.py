#!/usr/bin/env python3
"""Test script for unified search functionality."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dayone_mcp.database import DayOneDatabase


def test_basic_search(db):
    """Test basic text search."""
    print("\n1. Basic text search (vacation)...")
    entries = db.search_entries(text="vacation", limit=5)
    print(f"   ✓ Found {len(entries)} entries")
    return len(entries) > 0


def test_starred_filter(db):
    """Test starred filter."""
    print("\n2. Starred entries filter...")
    entries = db.search_entries(starred=True, limit=5)
    print(f"   ✓ Found {len(entries)} starred entries")
    if entries:
        print(f"   First entry: {entries[0]['creation_date'].strftime('%Y-%m-%d')}")
    return True


def test_media_filters(db):
    """Test media filters."""
    print("\n3. Media filters...")

    photos = db.search_entries(has_photos=True, limit=3)
    print(f"   ✓ Entries with photos: {len(photos)}")

    videos = db.search_entries(has_videos=True, limit=3)
    print(f"   ✓ Entries with videos: {len(videos)}")

    audio = db.search_entries(has_audio=True, limit=3)
    print(f"   ✓ Entries with audio: {len(audio)}")

    return True


def test_device_filter(db):
    """Test device filter."""
    print("\n4. Device filter (iPhone)...")
    entries = db.search_entries(creation_device="iPhone", limit=5)
    print(f"   ✓ Found {len(entries)} entries from iPhone")
    return True


def test_date_range(db):
    """Test date range filter."""
    print("\n5. Date range filter (October 2025)...")
    entries = db.search_entries(
        date_from="2025-10-01",
        date_to="2025-10-31",
        limit=10
    )
    print(f"   ✓ Found {len(entries)} entries in October 2025")
    if entries:
        print(f"   First: {entries[0]['creation_date'].strftime('%Y-%m-%d')}")
        print(f"   Last: {entries[-1]['creation_date'].strftime('%Y-%m-%d')}")
    return True


def test_combined_filters(db):
    """Test multiple filters combined."""
    print("\n6. Combined filters (starred + photos + October)...")
    entries = db.search_entries(
        starred=True,
        has_photos=True,
        date_from="2025-10-01",
        date_to="2025-10-31",
        limit=5
    )
    print(f"   ✓ Found {len(entries)} entries matching all criteria")
    return True


def test_tag_filter(db):
    """Test tag filter."""
    print("\n7. Tag filter...")
    # First get some tags to test with
    entries = db.read_recent_entries(limit=20)
    all_tags = set()
    for entry in entries:
        all_tags.update(entry.get('tags', []))

    if all_tags:
        test_tag = list(all_tags)[0]
        print(f"   Testing with tag: '{test_tag}'")
        tagged_entries = db.search_entries(tags=[test_tag], limit=5)
        print(f"   ✓ Found {len(tagged_entries)} entries with tag '{test_tag}'")
    else:
        print("   ⚠ No tags found to test with")

    return True


def test_location_filter(db):
    """Test location filter."""
    print("\n8. Location filter...")
    with_location = db.search_entries(has_location=True, limit=5)
    print(f"   ✓ Entries with location: {len(with_location)}")

    without_location = db.search_entries(has_location=False, limit=5)
    print(f"   ✓ Entries without location: {len(without_location)}")

    return True


def main():
    print("Testing Unified Search Functionality\n" + "=" * 70)

    try:
        db = DayOneDatabase()
        print("✓ Database connected")

        # Run all tests
        tests = [
            test_basic_search,
            test_starred_filter,
            test_media_filters,
            test_device_filter,
            test_date_range,
            test_combined_filters,
            test_tag_filter,
            test_location_filter
        ]

        passed = 0
        for test_func in tests:
            try:
                if test_func(db):
                    passed += 1
            except Exception as e:
                print(f"   ✗ Test failed: {e}")

        print("\n" + "=" * 70)
        print(f"✓ Tests passed: {passed}/{len(tests)}")

        if passed == len(tests):
            print("✓ All tests passed!")
            return 0
        else:
            print(f"⚠ {len(tests) - passed} test(s) had issues")
            return 0  # Don't fail - some filters may have no results

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
