# Day One MCP Server

A read-only Model Context Protocol (MCP) server for Day One journal on macOS. Access and search your Day One entries directly from Claude Desktop.

## Features

- 📖 **Read recent entries** with full text and metadata
- 🔍 **Search entries** by text content
- 📚 **List journals** with statistics
- 📊 **Count entries** across all or specific journals
- 📅 **"On This Day"** - View entries from previous years

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

- **"Show me my recent journal entries"** - View latest entries
- **"Search my journal for entries about vacation"** - Full-text search
- **"Find starred entries tagged work from last month"** - Advanced filtered search
- **"Show me all entries with photos from my iPhone"** - Media and device filter
- **"Find vacation entries with location data"** - Combined filters
- **"List my Day One journals"** - See all journals with stats
- **"How many entries do I have?"** - Get total entry count
- **"What did I write on June 14th in past years?"** - "On This Day" feature

## Available Tools

### `read_recent_entries`
Read recent journal entries with metadata and **text preview** (200 character limit).

**Parameters:**
- `limit` (optional): Number of entries (1-50, default: 10)
- `journal` (optional): Filter by journal name

**Note:** Returns preview only to avoid overwhelming the display.

### `search_entries`
Search journal entries with flexible filters, returns **text preview** (200 character limit).

**Parameters:**
- `text` (optional): Text to search for in entry content
- `tags` (optional): List of tags (entry must have ALL tags)
- `starred` (optional): Filter by starred status (true/false)
- `has_photos` (optional): Filter entries with photo attachments
- `has_videos` (optional): Filter entries with video attachments
- `has_audio` (optional): Filter entries with audio recordings
- `has_location` (optional): Filter entries with location data
- `creation_device` (optional): Device type (e.g., "iPhone", "MacBook Pro", "iPad")
- `date_from` (optional): Start date (YYYY-MM-DD format)
- `date_to` (optional): End date (YYYY-MM-DD format)
- `journal` (optional): Filter by journal name
- `limit` (optional): Number of results (1-50, default: 20)

**All filters use AND logic** - results must match all specified criteria.

**Examples:**
- Find starred entries with photos: `starred=true, has_photos=true`
- Find work entries from iPhone last month: `tags=["work"], creation_device="iPhone", date_from="2025-01-01", date_to="2025-01-31"`
- Find vacation entries with location: `text="vacation", has_location=true`

### `list_journals`
List all journals with entry counts and statistics.

### `get_entry_count`
Get total number of entries.

**Parameters:**
- `journal` (optional): Filter by journal name

### `get_entries_by_date`
Get "On This Day" entries from previous years with **FULL entry text** (no preview limit).

**Parameters:**
- `target_date`: Date in MM-DD or YYYY-MM-DD format (e.g., "06-14")
- `years_back` (optional): Years to search back (1-20, default: 5)

**Note:** Returns complete entry text for historical reflection and analysis.

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

## Project Structure

```
dayone-mcp/
├── src/
│   └── dayone_mcp/
│       ├── __init__.py       # Package metadata
│       ├── database.py       # Database access layer
│       └── server.py         # MCP server implementation
├── tests/
│   ├── test_database.py      # Database connection tests
│   ├── test_date_entries.py  # Date query tests
│   └── test_full_text.py     # Text extraction tests
├── pyproject.toml            # Project configuration
├── README.md                 # This file
├── CLAUDE.md                 # Claude Code guidance
└── BEEKEEPER_GUIDE.md        # Beekeeper Studio SQL guide
```

## License

MIT

## Acknowledgments

Built with the [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic.
