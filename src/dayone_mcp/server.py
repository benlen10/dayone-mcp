"""MCP server for read-only Day One journal access."""

import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

from .database import DayOneDatabase


# Tool argument schemas
class SearchEntriesArgs(BaseModel):
    text: str = Field(default="", description="Text to search for in entry content")
    tags: list[str] = Field(default=[], description="Tags to filter by (entry must have ALL tags)")
    starred: bool | None = Field(default=None, description="Filter by starred status (true/false/null)")
    has_photos: bool | None = Field(default=None, description="Filter entries with photos")
    has_videos: bool | None = Field(default=None, description="Filter entries with videos")
    has_audio: bool | None = Field(default=None, description="Filter entries with audio recordings")
    has_location: bool | None = Field(default=None, description="Filter entries with location data")
    creation_device: str = Field(default="", description="Device type (e.g., 'iPhone', 'MacBook Pro')")
    date_from: str = Field(default="", description="Start date YYYY-MM-DD")
    date_to: str = Field(default="", description="End date YYYY-MM-DD")
    journal: str = Field(default="", description="Journal name to filter by")
    limit: int = Field(default=20, ge=1, le=50, description="Number of results (1-50)")
    include_tags: bool = Field(default=False, description="Include tag data in results (set to true only if user asks for tags)")
    include_attachments: bool = Field(default=False, description="Include attachment/media file paths in results (set to true only if user asks for photos, videos, audio, or media)")


class ListJournalsArgs(BaseModel):
    pass


# Initialize server and database
app = Server("dayone-mcp")
db = DayOneDatabase()


def format_entry(entry: dict[str, Any], full_text: bool = False) -> str:
    """Format an entry for display.

    Args:
        entry: Entry dictionary with metadata and text
        full_text: If True, show full entry text. If False, limit to 200 chars preview.
    """
    lines = [
        f"📝 {entry['creation_date'].strftime('%Y-%m-%d %H:%M')}",
        f"Journal: {entry['journal_name']}"
    ]

    if entry['starred']:
        lines[0] += " ⭐"

    # Tags (only if included in query)
    if entry.get('tags'):
        lines.append(f"Tags: {', '.join(f'#{tag}' for tag in entry['tags'])}")

    # Attachments (only if included in query)
    if entry.get('attachments'):
        attachments = entry['attachments']

        # Count by type
        photos = [a for a in attachments if a['type'] in ('jpeg', 'png', 'heic', 'gif')]
        videos = [a for a in attachments if a['type'] in ('mp4', 'mov', 'avi')]
        audios = [a for a in attachments if a.get('duration') and a['type'] not in ('mp4', 'mov', 'avi')]
        pdfs = [a for a in attachments if a['type'] == 'pdf']

        media_parts = []
        if photos:
            media_parts.append(f"📷×{len(photos)}")
        if videos:
            media_parts.append(f"🎥×{len(videos)}")
        if audios:
            media_parts.append(f"🎵×{len(audios)}")
        if pdfs:
            media_parts.append(f"📄×{len(pdfs)}")

        if media_parts:
            lines.append(f"Media: {' '.join(media_parts)}")

        # Add file paths for each attachment
        for att in attachments:
            if att['file_path']:
                caption = f" - {att['caption']}" if att.get('caption') else ""
                lines.append(f"  • {att['file_path']}{caption}")

    # Location indicator (always available from main query)
    if entry.get('has_location'):
        lines.append("📍 Has location")

    if entry.get('years_ago') is not None and entry['years_ago'] > 0:
        lines.append(f"({entry['years_ago']} year{'s' if entry['years_ago'] > 1 else ''} ago)")

    # Add text (full or preview)
    text = entry['text']
    if text:
        if full_text:
            lines.append(f"\n{text}")
        else:
            preview = text[:200] + "..." if len(text) > 200 else text
            lines.append(f"\n{preview}")

    return '\n'.join(lines)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="search_entries",
            description="Search/browse Day One entries with flexible filters: text, tags, starred, photos/videos/audio, location, device, date range, journal. Returns FULL entry text and metadata. Use with no filters to browse recent entries.",
            inputSchema=SearchEntriesArgs.model_json_schema()
        ),
        Tool(
            name="list_journals",
            description="List all Day One journals with entry counts and statistics",
            inputSchema=ListJournalsArgs.model_json_schema()
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "search_entries":
            args = SearchEntriesArgs(**arguments)

            # Call database with all filter parameters
            entries = db.search_entries(
                text=args.text if args.text else None,
                tags=args.tags if args.tags else None,
                starred=args.starred,
                has_photos=args.has_photos,
                has_videos=args.has_videos,
                has_audio=args.has_audio,
                has_location=args.has_location,
                creation_device=args.creation_device if args.creation_device else None,
                date_from=args.date_from if args.date_from else None,
                date_to=args.date_to if args.date_to else None,
                journal=args.journal if args.journal else None,
                limit=args.limit,
                include_tags=args.include_tags,
                include_attachments=args.include_attachments
            )

            if not entries:
                return [TextContent(type="text", text="No entries found matching the specified filters.")]

            # Build descriptive header
            header = f"Found {len(entries)} entries"
            filters = []
            if args.text:
                filters.append(f"text: '{args.text}'")
            if args.tags:
                filters.append(f"tags: {', '.join(args.tags)}")
            if args.starred is not None:
                filters.append(f"starred: {args.starred}")
            if args.has_photos:
                filters.append("with photos")
            if args.has_videos:
                filters.append("with videos")
            if args.has_audio:
                filters.append("with audio")
            if args.has_location is not None:
                filters.append(f"location: {args.has_location}")
            if args.creation_device:
                filters.append(f"device: {args.creation_device}")
            if args.date_from or args.date_to:
                date_range = f"{args.date_from or '...'} to {args.date_to or '...'}"
                filters.append(f"dates: {date_range}")
            if args.journal:
                filters.append(f"journal: {args.journal}")

            if filters:
                header += f" ({', '.join(filters)})"

            result = [header + ":\n"]
            result.extend(format_entry(entry, full_text=True) + "\n" for entry in entries)

            return [TextContent(type="text", text='\n'.join(result))]

        elif name == "list_journals":
            journals = db.list_journals()

            if not journals:
                return [TextContent(type="text", text="No journals found.")]

            result = [f"Found {len(journals)} journal(s):\n"]
            for journal in journals:
                last_entry = journal['last_entry_date'].strftime('%Y-%m-%d') if journal['last_entry_date'] else 'Never'
                result.append(
                    f"📓 {journal['name']}\n"
                    f"   Entries: {journal['entry_count']}\n"
                    f"   Last entry: {last_entry}\n"
                )

            return [TextContent(type="text", text='\n'.join(result))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
