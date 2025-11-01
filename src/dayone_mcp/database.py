"""Day One database access module."""

import json
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional


class DayOneDatabase:
    """Read-only access to Day One SQLite database."""

    # Core Data epoch: January 1, 2001 00:00:00 UTC
    CORE_DATA_EPOCH = 978307200

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection.

        Args:
            db_path: Optional custom database path. If None, uses default Day One location.
        """
        if db_path is None:
            db_path = Path.home() / "Library/Group Containers/5U8NS4GX82.dayoneapp2/Data/Documents/DayOne.sqlite"

        self.db_path = db_path

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Day One database not found at {self.db_path}. "
                "Make sure Day One is installed and has been opened at least once."
            )

    def _connect(self) -> sqlite3.Connection:
        """Create a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _core_data_to_datetime(self, timestamp: float) -> datetime:
        """Convert Core Data timestamp to Python datetime."""
        return datetime.fromtimestamp(timestamp + self.CORE_DATA_EPOCH)

    def _extract_text(self, rich_text_json: Optional[str], markdown_text: Optional[str]) -> str:
        """Extract plain text from Day One's rich text JSON or markdown.

        Args:
            rich_text_json: Rich text JSON string
            markdown_text: Markdown text fallback

        Returns:
            Extracted plain text
        """
        if not rich_text_json and not markdown_text:
            return ""

        # Try rich text JSON first
        if rich_text_json:
            try:
                data = json.loads(rich_text_json)

                # Handle common Day One formats
                if isinstance(data, dict):
                    # Direct text field
                    if 'text' in data:
                        return str(data['text']).strip()

                    # AttributedString format
                    if 'attributedString' in data and 'string' in data['attributedString']:
                        return str(data['attributedString']['string']).strip()

                    # Ops/Delta format (Quill-like)
                    if 'ops' in data:
                        return ''.join(
                            str(op['insert'])
                            for op in data['ops']
                            if isinstance(op, dict) and 'insert' in op and isinstance(op['insert'], str)
                        ).strip()

                    # Delta wrapper
                    if 'delta' in data and 'ops' in data['delta']:
                        return ''.join(
                            str(op['insert'])
                            for op in data['delta']['ops']
                            if isinstance(op, dict) and 'insert' in op and isinstance(op['insert'], str)
                        ).strip()

                    # NSString format
                    if 'NSString' in data:
                        return str(data['NSString']).strip()

                elif isinstance(data, str):
                    return data.strip()

            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        # Fallback to markdown
        return markdown_text.strip() if markdown_text else ""

    def _get_entry_tags(self, conn: sqlite3.Connection, entry_uuid: str) -> list[str]:
        """Get tags for a specific entry."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.ZNAME
            FROM ZTAG t
            JOIN Z_16TAGS zt ON t.Z_PK = zt.Z_60TAGS1
            JOIN ZENTRY e ON zt.Z_16ENTRIES = e.Z_PK
            WHERE e.ZUUID = ?
        """, (entry_uuid,))
        return [row[0] for row in cursor.fetchall()]

    def _get_bulk_tags(self, conn: sqlite3.Connection, entry_uuids: list[str]) -> dict[str, list[str]]:
        """Get tags for multiple entries in a single query.

        Args:
            conn: Database connection
            entry_uuids: List of entry UUIDs

        Returns:
            Dictionary mapping entry UUID to list of tag names
        """
        if not entry_uuids:
            return {}

        cursor = conn.cursor()
        placeholders = ','.join('?' * len(entry_uuids))
        cursor.execute(f"""
            SELECT e.ZUUID, t.ZNAME
            FROM ZTAG t
            JOIN Z_16TAGS zt ON t.Z_PK = zt.Z_60TAGS1
            JOIN ZENTRY e ON zt.Z_16ENTRIES = e.Z_PK
            WHERE e.ZUUID IN ({placeholders})
            ORDER BY e.ZUUID, t.ZNAME
        """, entry_uuids)

        # Group tags by entry UUID
        tags_by_entry = {}
        for row in cursor.fetchall():
            uuid = row[0]
            tag = row[1]
            if uuid not in tags_by_entry:
                tags_by_entry[uuid] = []
            tags_by_entry[uuid].append(tag)

        return tags_by_entry

    def _get_bulk_attachments(self, conn: sqlite3.Connection, entry_uuids: list[str]) -> dict[str, list[dict[str, Any]]]:
        """Get attachments for multiple entries in a single query.

        Args:
            conn: Database connection
            entry_uuids: List of entry UUIDs

        Returns:
            Dictionary mapping entry UUID to list of attachment dictionaries
        """
        if not entry_uuids:
            return {}

        base_path = Path.home() / "Library/Group Containers/5U8NS4GX82.dayoneapp2/Data/Documents"

        cursor = conn.cursor()
        placeholders = ','.join('?' * len(entry_uuids))
        cursor.execute(f"""
            SELECT
                e.ZUUID,
                a.ZIDENTIFIER,
                a.ZTYPE,
                a.ZMD5,
                a.ZWIDTH,
                a.ZHEIGHT,
                a.ZDURATION,
                a.ZCAPTION,
                a.ZISRECORDING
            FROM ZATTACHMENT a
            JOIN ZENTRY e ON a.ZENTRY = e.Z_PK
            WHERE e.ZUUID IN ({placeholders})
            ORDER BY e.ZUUID, a.ZORDERINENTRY
        """, entry_uuids)

        # Group attachments by entry UUID
        attachments_by_entry = {}
        for row in cursor.fetchall():
            entry_uuid = row[0]
            attachment_type = row[2]
            md5 = row[3]

            # Determine media directory based on type
            if attachment_type in ('jpeg', 'png', 'heic', 'gif'):
                media_dir = 'DayOnePhotos'
            elif attachment_type in ('mp4', 'mov', 'avi'):
                media_dir = 'DayOneVideos'
            elif row[8]:  # ZISRECORDING
                media_dir = 'DayOneAudios'
            elif attachment_type == 'pdf':
                media_dir = 'DayOnePDFAttachments'
            else:
                media_dir = 'DayOnePhotos'  # Default fallback

            # Build file path
            file_path = base_path / media_dir / f"{md5}.{attachment_type}" if md5 else None

            attachment = {
                'identifier': row[1],
                'type': attachment_type,
                'file_path': str(file_path) if file_path and file_path.exists() else None,
                'width': row[4],
                'height': row[5],
                'duration': row[6],
                'caption': row[7]
            }

            if entry_uuid not in attachments_by_entry:
                attachments_by_entry[entry_uuid] = []
            attachments_by_entry[entry_uuid].append(attachment)

        return attachments_by_entry

    def read_recent_entries(self, limit: int = 10, journal: Optional[str] = None) -> list[dict[str, Any]]:
        """Read recent journal entries.

        Args:
            limit: Maximum number of entries (1-50)
            journal: Optional journal name filter

        Returns:
            List of entry dictionaries
        """
        limit = max(1, min(50, limit))  # Clamp between 1-50

        conn = self._connect()
        cursor = conn.cursor()

        query = """
            SELECT
                e.ZUUID as uuid,
                e.ZRICHTEXTJSON as rich_text,
                e.ZMARKDOWNTEXT as markdown_text,
                e.ZCREATIONDATE as creation_date,
                e.ZMODIFIEDDATE as modified_date,
                e.ZSTARRED as starred,
                e.ZTIMEZONE as timezone,
                j.ZNAME as journal_name,
                e.ZLOCATION as has_location,
                e.ZWEATHER as has_weather
            FROM ZENTRY e
            LEFT JOIN ZJOURNAL j ON e.ZJOURNAL = j.Z_PK
        """

        params = []
        if journal:
            query += " WHERE j.ZNAME = ?"
            params.append(journal)

        query += " ORDER BY e.ZCREATIONDATE DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        entries = []
        for row in cursor.fetchall():
            entry = {
                'uuid': row['uuid'],
                'text': self._extract_text(row['rich_text'], row['markdown_text']),
                'creation_date': self._core_data_to_datetime(row['creation_date']),
                'modified_date': self._core_data_to_datetime(row['modified_date']) if row['modified_date'] else None,
                'starred': bool(row['starred']),
                'timezone': row['timezone'],
                'journal_name': row['journal_name'] or 'Default',
                'has_location': bool(row['has_location']),
                'has_weather': bool(row['has_weather']),
                'tags': self._get_entry_tags(conn, row['uuid'])
            }
            entries.append(entry)

        conn.close()
        return entries

    def search_entries(
        self,
        text: Optional[str] = None,
        tags: Optional[list[str]] = None,
        starred: Optional[bool] = None,
        has_photos: Optional[bool] = None,
        has_videos: Optional[bool] = None,
        has_audio: Optional[bool] = None,
        has_location: Optional[bool] = None,
        creation_device: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        journal: Optional[str] = None,
        limit: int = 20,
        include_tags: bool = False,
        include_attachments: bool = False
    ) -> list[dict[str, Any]]:
        """Search entries with flexible filters.

        Args:
            text: Text to search for in entry content
            tags: List of tags (entry must have ALL tags)
            starred: Filter by starred status
            has_photos: Filter entries with photo attachments
            has_videos: Filter entries with video attachments
            has_audio: Filter entries with audio recordings
            has_location: Filter entries with location data
            creation_device: Filter by device type (e.g., "iPhone", "MacBook Pro")
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            journal: Journal name filter
            limit: Maximum results (1-50)
            include_tags: Fetch tag data for entries (default False for performance)
            include_attachments: Fetch attachment/media data for entries (default False for performance)

        Returns:
            List of matching entries
        """
        limit = max(1, min(50, limit))

        conn = self._connect()
        cursor = conn.cursor()

        # Base query
        query = """
            SELECT DISTINCT
                e.ZUUID as uuid,
                e.ZRICHTEXTJSON as rich_text,
                e.ZMARKDOWNTEXT as markdown_text,
                e.ZCREATIONDATE as creation_date,
                e.ZMODIFIEDDATE as modified_date,
                e.ZSTARRED as starred,
                e.ZTIMEZONE as timezone,
                j.ZNAME as journal_name
            FROM ZENTRY e
            LEFT JOIN ZJOURNAL j ON e.ZJOURNAL = j.Z_PK
        """

        conditions = []
        params = []

        # Text search
        if text:
            conditions.append("(e.ZRICHTEXTJSON LIKE ? OR e.ZMARKDOWNTEXT LIKE ?)")
            params.extend([f'%{text}%', f'%{text}%'])

        # Starred filter
        if starred is not None:
            conditions.append("e.ZSTARRED = ?")
            params.append(1 if starred else 0)

        # Location filter
        if has_location is not None:
            if has_location:
                conditions.append("e.ZLOCATION IS NOT NULL")
            else:
                conditions.append("e.ZLOCATION IS NULL")

        # Device filter
        if creation_device:
            conditions.append("e.ZCREATIONDEVICETYPE = ?")
            params.append(creation_device)

        # Date range filters
        if date_from:
            try:
                date_obj = datetime.strptime(date_from, '%Y-%m-%d')
                timestamp = date_obj.timestamp() - self.CORE_DATA_EPOCH
                conditions.append("e.ZCREATIONDATE >= ?")
                params.append(timestamp)
            except ValueError:
                pass  # Skip invalid dates

        if date_to:
            try:
                date_obj = datetime.strptime(date_to, '%Y-%m-%d')
                # Add one day to include the entire end date
                end_of_day = date_obj.timestamp() + 86400 - self.CORE_DATA_EPOCH
                conditions.append("e.ZCREATIONDATE < ?")
                params.append(end_of_day)
            except ValueError:
                pass  # Skip invalid dates

        # Journal filter
        if journal:
            conditions.append("j.ZNAME = ?")
            params.append(journal)

        # Media filters (using subqueries)
        if has_photos:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM ZATTACHMENT a
                    WHERE a.ZENTRY = e.Z_PK
                    AND a.ZTYPE IN ('jpeg', 'png')
                )
            """)

        if has_videos:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM ZATTACHMENT a
                    WHERE a.ZENTRY = e.Z_PK
                    AND a.ZTYPE IN ('mp4', 'mov')
                )
            """)

        if has_audio:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM ZATTACHMENT a
                    WHERE a.ZENTRY = e.Z_PK
                    AND a.ZISRECORDING = 1
                )
            """)

        # Tag filters (entry must have ALL specified tags)
        if tags:
            for tag in tags:
                conditions.append("""
                    EXISTS (
                        SELECT 1 FROM ZTAG t
                        JOIN Z_16TAGS zt ON t.Z_PK = zt.Z_60TAGS1
                        WHERE zt.Z_16ENTRIES = e.Z_PK
                        AND t.ZNAME = ?
                    )
                """)
                params.append(tag)

        # Build WHERE clause
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Order and limit
        query += " ORDER BY e.ZCREATIONDATE DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Bulk fetch optional data if requested
        entry_uuids = [row['uuid'] for row in rows]
        tags_by_entry = self._get_bulk_tags(conn, entry_uuids) if include_tags else {}
        attachments_by_entry = self._get_bulk_attachments(conn, entry_uuids) if include_attachments else {}

        # Build results
        entries = []
        for row in rows:
            uuid = row['uuid']
            entry = {
                'uuid': uuid,
                'text': self._extract_text(row['rich_text'], row['markdown_text']),
                'creation_date': self._core_data_to_datetime(row['creation_date']),
                'modified_date': self._core_data_to_datetime(row['modified_date']) if row['modified_date'] else None,
                'starred': bool(row['starred']),
                'timezone': row['timezone'],
                'journal_name': row['journal_name'] or 'Default'
            }

            # Add optional fields only if requested
            if include_tags:
                entry['tags'] = tags_by_entry.get(uuid, [])
            if include_attachments:
                entry['attachments'] = attachments_by_entry.get(uuid, [])

            entries.append(entry)

        conn.close()
        return entries

    def list_journals(self) -> list[dict[str, Any]]:
        """List all journals with statistics.

        Returns:
            List of journal dictionaries
        """
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                j.ZNAME as name,
                j.ZUUIDFORAUXILIARYSYNC as uuid,
                COUNT(e.Z_PK) as entry_count,
                MAX(e.ZCREATIONDATE) as last_entry_date
            FROM ZJOURNAL j
            LEFT JOIN ZENTRY e ON e.ZJOURNAL = j.Z_PK
            GROUP BY j.Z_PK, j.ZNAME, j.ZUUIDFORAUXILIARYSYNC
            ORDER BY j.ZNAME
        """)

        journals = []
        for row in cursor.fetchall():
            journal = {
                'name': row['name'],
                'uuid': row['uuid'],
                'entry_count': row['entry_count'],
                'last_entry_date': self._core_data_to_datetime(row['last_entry_date']) if row['last_entry_date'] else None
            }
            journals.append(journal)

        conn.close()
        return journals

    def get_entry_by_uuid(self, uuid: str, include_attachments: bool = True) -> Optional[dict[str, Any]]:
        """Get a single entry by UUID.

        Args:
            uuid: Entry UUID
            include_attachments: Fetch attachment data

        Returns:
            Entry dictionary or None if not found
        """
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                e.ZUUID as uuid,
                e.ZRICHTEXTJSON as rich_text,
                e.ZMARKDOWNTEXT as markdown_text,
                e.ZCREATIONDATE as creation_date,
                e.ZMODIFIEDDATE as modified_date,
                e.ZSTARRED as starred,
                e.ZTIMEZONE as timezone,
                j.ZNAME as journal_name
            FROM ZENTRY e
            LEFT JOIN ZJOURNAL j ON e.ZJOURNAL = j.Z_PK
            WHERE e.ZUUID = ?
        """, (uuid,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        entry = {
            'uuid': row['uuid'],
            'text': self._extract_text(row['rich_text'], row['markdown_text']),
            'creation_date': self._core_data_to_datetime(row['creation_date']),
            'modified_date': self._core_data_to_datetime(row['modified_date']) if row['modified_date'] else None,
            'starred': bool(row['starred']),
            'timezone': row['timezone'],
            'journal_name': row['journal_name'] or 'Default'
        }

        if include_attachments:
            attachments_by_entry = self._get_bulk_attachments(conn, [uuid])
            entry['attachments'] = attachments_by_entry.get(uuid, [])

        conn.close()
        return entry

    def get_entry_count(self, journal: Optional[str] = None) -> int:
        """Get total entry count.

        Args:
            journal: Optional journal name filter

        Returns:
            Number of entries
        """
        conn = self._connect()
        cursor = conn.cursor()

        if journal:
            cursor.execute("""
                SELECT COUNT(*)
                FROM ZENTRY e
                JOIN ZJOURNAL j ON e.ZJOURNAL = j.Z_PK
                WHERE j.ZNAME = ?
            """, (journal,))
        else:
            cursor.execute("SELECT COUNT(*) FROM ZENTRY")

        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_entries_by_date(self, target_date: str, years_back: int = 5) -> list[dict[str, Any]]:
        """Get 'On This Day' entries from previous years.

        Args:
            target_date: Date in MM-DD or YYYY-MM-DD format (e.g., '06-14')
            years_back: How many years to search back

        Returns:
            List of entries from this date in previous years
        """
        # Parse date
        if len(target_date) == 5 and '-' in target_date:  # MM-DD
            month, day = map(int, target_date.split('-'))
        elif len(target_date) == 10:  # YYYY-MM-DD
            _, month, day = map(int, target_date.split('-'))
        else:
            raise ValueError(f"Invalid date format: {target_date}. Use MM-DD or YYYY-MM-DD")

        conn = self._connect()
        cursor = conn.cursor()

        current_year = datetime.now().year
        date_conditions = []
        params = []

        # Build query for each year
        for year in range(current_year - years_back, current_year + 1):
            start_date = datetime(year, month, day)
            end_date = start_date + timedelta(days=1)

            start_ts = start_date.timestamp() - self.CORE_DATA_EPOCH
            end_ts = end_date.timestamp() - self.CORE_DATA_EPOCH

            date_conditions.append("(e.ZCREATIONDATE >= ? AND e.ZCREATIONDATE < ?)")
            params.extend([start_ts, end_ts])

        query = f"""
            SELECT
                e.ZUUID as uuid,
                e.ZRICHTEXTJSON as rich_text,
                e.ZMARKDOWNTEXT as markdown_text,
                e.ZCREATIONDATE as creation_date,
                e.ZMODIFIEDDATE as modified_date,
                e.ZSTARRED as starred,
                e.ZTIMEZONE as timezone,
                j.ZNAME as journal_name,
                e.ZLOCATION as has_location,
                e.ZWEATHER as has_weather
            FROM ZENTRY e
            LEFT JOIN ZJOURNAL j ON e.ZJOURNAL = j.Z_PK
            WHERE ({' OR '.join(date_conditions)})
            ORDER BY e.ZCREATIONDATE DESC
        """

        cursor.execute(query, params)

        entries = []
        for row in cursor.fetchall():
            creation_date = self._core_data_to_datetime(row['creation_date'])
            entry = {
                'uuid': row['uuid'],
                'text': self._extract_text(row['rich_text'], row['markdown_text']),
                'creation_date': creation_date,
                'modified_date': self._core_data_to_datetime(row['modified_date']) if row['modified_date'] else None,
                'starred': bool(row['starred']),
                'timezone': row['timezone'],
                'journal_name': row['journal_name'] or 'Default',
                'has_location': bool(row['has_location']),
                'has_weather': bool(row['has_weather']),
                'year': creation_date.year,
                'years_ago': current_year - creation_date.year,
                'tags': self._get_entry_tags(conn, row['uuid'])
            }
            entries.append(entry)

        conn.close()
        return entries
