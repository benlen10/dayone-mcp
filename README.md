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
- **"List my Day One journals"** - See all journals with stats
- **"How many entries do I have?"** - Get total entry count
- **"What did I write on June 14th in past years?"** - "On This Day" feature

## Available Tools

### `read_recent_entries`
Read recent journal entries with full text and metadata.

**Parameters:**
- `limit` (optional): Number of entries (1-50, default: 10)
- `journal` (optional): Filter by journal name

### `search_entries`
Search journal entries by text content.

**Parameters:**
- `search_text`: Text to search for
- `limit` (optional): Number of results (1-50, default: 20)
- `journal` (optional): Filter by journal name

### `list_journals`
List all journals with entry counts and statistics.

### `get_entry_count`
Get total number of entries.

**Parameters:**
- `journal` (optional): Filter by journal name

### `get_entries_by_date`
Get "On This Day" entries from previous years.

**Parameters:**
- `target_date`: Date in MM-DD or YYYY-MM-DD format (e.g., "06-14")
- `years_back` (optional): Years to search back (1-20, default: 5)

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

# Format code
uv run ruff format .

# Type check
uv run mypy .
```

## Project Structure

```
dayone-mcp/
├── src/
│   └── dayone_mcp/
│       ├── __init__.py       # Package metadata
│       ├── database.py       # Database access layer
│       └── server.py         # MCP server implementation
├── pyproject.toml            # Project configuration
└── README.md                 # This file
```

## License

MIT

## Acknowledgments

Built with the [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic.
