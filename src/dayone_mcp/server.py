"""MCP server for read-only Day One journal access."""

import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

from .database import DayOneDatabase


# Tool argument schemas
class ReadRecentEntriesArgs(BaseModel):
    limit: int = Field(default=10, ge=1, le=50, description="Number of entries to return (1-50)")
    journal: str = Field(default="", description="Optional journal name to filter by")


class SearchEntriesArgs(BaseModel):
    search_text: str = Field(description="Text to search for in entries")
    limit: int = Field(default=20, ge=1, le=50, description="Number of results (1-50)")
    journal: str = Field(default="", description="Optional journal name to filter by")


class ListJournalsArgs(BaseModel):
    pass


class GetEntryCountArgs(BaseModel):
    journal: str = Field(default="", description="Optional journal name to count entries for")


class GetEntriesByDateArgs(BaseModel):
    target_date: str = Field(description="Date in MM-DD or YYYY-MM-DD format (e.g., '06-14')")
    years_back: int = Field(default=5, ge=1, le=20, description="Years to search back (1-20)")


# Initialize server and database
app = Server("dayone-mcp")
db = DayOneDatabase()


def format_entry(entry: dict[str, Any]) -> str:
    """Format an entry for display."""
    lines = [
        f"📝 {entry['creation_date'].strftime('%Y-%m-%d %H:%M')}",
        f"Journal: {entry['journal_name']}"
    ]

    if entry['starred']:
        lines[0] += " ⭐"

    if entry.get('tags'):
        lines.append(f"Tags: {', '.join(f'#{tag}' for tag in entry['tags'])}")

    if entry['has_location']:
        lines.append("📍 Has location")

    if entry.get('years_ago') is not None and entry['years_ago'] > 0:
        lines.append(f"({entry['years_ago']} year{'s' if entry['years_ago'] > 1 else ''} ago)")

    # Add text preview (first 200 chars)
    text = entry['text']
    if text:
        preview = text[:200] + "..." if len(text) > 200 else text
        lines.append(f"\n{preview}")

    return '\n'.join(lines)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="read_recent_entries",
            description="Read recent journal entries with full text and metadata",
            inputSchema=ReadRecentEntriesArgs.model_json_schema()
        ),
        Tool(
            name="search_entries",
            description="Search journal entries by text content",
            inputSchema=SearchEntriesArgs.model_json_schema()
        ),
        Tool(
            name="list_journals",
            description="List all journals with entry counts and statistics",
            inputSchema=ListJournalsArgs.model_json_schema()
        ),
        Tool(
            name="get_entry_count",
            description="Get total number of entries, optionally filtered by journal",
            inputSchema=GetEntryCountArgs.model_json_schema()
        ),
        Tool(
            name="get_entries_by_date",
            description="Get 'On This Day' entries from previous years for a specific date",
            inputSchema=GetEntriesByDateArgs.model_json_schema()
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "read_recent_entries":
            args = ReadRecentEntriesArgs(**arguments)
            journal = args.journal if args.journal else None
            entries = db.read_recent_entries(limit=args.limit, journal=journal)

            if not entries:
                return [TextContent(type="text", text="No entries found.")]

            header = f"Found {len(entries)} recent entries"
            if journal:
                header += f" in journal '{journal}'"

            result = [header + ":\n"]
            result.extend(format_entry(entry) + "\n" for entry in entries)

            return [TextContent(type="text", text='\n'.join(result))]

        elif name == "search_entries":
            args = SearchEntriesArgs(**arguments)
            journal = args.journal if args.journal else None
            entries = db.search_entries(
                search_text=args.search_text,
                limit=args.limit,
                journal=journal
            )

            if not entries:
                return [TextContent(type="text", text=f"No entries found matching '{args.search_text}'.")]

            header = f"Found {len(entries)} entries matching '{args.search_text}'"
            if journal:
                header += f" in journal '{journal}'"

            result = [header + ":\n"]
            result.extend(format_entry(entry) + "\n" for entry in entries)

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

        elif name == "get_entry_count":
            args = GetEntryCountArgs(**arguments)
            journal = args.journal if args.journal else None
            count = db.get_entry_count(journal=journal)

            if journal:
                text = f"Journal '{journal}' has {count} entries."
            else:
                text = f"Total entries: {count}"

            return [TextContent(type="text", text=text)]

        elif name == "get_entries_by_date":
            args = GetEntriesByDateArgs(**arguments)
            entries = db.get_entries_by_date(
                target_date=args.target_date,
                years_back=args.years_back
            )

            if not entries:
                return [TextContent(
                    type="text",
                    text=f"No entries found for {args.target_date} in the past {args.years_back} years."
                )]

            # Group by year
            by_year = {}
            for entry in entries:
                year = entry['year']
                if year not in by_year:
                    by_year[year] = []
                by_year[year].append(entry)

            result = [f"📅 On This Day ({args.target_date}) - Found {len(entries)} entries:\n"]

            for year in sorted(by_year.keys(), reverse=True):
                year_entries = by_year[year]
                years_ago = year_entries[0]['years_ago']
                if years_ago == 0:
                    result.append(f"\n🗓️  {year} (This year):")
                elif years_ago == 1:
                    result.append(f"\n🗓️  {year} (1 year ago):")
                else:
                    result.append(f"\n🗓️  {year} ({years_ago} years ago):")

                for entry in year_entries:
                    result.append(format_entry(entry) + "\n")

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
