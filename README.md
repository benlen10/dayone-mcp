# Day One MCP Server

A read-only Model Context Protocol (MCP) server for Day One journal on macOS. Access and search your Day One entries directly from Claude Desktop.

## Features

- **Unified search** - Find entries with flexible filters (text, tags, starred, media, location, device, dates)
- **List journals** - View all journals with statistics
- **Browse recent** - Simply search with no filters
- **"On This Day"** - Use date filters to view historical entries

## Prerequisites

- **macOS** with Day One app installed
- **Python 3.11+**
- **uv** package manager - [Install from astral.sh](https://docs.astral.sh/uv/getting-started/installation/)

## Installation

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and setup

```bash
git clone <repository-url>
cd dayone-mcp
uv sync
```

### 3. Configure Claude Desktop

Add to your Claude Desktop config at `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dayone": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/dayone-mcp",
        "run",
        "python",
        "-m",
        "dayone_mcp.server"
      ]
    }
  }
}
```

**Important:** Replace `/ABSOLUTE/PATH/TO/dayone-mcp` with your actual installation path.

### 4. Restart Claude Desktop

After updating the configuration, restart Claude Desktop to load the MCP server.

## Usage

Once configured, you can interact with Day One through natural language:

### Example Queries

- **"Show me my recent journal entries"** - Browse recent (no filters)
- **"Search my journal for entries about vacation"** - Text search
- **"Find starred entries tagged work from last month"** - Multi-filter search
- **"Show me all entries with photos from my iPhone"** - Media + device filter
- **"What did I write on October 31st in past years?"** - Date filter for "On This Day"
- **"List my Day One journals"** - View all journals with stats

## Available Tools

Just **2 simple tools**:

### 1. `search_entries`
**One powerful tool** for all entry operations - search, browse, and filter.

Returns **FULL entry text** and all metadata.

**All parameters are optional** - use none for browsing, use filters to narrow results:

- `text` - Text to search for in entry content
- `tags` - List of tags (entry must have ALL specified tags)
- `starred` - Filter by starred status (true/false)
- `has_photos` - Filter entries with photo attachments
- `has_videos` - Filter entries with video attachments
- `has_audio` - Filter entries with audio recordings
- `has_location` - Filter entries with location data
- `creation_device` - Device type ("iPhone", "MacBook Pro", "iPad", "Apple Watch")
- `date_from` - Start date (YYYY-MM-DD)
- `date_to` - End date (YYYY-MM-DD)
- `journal` - Journal name filter
- `limit` - Number of results (1-50, default: 20)

**All filters use AND logic** - results must match all criteria.

**Examples:**
```
Browse recent: search_entries(limit=10)
Text search: search_entries(text="vacation")
Starred + photos: search_entries(starred=true, has_photos=true)
"On This Day": search_entries(date_from="2020-10-31", date_to="2025-10-31")
Multi-filter: search_entries(tags=["work"], creation_device="iPhone", date_from="2025-01-01")
```

### 2. `list_journals`
List all Day One journals with statistics.

**Returns:**
- Journal names
- Entry counts per journal
- Last entry date for each journal

## Database Location

The server automatically connects to Day One's database at:
```
~/Library/Group Containers/5U8NS4GX82.dayoneapp2/Data/Documents/DayOne.sqlite
```

Make sure Day One has been opened at least once to create the database.

## Troubleshooting

### Database not found
- Ensure Day One is installed and has been opened at least once
- The database is created when you first launch Day One

### Permission issues
- Day One database is read-only from this server
- No write operations are performed

### Claude Desktop connection issues
- Verify the absolute path in `claude_desktop_config.json`
- Check Claude Desktop logs for errors
- Restart Claude Desktop after configuration changes

## Development

```bash
# Install dependencies
uv sync

# Run server directly (for testing)
uv run python -m dayone_mcp.server

# Run tests
uv run python tests/test_database.py

# Test date-based queries
uv run python tests/test_date_entries.py

# Test full text display
uv run python tests/test_full_text.py
```


## License

MIT

## Acknowledgments

Built with the [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic.
